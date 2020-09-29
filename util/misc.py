import subprocess
import locale
from typing import *
import logging

encodings = [locale.getpreferredencoding(), 'utf8', 'ansi', 'latin-1']
logger = logging.getLogger('bgo_script.util')


def spawn_process_raw(cmd: Union[str, Sequence[str]]) -> Tuple[int, bytes, bytes]:
    logger.debug('Spawning process using command: %s' % str(cmd))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out_msg, err_msg = proc.communicate()
    return proc.returncode, out_msg, err_msg


def _decode(b: bytes) -> str:
    last_exc = None
    for encoding in encodings:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError as e:
            last_exc = e
    raise last_exc


def spawn_process(cmd: Union[str, Sequence[str]]) -> Tuple[int, str, str]:
    ret_code, out_msg, err_msg = spawn_process_raw(cmd)
    return ret_code, _decode(out_msg).rstrip('\n'), _decode(err_msg).rstrip('\n')
