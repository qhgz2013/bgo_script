__all__ = ['script_logger_root']

import logging
import sys
import os
from datetime import datetime


class ScreenOutputFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> int:
        return record.levelno in (logging.DEBUG, logging.INFO)


fmt_str = '[%(asctime)s] [%(levelname)s] [%(name)s] (%(filename)s:%(lineno)d) %(message)s'
fmt = logging.Formatter(fmt_str)

# ROOT logging config
root = logging.root
stdout_handler = logging.StreamHandler(sys.stdout)
if '--verbose' in sys.argv:
    stdout_handler.setLevel(logging.DEBUG)
else:
    stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(fmt)
stdout_handler.addFilter(ScreenOutputFilter())
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
stderr_handler.setFormatter(fmt)
root.addHandler(stdout_handler)
root.addHandler(stderr_handler)
# root.setLevel(logging.INFO)

# Script logging config
script_logger_root = logging.getLogger('bgo_script')
os.makedirs('logs', exist_ok=True)
script_logging_handler = logging.FileHandler(datetime.now().strftime('logs/%Y-%m-%d.log'), 'a')
fmt = logging.Formatter(fmt_str)
script_logging_handler.setFormatter(fmt)
script_logger_root.setLevel(logging.DEBUG)
script_logger_root.addHandler(script_logging_handler)
script_logger_root.debug('Root logger initialized')
