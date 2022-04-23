# _logging_config.py
# Provides my flavored solution to log messages on screen and to files
# Ver 1.3
# Changelog:
# Ver 1.3: Server port is now randomly selected one of the unused ports, and passes the port to child processes via
#          environment variable. bootstrap() is now implicitly called for child processes during import. Parameter
#          "backupCount" for ParallelTimedRotatingFileHandler is now worked even without rollover.
# Ver 1.2: Minor bug fixed (child logger would propagate same logs to parent logger) and added typing supports for
#          bootstrap().
# Ver 1.1: Added multiprocessing support (via local TCP socket), the configuration of child process is exactly same as
#          the parent process, i.e., calling bootstrap(), but no need for passing arguments since all log messages will
#          be redirected to parent process.
# Ver 1.0: All initial operations are now moved to bootstrap() function. Call it in main() and enjoys everything.
import logging
import re
import sys
import os
import threading
import time
from enum import Enum
from typing import *
import logging.handlers
import socketserver
import struct
import pickle

__all__ = ['bootstrap', 'default_formatter_str', 'bootstrap_parent', 'bootstrap_child']


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
        self._formatter: Dict[int, logging.Formatter] = {
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
        # since backupCount only works during rollover, we have to call it after init
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

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


class ForwardHandler(logging.Handler):
    """Do nothing, just forward the message to the next handler."""
    def __init__(self, forward_handler: logging.Handler):
        super(ForwardHandler, self).__init__()
        self.forward_handler = forward_handler

    def emit(self, record: logging.LogRecord) -> None:
        if self.forward_handler is not None:
            self.forward_handler.handle(record)


default_formatter_str = '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] (%(filename)s:%(lineno)d) %(message)s'
LOGGER_CONFIG_DICT = Optional[Dict[Optional[str], Optional[int]]]
LOGGING_SERVER_PORT_KEY = '_LOGGING_SERVER_PORT'


def bootstrap_parent(formatter_str: str = default_formatter_str, log_dir: str = 'logs', color: bool = True,
                     log_to_screen: bool = True, log_to_screen_loggers: LOGGER_CONFIG_DICT = None,
                     default_log_to_screen_level: Optional[int] = None,
                     write_to_file: bool = True, write_to_file_loggers: LOGGER_CONFIG_DICT = None,
                     default_write_to_file_level: Optional[int] = None, file_name_prefix: str = '(root)',
                     max_file_cnt: int = 10) -> None:
    """Configurate logging module.

    Known side effect: attribute "propagate" will be set to False

    :param formatter_str: The format string deciding what the log messages look like.
    :param log_dir: The subdirectory name where the log files should be put in.
    :param color: Display the colorized logs to screen if stdout or stderr is console.
    :param log_to_screen: Whether the log records should be displayed on screen (via stdout and stderr). INFO
     (and DEBUG depending on verbose argument) records will be logged to stdout while WARNING, ERROR and CRITICAL
     records will be logged to stderr.
    :param log_to_screen_loggers: A Dictionary specifying {logger_name, log_level}. Set logger_name to None to specify
     root logger, and set log_level to None to use default_log_to_screen_level (the next argument).
    :param default_log_to_screen_level: Specify the log level to display records on screen, leave None to detect from
     argv (DEBUG if "--verbose" is set, INFO otherwise).
    :param write_to_file: Whether the log records should be written to log files.
    :param write_to_file_loggers: A Dictionary specifying {logger_name, log_level}. Same as log_to_screen_loggers.
    :param default_write_to_file_level: Specify the log level to write to file, leave None will be treated as DEBUG.
    :param file_name_prefix: The prefix of log file. The log files are generated as "file_name_prefix.yyyy-mm-dd.log".
    :param max_file_cnt: Max log files in the log_dir.
    """
    verbose = '--verbose' in sys.argv
    if default_log_to_screen_level is None:
        default_log_to_screen_level = logging.DEBUG if verbose else logging.INFO
    if default_write_to_file_level is None:
        default_write_to_file_level = logging.DEBUG
    if log_to_screen_loggers is None:
        log_to_screen_loggers = {None: None}
    if write_to_file_loggers is None:
        write_to_file_loggers = {None: None}
    logging.root.setLevel(logging.DEBUG)
    if log_to_screen:
        # log to screen:
        # DEBUG, INFO -> stdout
        # WARNING, ERROR, CRITICAL -> stderr
        for log_to_screen_logger_name, log_to_screen_effective_level in log_to_screen_loggers.items():
            if log_to_screen_effective_level is None:
                log_to_screen_effective_level = default_log_to_screen_level
            screen_logger = logging.getLogger(log_to_screen_logger_name)
            # after configured, the child logger does not propagate log records to parent logger.
            # otherwise, a single log record will be logger twice or more
            screen_logger.propagate = False
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
            if 0 < log_to_screen_effective_level <= logging.INFO:
                stdout_handler.setLevel(log_to_screen_effective_level)
                # stdout handler needs a filter to ignore WARNING, ERROR and CRITICAL log entries
                stdout_handler.addFilter(ScreenOutputFilter())
                screen_logger.addHandler(stdout_handler)
            # noinspection PyTypeChecker
            stderr_handler.setLevel(max(logging.WARNING, log_to_screen_effective_level))
            screen_logger.addHandler(stderr_handler)
            # screen_logger.setLevel(log_to_screen_effective_level)
    if write_to_file:
        # creating directory if not exist
        log_dir = os.path.abspath(log_dir)
        os.makedirs(log_dir, exist_ok=True)
        file_handler = ParallelTimedRotatingFileHandler(os.path.join(log_dir, file_name_prefix), 'midnight',
                                                        backupCount=max_file_cnt, encoding='utf8')
        file_handler.setFormatter(logging.Formatter(formatter_str))
        file_handler.setLevel(logging.DEBUG)
        for write_to_file_logger_name, write_to_file_effective_level in write_to_file_loggers.items():
            file_logger = logging.getLogger(write_to_file_logger_name)
            file_logger.propagate = False
            if write_to_file_effective_level is None:
                write_to_file_effective_level = default_write_to_file_level
            forwarder = ForwardHandler(file_handler)
            forwarder.setLevel(write_to_file_effective_level)
            file_logger.addHandler(forwarder)
    # multiprocessing supports, socket-based implementation
    mp_log_server = LogRecordSocketReceiver('localhost', 0)
    mp_log_server.server_forever_non_blocking()
    os.putenv(LOGGING_SERVER_PORT_KEY, str(mp_log_server.server_address[1]))


# a small modification from
# https://docs.python.org/3/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network
class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            logger = logging.getLogger(record.name)
            logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """Simple TCP socket-based logging receiver suitable for testing."""

    allow_reuse_address = True

    def __init__(self, host: str = 'localhost', port: int = 0,
                 handler: Type[socketserver.BaseRequestHandler] = LogRecordStreamHandler,
                 timeout: Optional[float] = None):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.timeout = timeout

    def server_forever_non_blocking(self):
        thd = threading.Thread(target=self.serve_forever, args=(self.timeout,), daemon=True)
        thd.start()


def bootstrap_child() -> None:
    """Called from child process, all logging events should be transferred to parent process via socket."""
    logging_server_port = os.getenv(LOGGING_SERVER_PORT_KEY, None)
    if logging_server_port is None:
        raise RuntimeError('Logging server port is not set')
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(logging.handlers.SocketHandler('localhost', int(logging_server_port)))


# typing supports
# for parent process
@overload
def bootstrap(formatter_str: str = default_formatter_str, log_dir: str = 'logs', color: bool = True,
              log_to_screen: bool = True, log_to_screen_loggers: LOGGER_CONFIG_DICT = None,
              default_log_to_screen_level: Optional[int] = None,
              write_to_file: bool = True, write_to_file_loggers: LOGGER_CONFIG_DICT = None,
              default_write_to_file_level: Optional[int] = None, file_name_prefix: str = '(root)',
              max_file_cnt: int = 10):
    ...


# for child class
@overload
def bootstrap():
    ...


_bootstrap_called = False  # prevent duplicated calls


def bootstrap(*args, **kwargs):
    global _bootstrap_called
    if _bootstrap_called:
        return
    logging_server_port = os.getenv(LOGGING_SERVER_PORT_KEY, None)
    if logging_server_port is None:
        # parent process
        bootstrap_parent(*args, **kwargs)
    else:
        # child process
        bootstrap_child()
    _bootstrap_called = True


# bootstrap.__annotations__ = bootstrap_parent.__annotations__
# bootstrap.__doc__ = bootstrap_parent.__doc__

def _bootstrap_auto_call():
    # only call bootstrap for child process
    if os.getenv(LOGGING_SERVER_PORT_KEY, None) is not None:
        bootstrap()


_bootstrap_auto_call()
