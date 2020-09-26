import subprocess
import locale
from typing import *

encoding = locale.getpreferredencoding()


def spawn_process_raw(cmd: Union[str, Sequence[str]]) -> Tuple[bytes, bytes]:
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out_msg, err_msg = proc.communicate()
    return out_msg, err_msg


def spawn_process(cmd: Union[str, Sequence[str]]) -> str:
    out_msg, err_msg = spawn_process_raw(cmd)
    if len(err_msg) > 0:
        raise RuntimeError(str(err_msg, encoding).rstrip('\n'))
    return str(out_msg, encoding).rstrip('\n')
