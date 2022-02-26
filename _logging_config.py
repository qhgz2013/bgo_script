__all__ = ['bootstrap']

import logging
import re
import sys
import os
import time
from enum import Enum
from typing import *
import logging.handlers


class StrEnum(str, Enum):
    pass


class ConsoleColor(StrEnum):
    RESET = '\033[0m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD_RED = '\033[31;1m'


class ColorizedFormatter(logging.Formatter):
    def __init__(self, fmt: str, critical_color: str = ConsoleColor.BOLD_RED, error_color: str = ConsoleColor.RED,
                 warning_color: str = ConsoleColor.YELLOW, info_color: str = ConsoleColor.RESET,
                 debug_color: str = ConsoleColor.RESET):
        super(ColorizedFormatter, self).__init__()
        self._formatter = {
            logging.CRITICAL: logging.Formatter(f'{critical_color}{fmt}{ConsoleColor.RESET}'),
            logging.ERROR: logging.Formatter(f'{error_color}{fmt}{ConsoleColor.RESET}'),
            logging.WARNING: logging.Formatter(f'{warning_color}{fmt}{ConsoleColor.RESET}'),
            logging.INFO: logging.Formatter(f'{info_color}{fmt}{ConsoleColor.RESET}'),
            logging.DEBUG: logging.Formatter(f'{debug_color}{fmt}{ConsoleColor.RESET}')
        }

    def format(self, record: logging.LogRecord) -> str:
        return self._formatter[record.levelno].format(record)


class ScreenOutputFilter(logging.Filter):
    def __init__(self, level: Tuple[int] = (logging.DEBUG, logging.INFO)):
        super(ScreenOutputFilter, self).__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> int:
        return record.levelno in self.level


# https://stackoverflow.com/questions/24649789/how-to-force-a-rotating-name-with-pythons-timedrotatingfilehandler/25387192#25387192
# noinspection PyPep8Naming,PyTypeChecker
class ParallelTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 atTime=None, postfix=".log"):
        self.origFileName = filename
        self.postfix = postfix
        # <<< original TimedRotatingFileHandler
        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.interval = self.interval * interval  # multiply by units requested
        # <<< modifications
        t = int(time.time())
        # <<< super class __init__ moved here (and skips the parent TimedRotatingFileHandler)
        logging.handlers.BaseRotatingHandler.__init__(self, self.calculateFileName(t), 'a', encoding, delay)
        self.rolloverAt = self.computeRollover(t)

    def calculateFileName(self, currenttime):
        if self.utc:
            timeTuple = time.gmtime(currenttime)
        else:
            timeTuple = time.localtime(currenttime)

        return self.origFileName + "." + time.strftime(self.suffix, timeTuple) + self.postfix

    def getFilesToDelete(self):
        newFileName = self.calculateFileName(self.rolloverAt)
        dirName, fName = os.path.split(self.origFileName)
        dName, newFileName = os.path.split(newFileName)

        fileNames = os.listdir(dirName)
        result = []
        prefix = fName + "."
        postfix = self.postfix
        prelen = len(prefix)
        postlen = len(postfix)
        for fileName in fileNames:
            if fileName[:prelen] == prefix and fileName[-postlen:] == postfix and len(fileName) - postlen > prelen and \
                    fileName != newFileName:
                suffix = fileName[prelen:len(fileName) - postlen]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        self.baseFilename = os.path.abspath(self.calculateFileName(self.rolloverAt))
        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


default_formatter_str = '[%(asctime)s] [%(levelname)s] [%(name)s] (%(filename)s:%(lineno)d) %(message)s'


def _patched_get_files_to_delete(self):
    dir_name, base_name = os.path.split(self.baseFilename)
    base_name_no_ext, ext = os.path.splitext(base_name)
    file_names = os.listdir(dir_name)
    result = []
    prefix = base_name_no_ext + '.'
    suffix = ext
    plen = len(prefix)
    slen = len(suffix)
    for file_name in file_names:
        if file_name[:plen] == prefix and file_name[-slen:] == suffix:
            middle = file_name[plen:-slen]
            if self.extMatch.match(middle):
                result.append(os.path.join(dir_name, file_name))
    if len(result) < self.backupCount:
        result = []
    else:
        result.sort()
        result = result[:len(result) - self.backupCount]
    return result


def bootstrap(verbose: Optional[bool] = None, formatter_str: str = default_formatter_str, log_dir: str = 'logs',
              color: bool = True, log_to_screen: bool = True, log_to_screen_logger_name: Optional[str] = None,
              write_to_file: bool = True, write_to_file_logger_name: Optional[str] = None, max_file_cnt: int = 30):
    # todo: add docstring
    if verbose is None:
        # if verbose unset, detect it from argv
        verbose = '--verbose' in sys.argv
    logging.root.setLevel(logging.DEBUG)
    screen_logger = logging.getLogger(log_to_screen_logger_name)
    if log_to_screen:
        # log to screen:
        # DEBUG, INFO -> stdout
        # WARNING, ERROR, CRITICAL -> stderr
        stdout_handler = logging.StreamHandler(sys.stdout)
        stderr_handler = logging.StreamHandler(sys.stderr)
        if color and sys.stdout.isatty():
            # enable colorized output when color=True and stdout is console
            # stdout: default color
            stdout_formatter = ColorizedFormatter(formatter_str)
        else:
            # no color
            stdout_formatter = logging.Formatter(formatter_str)
        if color and sys.stderr.isatty():
            stderr_formatter = ColorizedFormatter(formatter_str)
        else:
            stderr_formatter = logging.Formatter(formatter_str)
        stdout_handler.setFormatter(stdout_formatter)
        stderr_handler.setFormatter(stderr_formatter)
        # if verbose: DEBUG, INFO -> stdout, otherwise: DEBUG -> filtered, INFO -> stdout
        if verbose:
            stdout_handler.setLevel(logging.DEBUG)
        else:
            stdout_handler.setLevel(logging.INFO)
        stderr_handler.setLevel(logging.WARNING)
        # stdout handler needs a filter to ignore WARNING, ERROR and CRITICAL log entries
        stdout_handler.addFilter(ScreenOutputFilter())
        # all done, add handlers to screen logger
        screen_logger.addHandler(stdout_handler)
        screen_logger.addHandler(stderr_handler)
    if write_to_file:
        # creating directory if not exist
        log_dir = os.path.abspath(log_dir)
        os.makedirs(log_dir, exist_ok=True)
        file_logger = logging.getLogger(write_to_file_logger_name)
        file_name = 'root' if write_to_file_logger_name is None else write_to_file_logger_name
        file_handler = ParallelTimedRotatingFileHandler(os.path.join(log_dir, file_name), 'midnight',
                                                        backupCount=max_file_cnt, encoding='utf8')
        file_handler.setFormatter(logging.Formatter(formatter_str))
        # set to DEBUG level
        file_handler.setLevel(logging.DEBUG)
        # todo: check impl
        # original implement:
        # file_logger.setLevel(logging.DEBUG) (not file_handler)
        file_logger.addHandler(file_handler)
        # write an initial debug log
        file_logger.debug('Logger initialized')

# fmt = logging.Formatter(fmt_str)
#
# # ROOT logging config
# root = logging.root
# stdout_handler = logging.StreamHandler(sys.stdout)
# if '--verbose' in sys.argv:
#     stdout_handler.setLevel(logging.DEBUG)
# else:
#     stdout_handler.setLevel(logging.INFO)
# if sys.stdout.isatty():
#     stdout_handler.setFormatter(logging.Formatter(f'\033[0m{fmt}'))
# else:
#     stdout_handler.setFormatter(fmt)
# stdout_handler.addFilter(ScreenOutputFilter())
# stderr_handler = logging.StreamHandler(sys.stderr)
# stderr_handler.setLevel(logging.WARNING)
# if sys.stderr.isatty():
#     stderr_handler.setFormatter()
# else:
#     stderr_handler.setFormatter(fmt)
# root.addHandler(stdout_handler)
# root.addHandler(stderr_handler)
# # root.setLevel(logging.INFO)
#
# # Script logging config
# script_logger_root = logging.getLogger('bgo_script')
# os.makedirs('logs', exist_ok=True)
# script_logging_handler = logging.FileHandler(datetime.now().strftime('logs/%Y-%m-%d.log'), 'a', encoding='utf8')
# fmt = logging.Formatter(fmt_str)
# script_logging_handler.setFormatter(fmt)
# script_logger_root.setLevel(logging.DEBUG)
# script_logger_root.addHandler(script_logging_handler)
# script_logger_root.debug('Root logger initialized')
