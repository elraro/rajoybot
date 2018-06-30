import platform
import uptime
from datetime import timedelta
import time

_start_time = time.time()


def get_pretty_machine_uptime_string():
    # Machine info
    uptime_seconds = uptime.uptime()
    machine_uptime = str(timedelta(seconds=uptime_seconds))
    return "Machine Uptime: " + machine_uptime


def get_pretty_machine_info():
    uname = platform.uname()
    return "Running on " + uname[0] + " " + uname[2] + " " + uname[4]


def get_pretty_python_uptime(custom_name=''):
    now = time.time()
    delta = now - _start_time
    str_uptime = str(timedelta(seconds=int(delta)))
    pretty_uptime = "{custom_name} Uptime: {uptime}".format(custom_name=custom_name, uptime=str_uptime)
    return pretty_uptime.strip()