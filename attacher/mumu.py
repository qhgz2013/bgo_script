# attacher.mumu
# Mumu simulator (blue one) related implementation.
# Ver 1.0
# Changelog:
# 1.0: Remove outdated WinAPI based attacher and simplify implementation.
from typing import *
import win32gui
import win32ui
import win32con
import numpy as np
from logging import getLogger
from .base import ScreenCapturer, CapturerRegistry, AttacherRegistry
from time import sleep
from util import LazyValue, register_handler
from .adb_util import ADBServer, spawn
from .adb import EventID, EventType, ADBRootAttacher, ADBAttacher
from basic_class import Resolution

__all__ = ['WinAPIScreenCapturer', 'MumuScreenCapturer', 'MumuADBServer', 'MumuAttacher', 'MumuRootAttacher']

logger = getLogger('bgo_script.attacher')


def locate_mumu_simulator_handle() -> Tuple[int, int]:
    """Locate Mumu simulator window, returns a tuple of (host_handle, player_handle)."""
    # SPY++:
    # Qt5QWindowIcon, MuMu模拟器 or Game name
    # |- Qt5QWindowIcon, NemuPlayer
    #    |- canvasWin, canvas
    host_handle = win32gui.FindWindow('Qt5QWindowIcon', None)
    player_handle = 0
    while host_handle > 0:
        player_handle = win32gui.FindWindowEx(host_handle, 0, 'Qt5QWindowIcon', 'NemuPlayer')
        if player_handle > 0:
            break
        else:
            host_handle = win32gui.FindWindowEx(0, host_handle, 'Qt5QWindowIcon', None)
    if player_handle <= 0:
        raise RuntimeError('Could not find child handle of Mumu simulator: NemuPlayer')
    logger.info(f'Located Mumu simulator handle: host: {host_handle:#x}, player: {player_handle:#x}')
    return host_handle, player_handle


def get_screenshot_winapi_impl(handle: int) -> np.ndarray:
    left, top, right, bottom = win32gui.GetWindowRect(handle)
    window_height = bottom - top
    window_width = right - left
    handle_dc = win32gui.GetWindowDC(handle)
    new_dc = win32ui.CreateDCFromHandle(handle_dc)
    compat_dc = new_dc.CreateCompatibleDC()
    new_bitmap = win32ui.CreateBitmap()
    new_bitmap.CreateCompatibleBitmap(new_dc, window_width, window_height)
    compat_dc.SelectObject(new_bitmap)
    compat_dc.BitBlt((0, 0), (window_width, window_height), new_dc, (0, 0), win32con.SRCCOPY)
    arr = new_bitmap.GetBitmapBits(True)
    arr = np.fromstring(arr, dtype='uint8').reshape([window_height, window_width, -1])
    new_dc.DeleteDC()
    compat_dc.DeleteDC()
    win32gui.ReleaseDC(handle, handle_dc)
    win32gui.DeleteObject(new_bitmap.GetHandle())
    screenshot = np.flip(arr[..., :3], -1)
    return screenshot


def check_window_minimized(handle: int) -> bool:
    style = win32gui.GetWindowLong(handle, win32con.GWL_STYLE)
    return (style & win32con.WS_MINIMIZE) != 0


class WinAPIScreenCapturer(ScreenCapturer):
    """Capturing screenshot using WinAPI.

    Note: It is the native solution with the best performance, but will not work under the conditions like:
    (1) The window of located handle is minimized (a blank screenshot will be obtained);
    (2) Part of window is out of display size (the exceeded area will not be re-draw thanks to the Windows mechanism);
    (3) Logged in as remote desktop users but the client-side window is minimized or disconnected.
    """
    def __init__(self):
        super(WinAPIScreenCapturer, self).__init__()
        self.screen_cap_handle = LazyValue(self.locate_handle)

    def get_resolution(self) -> Resolution:
        left, top, right, bottom = win32gui.GetWindowRect(self.screen_cap_handle())
        return Resolution(bottom - top, right - left)

    def get_screenshot(self) -> np.ndarray:
        return get_screenshot_winapi_impl(self.screen_cap_handle())

    def locate_handle(self) -> int:
        """Implement the handle lookup process here. WinAPI calls will be applied to the located handle."""
        raise NotImplementedError


@register_handler(CapturerRegistry, 'mumu')
class MumuScreenCapturer(WinAPIScreenCapturer):
    """Screen capture implementation for mumu simulator."""
    __warned_minimize = False

    def __init__(self):
        super(MumuScreenCapturer, self).__init__()
        self.simulator_host_handle = 0

    def locate_handle(self) -> int:
        host_handle, player_handle = locate_mumu_simulator_handle()
        self.simulator_host_handle = host_handle
        return player_handle

    def get_screenshot(self) -> np.ndarray:
        if check_window_minimized(self.simulator_host_handle) and not self.__warned_minimize:
            logger.warning('Screenshot capture is not supported for minimized window')
            self.__warned_minimize = True
        while True:
            while check_window_minimized(self.simulator_host_handle):
                sleep(0.2)
            screenshot = super(MumuScreenCapturer, self).get_screenshot()
            if not check_window_minimized(self.simulator_host_handle):
                return screenshot


class MumuADBServer(ADBServer):
    def __init__(self, adb_executable_path: Optional[str] = None):
        super(MumuADBServer, self).__init__(adb_executable_path)

    def _start_internal(self):
        super(MumuADBServer, self)._start_internal()
        # hooks here
        result = spawn(self.adb_executable, 'connect', 'localhost:7555', raise_exc=True).strip()
        if len(result) > 0 and not result.startswith('connected to') and not result.startswith('already connected to'):
            raise RuntimeError(f'Failed to connect Mumu simulator via ADB: {result}')


# the original one uses WinAPI to simulate clicks and slides, but it does not work now
@register_handler(AttacherRegistry, 'mumu')
class MumuAttacher(ADBAttacher):
    def __init__(self, adb_server: Optional[ADBServer] = None):
        adb_server = adb_server or MumuADBServer()
        super(MumuAttacher, self).__init__(adb_server, device='localhost:7555')


@register_handler(AttacherRegistry, 'mumu_root')
class MumuRootAttacher(ADBRootAttacher):
    def __init__(self, adb_server: Optional[ADBServer] = None):
        adb_server = adb_server or MumuADBServer()
        super(MumuRootAttacher, self).__init__(adb_server, device='localhost:7555')

    def _hook_send_event_touch_down(self, device: str, args: List[str], px: int, py: int):
        # Mumu simulator requires ABS_MT_TRACKING_ID
        args.insert(0, f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_TRACKING_ID} 1')

    def _hook_send_event_touch_up(self, device: str, args: List[str]):
        args.insert(0, f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_TRACKING_ID} 0')
