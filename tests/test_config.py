import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from config import parse_config


class TestConfig:
    def test_defaults(self, monkeypatch):
        """Config should have sensible defaults when no env vars are set."""
        monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
        monkeypatch.delenv('TELEGRAM_USER_ALIAS', raising=False)
        monkeypatch.delenv('SQLITE_FILE', raising=False)
        monkeypatch.delenv('MYSQL_HOST', raising=False)
        monkeypatch.setattr('sys.argv', ['bot.py'])
        config = parse_config()
        assert config.token is None
        assert config.admin is None
        assert config.mysql_port == '3306'
        assert config.mysql_database == 'rajoybot'
        assert config.data == 'data.json'
        assert config.webhook_port == 443
        assert config.webhook_listening_port == 8080

    def test_env_vars(self, monkeypatch):
        """Environment variables should be picked up as defaults."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token-123')
        monkeypatch.setenv('TELEGRAM_USER_ALIAS', 'testadmin')
        monkeypatch.setenv('SQLITE_FILE', '/tmp/test.sqlite')
        monkeypatch.setattr('sys.argv', ['bot.py'])
        config = parse_config()
        assert config.token == 'test-token-123'
        assert config.admin == 'testadmin'
        assert config.sqlite == '/tmp/test.sqlite'

    def test_cli_args_override_env(self, monkeypatch):
        """CLI arguments should override environment variables."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'env-token')
        monkeypatch.setattr('sys.argv', ['bot.py', '--token', 'cli-token'])
        config = parse_config()
        assert config.token == 'cli-token'
