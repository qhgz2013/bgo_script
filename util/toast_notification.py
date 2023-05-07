# modified from https://gist.github.com/wontoncc/1808234
from win32api import *
from win32gui import *
import win32con
import pywintypes
import os
import time
import multiprocessing as mp
from typing import Optional

__all__ = ['WindowsBalloonTip', 'balloon_tip']


class WindowsBalloonTip:
    class_atom = None
    hinst = None

    def __init__(self, title: str, msg: str, destroy_delay: float = 10, icon_path: Optional[str] = None):
        """Create a balloon tip notification on Windows.

        Note: This class will block the calling thread until the notification is destroyed.

        :param title: Title of the notification
        :param msg: Message of the notification
        :param destroy_delay: Duration (in seconds) before the notification is destroyed
        :param icon_path: Icon file path of the notification, default: builtin IDI_APPLICATION icon
        """
        cls = type(self)
        message_map = {win32con.WM_DESTROY: self.on_destroy}
        # Register the Window class.
        if cls.class_atom is None:
            wc = WNDCLASS()
            cls.hinst = wc.hInstance = GetModuleHandle(None)
            wc.lpszClassName = "PythonTaskbar"
            wc.lpfnWndProc = message_map  # could also specify a wndproc.
            cls.class_atom = RegisterClass(wc)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = CreateWindow(cls.class_atom, "Taskbar", style, 0, 0, win32con.CW_USEDEFAULT, 
                                 win32con.CW_USEDEFAULT, 0, 0, cls.hinst, None)
        UpdateWindow(self.hwnd)
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        # noinspection PyUnresolvedReferences
        try:
            if icon_path is None:
                hicon = LoadIcon(0, win32con.IDI_APPLICATION)
            else:
                hicon = LoadImage(cls.hinst, os.path.abspath(icon_path), win32con.IMAGE_ICON, 0, 0, icon_flags)
        except pywintypes.error:
            hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "tooltip")
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO, win32con.WM_USER + 20, hicon, "Balloon tooltip",
                                      msg, 200, title))
        time.sleep(destroy_delay)
        DestroyWindow(self.hwnd)

    def on_destroy(self, _hwnd, _msg, _wparam, _lparam):
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        # PostQuitMessage(0) # Terminate the app.
        return 0


class _OrphanedProcess(mp.Process):
    def join(self, *args, **kwargs):
        pass

    def __del__(self):
        pass


def balloon_tip(title: str, msg: str, destroy_delay: float = 10, icon_path: Optional[str] = None):
    """Create a balloon tip notification on Windows (non-blocking method).

    :param title: Title of the notification
    :param msg: Message of the notification
    :param destroy_delay: Duration (in seconds) before the notification is destroyed
    :param icon_path: Icon file path of the notification, default: builtin IDI_APPLICATION icon
    """
    p = _OrphanedProcess(target=WindowsBalloonTip, args=(title, msg, destroy_delay, icon_path), daemon=False)
    p.start()
