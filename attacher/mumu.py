from . import AbstractAttacher
import win32gui
import win32con
import numpy as np
from warnings import warn
from time import sleep
from typing import *
from util import LazyValue


def is_admin() -> bool:
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


class MumuAttacher(AbstractAttacher):
    __warned_minimize = False

    def __init__(self):
        super(MumuAttacher, self).__init__()
        self.simulator_handle = None
        self.is_admin = LazyValue(is_admin)

    def locate_handle(self) -> int:
        # SPY++:
        # Qt5QWindowIcon, MuMu模拟器 or Game name
        # |- Qt5QWindowIcon, NemuPlayer
        #    |- canvasWin, canvas
        simulator_handle = win32gui.FindWindow('Qt5QWindowIcon', None)
        window_handle = 0
        while simulator_handle > 0:
            window_handle = win32gui.FindWindowEx(simulator_handle, 0, 'Qt5QWindowIcon', 'NemuPlayer')
            if window_handle > 0:
                break
            else:
                simulator_handle = win32gui.FindWindowEx(0, simulator_handle, 'Qt5QWindowIcon', None)
        assert window_handle > 0, 'Could not find child handle of Mumu simulator: NemuPlayer'
        self.simulator_handle = simulator_handle
        return window_handle

    def is_minimize(self) -> bool:
        self.handle()  # make sure it's initialized
        style = win32gui.GetWindowLong(self.simulator_handle, win32con.GWL_STYLE)
        return (style & win32con.WS_MINIMIZE) != 0

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        if self.is_minimize() and not self.__warned_minimize:
            warn('Screenshot capture is not supported for minimized window', RuntimeWarning)
            self.__warned_minimize = True
        while True:
            while self.is_minimize():
                sleep(0.2)
            screenshot = super(MumuAttacher, self).get_screenshot(width, height)
            if not self.is_minimize():
                return screenshot

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        if not self.is_admin():
            warn('Could not send message to specified handle without admin privileges', RuntimeWarning)
        else:
            super(MumuAttacher, self).send_click(x, y, stay_time)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        if not self.is_admin():
            warn('Could not send message to specified handle without admin privileges', RuntimeWarning)
        else:
            super(MumuAttacher, self).send_slide(p_from, p_to, stay_time_before_move, stay_time_move,
                                                 stay_time_after_move)
