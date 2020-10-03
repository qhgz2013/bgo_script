import subprocess
import locale
from typing import *
import logging

encodings = [locale.getpreferredencoding(), 'utf8', 'ansi', 'latin-1']
logger = logging.getLogger('bgo_script.util')


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
