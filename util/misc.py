import subprocess
import locale
from types import TracebackType
from typing import *
from typing import IO
import logging
import os
import sys
from io import BytesIO

__all__ = ['spawn_process_raw', 'spawn_process', 'find_path', 'SingletonMeta', 'FIFOBuffer']

encodings = [locale.getpreferredencoding(), 'utf8', 'ansi', 'latin-1']
logger = logging.getLogger('bgo_script.util')
_cached_path = None


def spawn_process_raw(cmd: Union[str, Sequence[str]], timeout: Optional[float] = None,
                      timed_out_retry: int = 5) -> Tuple[int, bytes, bytes]:
    logger.debug('Spawning process using command: %s' % str(cmd))
    proc = None,
    out_msg = None
    err_msg = None
    for i in range(timed_out_retry):
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_msg, err_msg = proc.communicate(timeout=timeout)
            break
        except subprocess.TimeoutExpired:
            if i + 1 == timed_out_retry:
                raise
            logger.warning('Process communication timed out, retrying %d / %d' % (i + 1, timed_out_retry))
    return proc.returncode, out_msg, err_msg


def _decode(b: bytes) -> str:
    last_exc = None
    for encoding in encodings:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError as e:
            last_exc = e
    raise last_exc


def spawn_process(cmd: Union[str, Sequence[str]], timeout: Optional[float] = None,
                  timed_out_retry: int = 5) -> Tuple[int, str, str]:
    ret_code, out_msg, err_msg = spawn_process_raw(cmd, timeout, timed_out_retry)
    return ret_code, _decode(out_msg).rstrip('\n'), _decode(err_msg).rstrip('\n')


def find_path(file: str) -> Optional[str]:
    """
    Find file in PATH environment

    :param file: File to find
    :return: Absolute path for the specified file (if found) or none
    """
    global _cached_path
    if _cached_path is None:
        _cached_path = set(sys.path)
        _cached_path.update(os.getenv('PATH').split(os.pathsep))
        logger.debug('PATH environment: %s', _cached_path)
    for path in _cached_path:
        candidate_file = os.path.abspath(os.path.join(path, file))
        if os.path.isfile(candidate_file):
            return candidate_file


class SingletonMeta(type):
    """A singleton meta class"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def __remove_instance__(cls):
        del cls._instances[cls]


class FIFOBuffer(IO[bytes]):
    def close(self) -> None:
        self._buf.close()

    def fileno(self) -> int:
        return self._buf.fileno()

    def flush(self) -> None:
        self._buf.flush()

    def isatty(self) -> bool:
        return self._buf.isatty()

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def readable(self) -> bool:
        return self._buf.readable()

    def readline(self, limit: int = -1) -> bytes:
        return self._buf.readline(limit)

    def readlines(self, hint: int = -1) -> List[bytes]:
        return self._buf.readlines(hint)

    def seek(self, offset: int, whence: int = 0) -> int:
        raise IOError

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        return 0

    def truncate(self, size: Optional[int] = None) -> int:
        raise IOError

    def writable(self) -> bool:
        return self._buf.writable()

    def writelines(self, lines: Iterable[bytes]) -> None:
        for line in lines:
            self.write(line)

    def __next__(self) -> bytes:
        return self.readline()

    def __iter__(self) -> Iterator[bytes]:
        return self

    def __enter__(self) -> IO[bytes]:
        return self

    def __exit__(self, t: Optional[Type[BaseException]], value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> Optional[bool]:
        self.close()
        return None

    def __init__(self, gc_size: int = 0x1e00000):
        self._buf = BytesIO()
        self._gc_size = gc_size

    def write(self, s: bytes) -> int:
        read_pos = self._buf.tell()
        if read_pos > self._gc_size:
            new_buffer = BytesIO()
            new_buffer.write(self._buf.read())
            new_buffer.seek(0)
            self._buf.close()
            self._buf = new_buffer
            read_pos = 0
        self._buf.seek(0, 2)
        bytes_wrote = self._buf.write(s)
        self._buf.seek(read_pos)
        return bytes_wrote
