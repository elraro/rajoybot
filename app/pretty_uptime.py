import platform
import time
from datetime import timedelta

_start_time = time.time()


def _get_machine_uptime_seconds() -> float | None:
    """Get machine uptime in seconds by reading /proc/uptime (Linux)."""
    try:
        with open("/proc/uptime") as f:
            return float(f.readline().split()[0])
    except (OSError, ValueError):
        return None


def get_pretty_machine_uptime_string() -> str:
    uptime_seconds = _get_machine_uptime_seconds()
    if uptime_seconds is None:
        return "Machine Uptime: unavailable"
    machine_uptime = str(timedelta(seconds=int(uptime_seconds)))
    return "Machine Uptime: " + machine_uptime


def get_pretty_machine_info() -> str:
    uname = platform.uname()
    return "Running on " + uname[0] + " " + uname[2] + " " + uname[4]


def get_pretty_python_uptime(custom_name: str = '') -> str:
    now = time.time()
    delta = now - _start_time
    str_uptime = str(timedelta(seconds=int(delta)))
    pretty_uptime = f"{custom_name} Uptime: {str_uptime}"
    return pretty_uptime.strip()
