import argparse
import os
from dataclasses import dataclass


@dataclass
class Config:
    token: str | None
    admin: str | None
    bucket: str
    sqlite: str | None
    mysql_host: str | None
    mysql_port: str
    mysql_user: str
    mysql_password: str
    mysql_database: str
    data: str
    logfile: str | None
    verbosity: str
    webhook_host: str | None
    webhook_port: int
    webhook_listening: str
    webhook_listening_port: int


def parse_config() -> Config:
    parser = argparse.ArgumentParser(description="RajoyBot - Telegram bot for Rajoy audio clips")
    parser.add_argument("-v", "--verbosity", help="Defines log verbosity",
                        choices=['CRITICAL', 'ERROR', 'WARN', 'INFO', 'DEBUG'], default='INFO')
    parser.add_argument("-b", "--bucket", help="Bucket or url where audios are stored",
                        default='https://github.com/elraro/RajoyBot/raw/master/RajoyBotSounds/')
    parser.add_argument("--sqlite", help="SQLite file path",
                        default=os.environ.get('SQLITE_FILE'))
    parser.add_argument("--mysql-host", help="mysql host",
                        default=os.environ.get('MYSQL_HOST'))
    parser.add_argument("--mysql-port", type=str, help="mysql port",
                        default=os.environ.get('MYSQL_PORT', '3306'))
    parser.add_argument("--mysql-user", type=str, help="mysql user",
                        default=os.environ.get('MYSQL_USER', 'rajoybot'))
    parser.add_argument("--mysql-password", type=str, help="mysql password",
                        default=os.environ.get('MYSQL_PASSWORD', 'rajoybot'))
    parser.add_argument("--mysql-database", type=str, help="mysql database name",
                        default=os.environ.get('MYSQL_DATABASE', 'rajoybot'))
    parser.add_argument("--token", type=str, help="Telegram API token given by @botfather.",
                        default=os.environ.get('TELEGRAM_BOT_TOKEN'))
    parser.add_argument("--admin", type=str, help="Alias of the admin user.",
                        default=os.environ.get('TELEGRAM_USER_ALIAS'))
    parser.add_argument("--data", type=str, help="Data JSON path.",
                        default=os.environ.get('DATA_JSON', 'data.json'))
    parser.add_argument("--logfile", type=str, help="Log to defined file.",
                        default=os.environ.get('LOGFILE'))
    parser.add_argument("--webhook-host", type=str, help="Sets a webhook to the specified host.",
                        default=os.environ.get('WEBHOOK_HOST'))
    parser.add_argument("--webhook-port", type=int, help="Webhook port. Default is 443.",
                        default=int(os.environ.get('WEBHOOK_PORT', '443')))
    parser.add_argument("--webhook-listening", type=str, help="Webhook local listening IP.",
                        default=os.environ.get('WEBHOOK_LISTEN', '0.0.0.0'))
    parser.add_argument("--webhook-listening-port", type=int, help="Webhook local listening port.",
                        default=int(os.environ.get('WEBHOOK_LISTEN_PORT', '8080')))

    args = parser.parse_args()

    return Config(
        token=args.token,
        admin=args.admin,
        bucket=args.bucket,
        sqlite=args.sqlite,
        mysql_host=args.mysql_host,
        mysql_port=args.mysql_port,
        mysql_user=args.mysql_user,
        mysql_password=args.mysql_password,
        mysql_database=args.mysql_database,
        data=args.data,
        logfile=args.logfile,
        verbosity=args.verbosity,
        webhook_host=args.webhook_host,
        webhook_port=args.webhook_port,
        webhook_listening=args.webhook_listening,
        webhook_listening_port=args.webhook_listening_port,
    )
