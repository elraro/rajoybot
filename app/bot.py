import json
import logging
import random
import string
from typing import Any

import pretty_uptime
import unidecode
from config import Config, parse_config
from dotenv import load_dotenv
from persistence import SoundRepository, tools
from telegram import InlineQueryResultVoice, Update
from telegram.ext import (
    Application,
    ChosenInlineResultHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    filters,
)

LOG = logging.getLogger('RajoyBot')

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
REMOVE_CHARS = str.maketrans('', '', string.punctuation)
TELEGRAM_INLINE_MAX_RESULTS = 48


def _make_voice_result(sound: dict[str, Any], bucket: str, title: str | None = None) -> InlineQueryResultVoice:
    return InlineQueryResultVoice(
        id=str(sound["id"]),
        voice_url=bucket + sound["filename"],
        title=title or sound["text"],
        caption=sound["text"]
    )


def search_sounds(query: str, sounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Search sounds by matching query words against tag words."""
    results = []
    query_words = query.split()
    for sound in sounds:
        tag_words = sound["tags"].split()
        if all(any(qw in tw for tw in tag_words) for qw in query_words):
            results.append(sound)
        if len(results) > TELEGRAM_INLINE_MAX_RESULTS:
            break
    return results


async def synchronize_sounds(config: Config, database: SoundRepository) -> list[dict[str, Any]]:
    db_sounds = await database.get_sounds()
    LOG.debug("Sounds in db (%d)", len(db_sounds))

    with open(config.data) as f:
        data_json = json.load(f)

    json_sounds = data_json["sounds"]
    LOG.debug("Sounds in data.json (%d)", len(json_sounds))

    # Adding new sounds to db
    for jsound in json_sounds:
        query = await database.get_sound(filename=jsound["filename"])
        if not query:
            jsound["id"] = int(''.join(random.choices(string.digits, k=8)))
            await database.add_sound(jsound["id"], jsound["filename"], jsound["text"], jsound["tags"])

    # Removing deleted sounds from db
    db_sounds = await database.get_sounds()
    remaining = []
    for db_sound in db_sounds:
        found = any(jsound["filename"] == db_sound["filename"] for jsound in json_sounds)
        if not found:
            await database.delete_sound(db_sound)
        else:
            remaining.append(db_sound)

    return remaining


def main() -> None:
    load_dotenv()

    config = parse_config()

    logging.basicConfig(level=getattr(logging, config.verbosity, logging.INFO), format=LOG_FORMAT)

    if config.logfile:
        file_handler = logging.FileHandler(config.logfile)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)

    if not config.token:
        LOG.critical('No telegram bot token provided. Use --token argument or TELEGRAM_BOT_TOKEN env var.')
        exit(1)

    if not config.admin:
        LOG.warning('No admin user specified. Use --admin argument or TELEGRAM_USER_ALIAS env var.')

    LOG.info('Starting up bot...')

    if config.mysql_host:
        LOG.info('Using MySQL as persistence layer: host %s port %s', config.mysql_host, config.mysql_port)
        database = SoundRepository('mysql', host=config.mysql_host, port=config.mysql_port, user=config.mysql_user,
                                   password=config.mysql_password, database_name=config.mysql_database)
    else:
        LOG.info('Using SQLite as persistence layer: %s', config.sqlite)
        database = SoundRepository('sqlite', filename=config.sqlite)

    sounds: list[dict[str, Any]] = []

    # --- Handler definitions ---

    async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        LOG.debug(update.message)
        await update.message.reply_text(
            "Este bot es inline. Teclea su nombre en una conversación/grupo y podras enviar un mensaje moderno."
        )
        await database.add_or_update_user(update.message.from_user)

    async def query_empty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        inline_query = update.inline_query
        LOG.debug(inline_query)
        r = []
        recently_used_sounds = await tools.get_latest_used_sounds_from_user(inline_query.from_user.id)
        for sound in recently_used_sounds:
            r.append(_make_voice_result(sound, config.bucket, title='🕚 ' + sound["text"]))
        for sound in sounds:
            if sound in recently_used_sounds:
                continue
            r.append(_make_voice_result(sound, config.bucket))
            if len(r) > TELEGRAM_INLINE_MAX_RESULTS:
                break
        await inline_query.answer(r, is_personal=True, cache_time=5)
        await save_query(inline_query)

    async def query_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        inline_query = update.inline_query
        LOG.debug(inline_query)
        try:
            text = unidecode.unidecode(inline_query.query).translate(REMOVE_CHARS).lower()
            LOG.debug("Querying: %s", text)
            r = [_make_voice_result(sound, config.bucket) for sound in search_sounds(text, sounds)]
            await inline_query.answer(r, cache_time=5)
            await save_query(inline_query)
        except Exception as e:
            LOG.error("Query aborted: %s", e)

    async def on_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chosen = update.chosen_inline_result
        LOG.debug('Chosen result: %s', str(chosen))
        try:
            await database.add_result(chosen)
        except Exception as e:
            LOG.error("Couldn't save result: %s", e)

    async def save_query(query: Any) -> None:
        try:
            await database.add_query(query)
        except Exception as e:
            LOG.error("Couldn't save query: %s", e)

    async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        LOG.debug(update.message)
        bot_uptime = pretty_uptime.get_pretty_python_uptime(custom_name='Bot')
        users = await database.get_users()
        queries = await database.get_queries()
        results = await database.get_results()
        await update.message.reply_text(
            f'🤖 {bot_uptime}\n'
            '*All time stats:*\n'
            f'👥 Users: {len(users)}\n'
            f'🔎 Queries: {len(queries)}\n'
            f'🔊 Results: {len(results)}\n',
            parse_mode='Markdown'
        )

    async def send_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        LOG.debug(update.message)
        py_uptime = pretty_uptime.get_pretty_python_uptime(custom_name='Bot')
        machine_uptime = pretty_uptime.get_pretty_machine_uptime_string()
        machine_info = pretty_uptime.get_pretty_machine_info()
        await update.message.reply_text(
            f'💻 {machine_info}\n'
            f'⌛ {machine_uptime}\n'
            f'🤖 {py_uptime}\n'
        )

    async def post_init(application: Application) -> None:
        await database.init()
        loaded = await synchronize_sounds(config, database)
        sounds.extend(loaded)
        LOG.info('Serving %i sounds.', len(sounds))

    async def post_shutdown(application: Application) -> None:
        from tortoise import Tortoise
        await Tortoise.close_connections()

    # --- Build application ---

    app = (
        Application.builder()
        .token(config.token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", send_welcome))

    if config.admin:
        admin_filter = filters.User(username=config.admin)
        app.add_handler(CommandHandler("stats", send_stats, filters=admin_filter))
        app.add_handler(CommandHandler("uptime", send_uptime, filters=admin_filter))

    app.add_handler(InlineQueryHandler(query_empty, pattern="^$"))
    app.add_handler(InlineQueryHandler(query_text))
    app.add_handler(ChosenInlineResultHandler(on_result))

    if config.webhook_host:
        LOG.info("Starting webhook on %s:%s", config.webhook_host, config.webhook_port)
        app.run_webhook(
            listen=config.webhook_listening,
            port=config.webhook_listening_port,
            webhook_url=f"https://{config.webhook_host}:{config.webhook_port}/{config.token}/",
        )
    else:
        LOG.info("Starting polling...")
        app.run_polling()


if __name__ == '__main__':
    main()
