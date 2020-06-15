# Version: 1.0
import sys
import ctypes
from typing import *
from logging import root
import win32pipe
import win32file
import pickle
import struct


def is_running_as_admin() -> bool:
    return ctypes.windll.shell32.IsUserAnAdmin()


def run_as_admin(wait_exit: bool = True) -> Optional[int]:
    # noinspection PyUnresolvedReferences
    from win32com.shell.shell import ShellExecuteEx
    from win32event import WaitForSingleObject, INFINITE
    from win32process import GetExitCodeProcess
    # import win32con
    # noinspection PyUnresolvedReferences
    from win32com.shell import shellcon
    import win32api
    cmd = '"%s"' % sys.executable
    params = ' '.join(['"%s"' % x for x in sys.argv])
    proc = ShellExecuteEx(lpFile=cmd, lpParameters=params, lpVerb='runas',  # nShow=win32con.SW_SHOWNORMAL,
                          fMask=shellcon.SEE_MASK_NOCLOSEPROCESS)
    if wait_exit:
        handle = proc['hProcess']
        WaitForSingleObject(handle, INFINITE)
        rc = GetExitCodeProcess(handle)
        win32api.CloseHandle(handle)
        return rc


class BasicNamedPipe:
    def __init__(self, pipe):
        self._pipe = pipe

    def close(self):
        win32file.CloseHandle(self._pipe)

    def send(self, msg: Any):
        packed_msg = pickle.dumps(msg)
        msg_length = struct.pack('>I', len(packed_msg))
        # 64k segmentation write
        full_msg = msg_length + packed_msg
        for i in range(0, len(full_msg), 65536):
            win32file.WriteFile(self._pipe, full_msg[i*65536:(i+1)*65536])
        win32file.FlushFileBuffers(self._pipe)

    def recv(self) -> Any:
        err, full_msg = win32file.ReadFile(self._pipe, 65536)
        if err != 0:
            raise RuntimeError('Read from named pipe error: %d' % err)
        if len(full_msg) < 4:
            raise ValueError('Invalid format')
        msg_length = struct.unpack('>I', full_msg[:4])[0]
        packed_msg = full_msg[4:]
        while len(packed_msg) < msg_length:
            err, msg = win32file.ReadFile(self._pipe, 65536)
            if err != 0:
                raise RuntimeError('Read from named pipe error: %d' % err)
            packed_msg += msg
        return pickle.loads(packed_msg)


class NamedPipeServer(BasicNamedPipe):
    def __init__(self, name: str, wait_connected: bool = False, block_io: bool = True):
        pipe = win32pipe.CreateNamedPipe('\\\\.\\pipe\\' + name, win32pipe.PIPE_ACCESS_DUPLEX,
                                         win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE |
                                         (win32pipe.PIPE_WAIT if block_io else win32pipe.PIPE_NOWAIT),
                                         1, 65536, 65536, 0, None)
        root.info('WINAPI: Created named pipe %s: %s' % (name, str(pipe)))
        if wait_connected:
            win32pipe.ConnectNamedPipe(pipe, None)
        super(NamedPipeServer, self).__init__(pipe)


class NamedPipeClient(BasicNamedPipe):
    def __init__(self, name: str):
        pipe = win32file.CreateFile('\\\\.\\pipe\\' + name, win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                    0, None, win32file.OPEN_EXISTING, 0, None)
        if win32pipe.SetNamedPipeHandleState(pipe, win32pipe.PIPE_READMODE_MESSAGE, None, None):
            raise RuntimeError('Could not set pipe mode to PIPE_TYPE_MESSAGE')
        root.info('WINAPI: Connected to named pipe %s: %s' % (name, str(pipe)))
        super(NamedPipeClient, self).__init__(pipe)
