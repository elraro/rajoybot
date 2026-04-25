import logging
from typing import Any

from tortoise import Tortoise, connections, fields
from tortoise.models import Model

LOG = logging.getLogger('RajoyBot.persistence')


# --- Models ---

class Sound(Model):
    id = fields.IntField(primary_key=True, generated=False)
    filename = fields.CharField(max_length=255, unique=True, db_index=True)
    text = fields.CharField(max_length=512)
    tags = fields.CharField(max_length=512)
    disabled = fields.BooleanField(default=False)

    uses: fields.ReverseRelation["ResultHistory"]

    class Meta:
        table = "sound"


class User(Model):
    # Telegram user ids exceed 2^31; BIGINT is required.
    id = fields.BigIntField(primary_key=True, generated=False)
    is_bot = fields.BooleanField()
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255, null=True)
    username = fields.CharField(max_length=255, null=True)
    language_code = fields.CharField(max_length=16, null=True)
    first_seen = fields.DatetimeField(auto_now_add=True)

    queries: fields.ReverseRelation["QueryHistory"]
    results: fields.ReverseRelation["ResultHistory"]

    class Meta:
        table = "user"


class QueryHistory(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField('models.User', related_name='queries')
    text = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "queryhistory"


class ResultHistory(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField('models.User', related_name='results')
    sound = fields.ForeignKeyField('models.Sound', related_name='uses')
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "resulthistory"


# --- Repository ---

def _user_fields_from_any(user: Any) -> dict[str, Any]:
    """Extract user fields from either a dict or a Telegram User object."""
    if isinstance(user, dict):
        return user
    return {
        'id': user.id,
        'is_bot': user.is_bot,
        'first_name': user.first_name,
        'last_name': getattr(user, 'last_name', None),
        'username': getattr(user, 'username', None),
        'language_code': getattr(user, 'language_code', None),
    }


class SoundRepository:

    def __init__(self, provider: str, filename: str | None = None, host: str | None = None,
                 port: str | None = None, user: str | None = None, password: str | None = None,
                 database_name: str | None = None) -> None:
        self._provider = provider
        self._filename = filename
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database_name = database_name

    async def init(self) -> None:
        """Initialize the database connection. Must be called with await."""
        if self._provider == 'mysql':
            LOG.info('Starting persistence layer using MySQL on %s db: %s', self._host, self._database_name)
            db_url = f"mysql://{self._user}:{self._password}@{self._host}:{self._port}/{self._database_name}"
        elif self._provider == 'postgres':
            LOG.info('Starting persistence layer using PostgreSQL on %s db: %s', self._host, self._database_name)
            db_url = f"postgres://{self._user}:{self._password}@{self._host}:{self._port}/{self._database_name}"
        elif self._filename is not None:
            LOG.info('Starting persistence layer on file %s using SQLite.', self._filename)
            db_url = f"sqlite://{self._filename}"
        else:
            LOG.info('Starting persistence layer on memory using SQLite.')
            db_url = "sqlite://:memory:"

        # _enable_global_fallback=True is required because python-telegram-bot runs
        # post_init in one task and dispatches handlers in fresh tasks that don't
        # inherit Tortoise's contextvar. The global fallback lets handlers find the
        # connection cross-task. Without it, every handler hits "No TortoiseContext
        # is currently active".
        await Tortoise.init(
            db_url=db_url,
            modules={'models': ['persistence']},
            _enable_global_fallback=True,
        )
        await Tortoise.generate_schemas()
        if self._provider == 'mysql':
            await self._migrate_mysql_user_id_to_bigint()

    async def _migrate_mysql_user_id_to_bigint(self) -> None:
        """Idempotent migration for legacy MySQL deployments where user.id was INT.

        Telegram user ids exceed 2^31; switching the column type is a no-op when
        already BIGINT, so it's safe to run on every startup.
        """
        conn = connections.get('default')
        statements = [
            "ALTER TABLE queryhistory MODIFY COLUMN user_id BIGINT NOT NULL",
            "ALTER TABLE resulthistory MODIFY COLUMN user_id BIGINT NOT NULL",
            "ALTER TABLE `user` MODIFY COLUMN id BIGINT NOT NULL",
        ]
        for sql in statements:
            try:
                await conn.execute_query(sql)
            except Exception as e:
                LOG.warning("Schema migration step skipped (%s): %s", sql, e)

    # --- Sound operations ---

    async def get_sounds(self, include_disabled: bool = False) -> list[dict[str, Any]]:
        query = Sound.all() if include_disabled else Sound.filter(disabled=False)
        return [_sound_to_dict(s) for s in await query]

    async def get_sound(self, id: int | None = None, filename: str | None = None) -> dict[str, Any] | None:
        filters = {}
        if id is not None:
            filters['id'] = id
        if filename is not None:
            filters['filename'] = filename
        if not filters:
            return None
        db_object = await Sound.filter(**filters).first()
        return _sound_to_dict(db_object) if db_object else None

    async def add_sound(self, id: int, filename: str, text: str, tags: str) -> None:
        LOG.info('Adding sound: %s %s', id, filename)
        await Sound.create(id=id, filename=filename, text=text, tags=tags, disabled=False)

    async def enable_sound(self, filename: str) -> bool:
        """Re-enable a previously soft-deleted sound. Returns True if a row was flipped."""
        db_sound = await Sound.filter(filename=filename).first()
        if db_sound is None or not db_sound.disabled:
            return False
        LOG.info('Re-enabling sound %s', filename)
        db_sound.disabled = False
        await db_sound.save()
        return True

    async def delete_sound(self, sound: dict[str, Any]) -> None:
        LOG.info('Deleting sound %s', str(sound))
        db_sound = await Sound.filter(filename=sound['filename']).first()
        if db_sound is None:
            return
        if await db_sound.uses.all().count() > 0:
            db_sound.disabled = True
            await db_sound.save()
        else:
            await db_sound.delete()

    # --- User operations ---

    async def get_users(self) -> list[dict[str, Any]]:
        return [_user_to_dict(u) for u in await User.all()]

    async def get_user(self, id: int | None = None, username: str | None = None) -> dict[str, Any] | None:
        filters = {}
        if id is not None:
            filters['id'] = id
        if username is not None:
            filters['username'] = username
        if not filters:
            return None
        db_object = await User.filter(**filters).first()
        return _user_to_dict(db_object) if db_object else None

    async def add_or_update_user(self, user: Any) -> dict[str, Any] | None:
        user = _user_fields_from_any(user)
        db_user = await self.get_user(id=user['id'])

        if db_user is None:
            LOG.info('Adding user: %s', str(user))
            await User.create(**user)
        elif user != db_user:
            LOG.info('Updating user: %s', str(db_user))
            await User.filter(id=user['id']).update(
                is_bot=user['is_bot'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                username=user['username'],
                language_code=user['language_code'],
            )
        else:
            LOG.debug('User %s already in database.', user['id'])
            return None
        return await self.get_user(user['id'])

    # --- History operations ---

    async def _ensure_user(self, from_user: Any) -> dict[str, Any]:
        """Get or create a user, returning the user dict."""
        db_user = await self.get_user(from_user.id)
        if not db_user:
            db_user = await self.add_or_update_user(from_user)
        return db_user

    async def add_query(self, query: Any) -> None:
        LOG.info("Adding query: %s", str(query))
        db_user = await self._ensure_user(query.from_user)
        await QueryHistory.create(user_id=db_user['id'], text=query.query)

    async def add_result(self, result: Any) -> None:
        LOG.info("Adding result: %s", str(result))
        db_user = await self._ensure_user(result.from_user)
        await ResultHistory.create(user_id=db_user['id'], sound_id=int(result.result_id))

    async def get_queries(self) -> list[dict[str, Any]]:
        return [_query_to_dict(q) for q in await QueryHistory.all().prefetch_related('user')]

    async def get_results(self) -> list[dict[str, Any]]:
        return [_result_to_dict(r) for r in await ResultHistory.all().prefetch_related('user', 'sound')]

    # --- Counts (avoid loading entire tables for stats) ---

    async def count_users(self) -> int:
        return await User.all().count()

    async def count_queries(self) -> int:
        return await QueryHistory.all().count()

    async def count_results(self) -> int:
        return await ResultHistory.all().count()


# --- Mappers ---

def _sound_to_dict(db_object: Sound) -> dict[str, Any]:
    return {'id': db_object.id, 'filename': db_object.filename, 'text': db_object.text, 'tags': db_object.tags}


def _user_to_dict(db_object: User) -> dict[str, Any]:
    return {
        'id': db_object.id,
        'is_bot': db_object.is_bot,
        'first_name': db_object.first_name,
        'username': db_object.username,
        'last_name': db_object.last_name,
        'language_code': db_object.language_code,
    }


def _query_to_dict(db_object: QueryHistory) -> dict[str, Any]:
    return {
        'id': db_object.id,
        'user': _user_to_dict(db_object.user),
        'text': db_object.text,
        'timestamp': db_object.timestamp,
    }


def _result_to_dict(db_object: ResultHistory) -> dict[str, Any]:
    return {
        'id': db_object.id,
        'user': _user_to_dict(db_object.user),
        'sound': _sound_to_dict(db_object.sound),
        'timestamp': db_object.timestamp,
    }
