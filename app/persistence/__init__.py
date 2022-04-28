from .loggerfactory import LoggerFactory
import datetime
from pony.orm import *

LOG = LoggerFactory('RajoyBot.persistence').get_logger()
db = Database()


class Sound(db.Entity):
    id = PrimaryKey(int)
    filename = Required(str, index=True, unique=True)
    text = Required(str)
    tags = Required(str)
    uses = Set('ResultHistory')
    disabled = Required(bool)


class User(db.Entity):
    id = PrimaryKey(int)
    is_bot = Required(bool)
    first_name = Required(str)
    last_name = Optional(str)
    username = Optional(str)
    language_code = Optional(str)
    queries = Set('QueryHistory')
    results = Set('ResultHistory')
    first_seen = Required(datetime.datetime, sql_default='CURRENT_TIMESTAMP')


class QueryHistory(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    text = Optional(str)
    timestamp = Required(datetime.datetime, sql_default='CURRENT_TIMESTAMP')


class ResultHistory(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    sound = Required(Sound)
    timestamp = Required(datetime.datetime, sql_default='CURRENT_TIMESTAMP')


class Database:

    def __init__(self, provider, filename=None, host=None, port=None, user=None, password=None, database_name=None, ):
        if provider == 'mysql':
            LOG.info('Starting persistence layer using MySQL on %s db: %s', host, database_name)
            LOG.debug('MySQL data: host --> %s, user --> %s, db --> %s, password empty --> %s',
                      host, user, database_name, str(password is None))
            db.bind(provider='mysql', host=host, port=int(port), user=user, passwd=password, db=database_name)
        elif provider == 'postgres':
            LOG.info('Starting persistence layer using PostgreSQL on %s db: %s', host, database_name, create_db=True)
            LOG.debug('PostgreSQL data: host --> %s, user --> %s, db --> %s, password empty --> %s',
                      host, user, database_name, str(password is None))
            db.bind(provider='postgres', host=host, user=user, password=password, database=database_name,
                    create_db=True)
        elif filename is not None:
            LOG.info('Starting persistence layer on file %s using SQLite.', filename)
            db.bind(provider='sqlite', filename=filename, create_db=True)
        else:
            LOG.info('Starting persistence layer on memory using SQLite.')
            db.bind(provider='sqlite', filename=':memory:')
        db.generate_mapping(create_tables=True)

    @db_session
    def get_sounds(self, include_disabled=False):
        query = Sound.select(lambda s: s.disabled is include_disabled)
        sounds = [object_to_sound(db_object)
                  for db_object in query]
        LOG.debug("get_sounds: Obtained: %s", str(sounds))
        return sounds

    @db_session
    def get_sound(self, id=None, filename=None):
        if not id:
            db_object = Sound.get(filename=filename)
        elif not filename:
            db_object = Sound.get(id=id)
        else:
            db_object = Sound.get(id=id, filename=filename)

        if db_object:
            return object_to_sound(db_object)

    @db_session
    def add_sound(self, id, filename, text, tags):
        LOG.info('Adding sound: %s %s', id, filename)
        Sound(id=id, filename=filename, text=text, tags=tags, disabled=False)
        commit()

    @db_session
    def delete_sound(self, sound):
        LOG.info('Deleting sound %s', str(sound))
        sound = Sound.get(filename=sound['filename'])
        if len(sound.uses) > 0:
            sound.delete()
        else:
            sound.disabled = True

    @db_session
    def add_or_update_user(self, user):
        if not isinstance(user, dict):
            user = vars(user)
            LOG.debug('Translated type: %s', str(user))
        db_user = self.get_user(id=user['id'])
        if db_user is not None and user != db_user:
            LOG.info('Updating user: %s', str(db_user))
            updated_user = User[user['id']]
            updated_user.id = user['id']
            updated_user.is_bot = user['is_bot']
            updated_user.first_name = user['first_name']
            updated_user.last_name = (user['last_name'] if user['last_name'] is not None else '')
            updated_user.username = (user['username'] if user['username'] is not None else '')
            updated_user.language_code = (user['language_code'] if user['language_code'] is not None else '')
        elif db_user is None:
            LOG.info('Adding user: %s', str(user))
            User(id=user['id'], is_bot=user['is_bot'], first_name=user['first_name'],
                 last_name=(user['last_name'] if user['last_name'] is not None else ''),
                 username=(user['username'] if user['username'] is not None else ''),
                 language_code=(user['language_code'] if user['language_code'] is not None else ''))
        else:
            LOG.debug('User %s already in database.', user['id'])
            return
        commit()
        return self.get_user(user['id'])

    @db_session
    def get_users(self):
        query = User.select()
        users = [object_to_user(db_object) for db_object in query]
        LOG.debug("get_users: Obtained: %s", str(users))
        return users

    @db_session
    def get_user(self, id=None, username=None):
        if not id:
            db_object = User.get(username=username)
        elif not username:
            db_object = User.get(id=id)
        else:
            db_object = User.get(id=id, username=username)

        if db_object:
            return object_to_user(db_object)

    @db_session
    def add_query(self, query):
        LOG.info("Adding query: %s", str(query))
        from_user = query.from_user
        db_user = self.get_user(from_user.id)
        if not db_user:
            db_user = self.add_or_update_user(from_user)
        QueryHistory(user=User[db_user['id']], text=query.query)

    @db_session
    def get_queries(self):
        query = QueryHistory.select()
        queries = [object_to_query(db_object) for db_object in query]
        LOG.debug("get_queries: Obtained: %s", str(queries))
        return queries

    @db_session
    def add_result(self, result):
        LOG.info("Adding result: %s", str(result))
        from_user = result.from_user
        db_user = self.get_user(from_user.id)
        if not db_user:
            db_user = self.add_or_update_user(from_user)
        ResultHistory(user=User[db_user['id']], sound=Sound[result.result_id])

    @db_session
    def get_results(self):
        query = ResultHistory.select()
        results = [object_to_result(db_object) for db_object in query]
        LOG.debug("get_results: Obtained: %s", str(results))
        return results


# MAPPERS


def object_to_sound(db_object):
    return {'id': db_object.id, 'filename': db_object.filename, 'text': db_object.text, 'tags': db_object.tags}


def object_to_user(db_object):
    return {'id': db_object.id, 'is_bot': db_object.is_bot, 'first_name': db_object.first_name,
            'username': (db_object.username if db_object.username != '' else None),
            'last_name': (db_object.last_name if db_object.last_name != '' else None),
            'language_code': (db_object.language_code if db_object.language_code != '' else None)}


def object_to_query(db_object):
    return {'id': db_object.id, 'user': object_to_user(db_object.user), 'text': db_object.text,
            'timestamp': db_object.timestamp}


def object_to_result(db_object):
    return {'id': db_object.id, 'user': object_to_user(db_object.user), 'sound': object_to_sound(db_object.sound),
            'timestamp': db_object.timestamp}
