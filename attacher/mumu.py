from . import HandleBasedAttacher
from .adb import AdbAttacherRootEnhanced, EventType, EventID
import win32gui
import win32con
import numpy as np
from time import sleep
from typing import *
from util import LazyValue, spawn_process_raw
from winapi import is_running_as_admin
import logging

logger = logging.getLogger('bgo_script.attacher')


class MumuAttacher(HandleBasedAttacher):
    __warned_minimize = False
    __warned_deprecated_v1_attacher = False

    def __init__(self):
        super(MumuAttacher, self).__init__()
        self.simulator_handle = None
        self.is_admin = LazyValue(is_running_as_admin)
        if not MumuAttacher.__warned_deprecated_v1_attacher:
            MumuAttacher.__warned_deprecated_v1_attacher = True
            logger.warning('Mumu Attacher (V1 version) is deprecated since some versions of mumu simulator does not '
                           'work properly with PostMessage / SendMessage to simulate mouse move event')

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
        logger.info('Located Mumu simulator handle: %d' % self.simulator_handle)
        return window_handle

    def is_minimize(self) -> bool:
        self.handle()  # make sure it's initialized
        style = win32gui.GetWindowLong(self.simulator_handle, win32con.GWL_STYLE)
        return (style & win32con.WS_MINIMIZE) != 0

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        if self.is_minimize() and not self.__warned_minimize:
            logger.warning('Screenshot capture is not supported for minimized window')
            self.__warned_minimize = True
        while True:
            while self.is_minimize():
                sleep(0.2)
            screenshot = HandleBasedAttacher.get_screenshot(self, width, height)
            if not self.is_minimize():
                return screenshot

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        if not self.is_admin():
            logger.warning('Could not send message to specified handle without admin privileges')
        else:
            HandleBasedAttacher.send_click(self, x, y, stay_time)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        if not self.is_admin():
            logger.warning('Could not send message to specified handle without admin privileges')
        else:
            HandleBasedAttacher.send_slide(self, p_from, p_to, stay_time_before_move, stay_time_move,
                                           stay_time_after_move)


class MumuAttacherV2(MumuAttacher, AdbAttacherRootEnhanced):
    def __init__(self):
        super(MumuAttacher, self).__init__()

    def _hook_after_sever_started(self):
        spawn_process_raw([self._adb, 'connect', 'localhost:7555'])

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        return MumuAttacher.get_screenshot(self, width, height)

    def _hook_send_event_touch_down(self, device: str, args: List[str], px: int, py: int):
        # Mumu simulator requires ABS_MT_TRACKING_ID
        args.insert(0, f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_TRACKING_ID.value} 1')

    def _hook_send_event_touch_up(self, device: str, args: List[str]):
        args.insert(0, f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_TRACKING_ID.value} 0')

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        AdbAttacherRootEnhanced.send_click(self, x, y, stay_time)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        AdbAttacherRootEnhanced.send_slide(self, p_from, p_to, stay_time_before_move, stay_time_move, stay_time_after_move)
