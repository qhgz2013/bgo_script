import logging
import sys
import os
from datetime import datetime
fmt_str = '[%(asctime)s] [%(levelname)s] [%(name)s] (%(filename)s:%(lineno)d) %(message)s'
logging.basicConfig(format=fmt_str, level=logging.INFO, stream=sys.stdout)

script_logger_root = logging.getLogger('bgo_script')
os.makedirs('logs', exist_ok=True)
script_logging_handler = logging.FileHandler(datetime.now().strftime('logs/%Y-%m-%d.log'), 'a')
fmt = logging.Formatter(fmt_str)
script_logging_handler.setFormatter(fmt)
script_logger_root.setLevel(logging.DEBUG)
script_logger_root.addHandler(script_logging_handler)
script_logger_root.debug('Root logger initialized')
