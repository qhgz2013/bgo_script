# https://gist.github.com/wontoncc/1808234
from win32api import *
from win32gui import *
import win32con
import sys, os
import struct
import time
import multiprocessing as mp

__all__ = ['WindowsBalloonTip', 'balloon_tip']


class WindowsBalloonTip:
    class_atom = None

    def __init__(self, title: str, msg: str, destroy_delay: float = 10):
        cls = type(self)
        message_map = {win32con.WM_DESTROY: self.on_destroy}
        # Register the Window class.
        if cls.class_atom is None:
            wc = WNDCLASS()
            hinst = wc.hInstance = GetModuleHandle(None)
            wc.lpszClassName = "PythonTaskbar"
            wc.lpfnWndProc = message_map  # could also specify a wndproc.
            cls.class_atom = RegisterClass(wc)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = CreateWindow(cls.class_atom, "Taskbar", style, 0, 0, win32con.CW_USEDEFAULT, 
                                 win32con.CW_USEDEFAULT, 0, 0, hinst, None)
        UpdateWindow(self.hwnd)
        icon_path = os.path.abspath(os.path.join(sys.path[0], "balloontip.ico"))
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        try:
            hicon = LoadImage(hinst, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
        except:
            hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "tooltip")
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO, win32con.WM_USER+20, hicon, "Balloon tooltip", 
                                      msg, 200, title))
        time.sleep(destroy_delay)
        DestroyWindow(self.hwnd)

    def on_destroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        # PostQuitMessage(0) # Terminate the app.
        return 0


class _OrphanedProcess(mp.Process):
    def join(self, *args, **kwargs):
        pass

    def __del__(self):
        pass


def balloon_tip(title: str, msg: str, destroy_delay: float = 10):
    p = _OrphanedProcess(target=WindowsBalloonTip, args=(title, msg, destroy_delay), daemon=False)
    p.start()
