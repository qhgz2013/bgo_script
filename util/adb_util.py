import subprocess
import threading
from typing import *
from typing import IO
import os
from io import StringIO
import logging
from .misc import find_path

pipe = subprocess.PIPE
logger = logging.getLogger('bgo_script.util.adb')
_cache_adb_path_not_found = object()
_cache_adb_path = None


def find_adb_path() -> Optional[str]:
    """
    Find adb executable in PATH environment
    :return: Absolute path for adb executable (if found) or none
    """
    global _cache_adb_path
    if _cache_adb_path is None:
        _cache_adb_path = find_path('adb.exe') or _cache_adb_path_not_found
        if _cache_adb_path == _cache_adb_path_not_found:
            logger.warning('ADB executable not found in PATH environment')
        else:
            logger.debug('ADB executable path: %s', _cache_adb_path)
    if _cache_adb_path == _cache_adb_path_not_found:
        return None
    return _cache_adb_path


class AdbShellWrapper:
    def __init__(self, adb_path: str):
        self._adb_proc = subprocess.Popen([adb_path, 'shell'], stdin=pipe, stdout=pipe, stderr=pipe)
        self._mutex = threading.RLock()
        self._boundary = None
        self._stdout_buf = StringIO()
        self._stderr_buf = StringIO()
        self._session_started = threading.Event()
        self._session_finished = threading.Event()
        self._stdout_printer = threading.Thread()
        self._session_result = None
        self._wait_session = None
        self._stdout_thread = threading.Thread(target=self._print_msg_callback, daemon=True,
                                               args=(self._adb_proc.stdout, 'stdout', self._stdout_buf))
        self._stdout_thread.start()
        self._stderr_thread = threading.Thread(target=self._print_msg_callback, daemon=True,
                                               args=(self._adb_proc.stderr, 'stderr', self._stderr_buf))
        self._stderr_thread.start()

    def _print_msg_callback(self, f: IO, msg_type: str, target_buf: StringIO):
        while self._adb_proc.poll() is None:
            data = f.readline().decode('utf8').rstrip()
            if len(data) == 0:
                continue
            with self._mutex:
                logger.debug('%s: %s', msg_type, data)
                if self._boundary is None:
                    # no session available here
                    continue
                if self._session_started.is_set():
                    if data != self._boundary:
                        # logger.warning('Adb shell session error: unexpected output "%s", ignored.', data)
                        continue
                    self._session_started.clear()
                    if not self._wait_session:
                        self._session_finished.set()
                    continue
                elif data.startswith(self._boundary):
                    if data == self._boundary + '-s':
                        self._session_result = 0
                        self._session_finished.set()
                        continue
                    elif data.startswith(self._boundary + '-f'):
                        self._session_result = int(data[len(self._boundary)+2:])
                        self._session_finished.set()
                        continue
                target_buf.write(data + '\n')

    @staticmethod
    def _build_command(args: Sequence[Any]) -> str:
        if len(args) == 0:
            return ''
        iobuf = StringIO()
        iobuf.write(str(args[0]))
        for arg in args[1:]:
            iobuf.write(" '")
            iobuf.write(str(arg).replace("'", "'\"'\"'"))
            iobuf.write("'")
        return iobuf.getvalue()

    def interact(self, cmd: Union[str, Sequence[Any]], wait: bool = True) -> Optional[Tuple[int, str, str]]:
        if not isinstance(cmd, str):
            cmd = self._build_command(cmd)
        boundary = '--' + os.urandom(8).hex()
        cmd = f'echo {boundary} && ((({cmd}) && echo {boundary}-s) || echo {boundary}-f$?)'
        with self._mutex:
            self._boundary = boundary
            logger.debug('stdin: %s', cmd)
            cmd = cmd.encode('utf8') + b'\n'
            self._session_result = None
            self._wait_session = wait
            self._adb_proc.stdin.write(cmd)
            self._adb_proc.stdin.flush()
            self._session_started.set()
        self._session_finished.wait()
        self._session_finished.clear()
        if not wait:
            return None
        with self._mutex:
            stdout = self._stdout_buf.getvalue()
            stderr = self._stderr_buf.getvalue()
            self._stdout_buf.seek(0)
            self._stderr_buf.seek(0)
            self._stdout_buf.truncate(0)
            self._stderr_buf.truncate(0)
        # noinspection PyTypeChecker
        return self._session_result, stdout, stderr
