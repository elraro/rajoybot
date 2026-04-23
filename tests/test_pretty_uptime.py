import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pretty_uptime


class TestPrettyUptime:
    def test_python_uptime_format(self):
        result = pretty_uptime.get_pretty_python_uptime(custom_name='Bot')
        assert 'Bot Uptime:' in result

    def test_python_uptime_no_name(self):
        result = pretty_uptime.get_pretty_python_uptime()
        assert result.startswith('Uptime:')

    def test_machine_info_returns_string(self):
        result = pretty_uptime.get_pretty_machine_info()
        assert result.startswith('Running on ')
        assert len(result) > len('Running on ')

    def test_machine_uptime_returns_string(self):
        result = pretty_uptime.get_pretty_machine_uptime_string()
        assert result.startswith('Machine Uptime:')
