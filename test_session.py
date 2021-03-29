import _logging_config
from util import AdbShellWrapper, find_adb_path
import subprocess
import threading
import numpy as np
import matplotlib.pyplot as plt


class AdbShellWrapperDbg:
    def __init__(self, adb_path: str):
        pipe = subprocess.PIPE
        self._adb_proc = subprocess.Popen([adb_path, 'shell'], stdin=pipe, stdout=pipe, stderr=subprocess.STDOUT, shell=True, close_fds=True)
        self._mutex = threading.RLock()
        self._boundary = None
        self._stdout_printer = threading.Thread()
        self._session_result = None
        self._stdout_thread = threading.Thread(target=self._print_msg_callback, daemon=True,
                                               args=(self._adb_proc.stdout, 'stdout'))
        # self._stdout_thread.start()

    def _print_msg_callback(self, f, msg_type: str):
        import sys
        while self._adb_proc.poll() is None:
            ch = f.read(1).decode('utf8')
            if ch == '\r':
                ch = '\\r'
            sys.stdout.write(ch)
            sys.stdout.flush()

    def interact(self, cmd: str, **_):
        with self._mutex:
            cmd = cmd.encode('utf8') + b'\n'
            self._session_result = None
            self._adb_proc.stdin.write(cmd)
            self._adb_proc.stdin.flush()


if __name__ == '__main__':
    shell = AdbShellWrapperDbg(find_adb_path())
    # while True:
    #     cmd = input('> ')
    #     shell.interact(cmd)
    # shell.interact('stty -a')
    shell.interact("whoami;\nsu -c 'sleep 1';\nwhoami", wait=False)
    print(shell._adb_proc.communicate(b"who am i;\nsu -c 'sleep 1';\nwho am i\n"))
    # shell._adb_proc.stdin.close()
    # shell.interact('echo 124\nwhoami', wait=False)
    # shell.interact('whoami')
    from time import sleep
    sleep(5)
