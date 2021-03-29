import numpy as np
from typing import *
from util import LazyValue
import win32gui
import win32con
import win32ui
from time import sleep, time
import image_process
import logging

logger = logging.getLogger('bgo_script.attacher')


class AbstractAttacher:
    """
    AbstractAttacher defines the basic interface to interact with the game application
    """
    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        raise NotImplementedError

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        raise NotImplementedError

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        raise NotImplementedError


class HandleBasedAttacher(AbstractAttacher):
    """
    HandleBasedAttacher implemented common handle (hWnd) based IPC interaction with specified handle through WINAPI
    """
    def __init__(self):
        super(HandleBasedAttacher, self).__init__()
        self.handle = LazyValue(self.locate_handle)

    def locate_handle(self) -> int:
        """
        Locate the simulator handle, used for screenshot capturing and message sending

        :return: The handle of the simulator, if not found, returns 0
        """
        raise NotImplementedError

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        """
        Get the current screenshot of simulator.

        :param width: the width of reshaped screenshot (in pixels), default: window width
        :param height: the height of reshaped screenshot (in pixels), default: window height
        :return: returns a numpy array shapes [h, w, c] which c = 3 in RGB order
        """
        left, top, right, bottom = win32gui.GetWindowRect(self.handle())
        window_height = bottom - top
        window_width = right - left
        handle_dc = win32gui.GetWindowDC(self.handle())
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
        win32gui.ReleaseDC(self.handle(), handle_dc)
        win32gui.DeleteObject(new_bitmap.GetHandle())
        screenshot = np.flip(arr[..., :3], -1)
        if width is None:
            width = window_width
        if height is None:
            height = window_height
        if width != window_width or height != window_width:
            screenshot = image_process.resize(screenshot, width, height)
        return screenshot

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        """
        Send the click event to the simulator.
        Execution order: MOUSE BUTTON DOWN EVENT -> sleep(stay_time) -> MOUSE BUTTON UP EVENT

        :param x: normalized coordinate X, ranges [0, 1), re-scale is required, which depends on the window size
        :param y: normalized coordinate Y, ranges [0, 1), re-scale is required, which depends on the window size
        :param stay_time: the interval between MOUSE BUTTON DOWN and MOUSE BUTTON UP
        :return: None
        """
        logger.debug('Performing click: (%f, %f)' % (x, y))
        handle = self.handle()
        left, top, right, bottom = win32gui.GetWindowRect(handle)
        height = bottom - top
        width = right - left
        x = int(x * width)
        y = int(y * height)
        pos = x | (y << 16)
        # root.info('PostMessage(%d, WM_LBUTTONDOWN, MK_LBUTTON, pos: (%d, %d))' % (handle, x, y))
        win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
        sleep(stay_time)
        # root.info('PostMessage(%d, WM_LBUTTONUP, 0, pos: (%d, %d))' % (handle, x, y))
        win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, 0, pos)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        """
        Send the slide event to the simulator.

        :param p_from: normalized coordinate (X1, Y1) before sliding, ranges [0, 1), re-scale is required,
         which depends on the window size
        :param p_to: normalized coordinate (X2, Y2) after sliding, ranges [0, 1), re-rescale is required,
         which depends on the window size
        :param stay_time_before_move: the interval between MOUSE BUTTON DOWN and MOUSE MOVE (in seconds)
        :param stay_time_move: the duration of MOUSE MOVE loop (in seconds)
        :param stay_time_after_move: the interval between MOUSE MOVE and MOUSE BUTTON UP (in seconds)
        :return: None
        """
        logger.debug('Performing slide: from %s to %s' % (str(p_from), str(p_to)))
        handle = self.handle()
        left, top, right, bottom = win32gui.GetWindowRect(handle)
        height = bottom - top
        width = right - left
        x1, y1 = p_from
        x2, y2 = p_to
        x1 = int(x1 * width)
        y1 = int(y1 * height)
        x2 = int(x2 * width)
        y2 = int(y2 * height)
        begin_pos = x1 | (y1 << 16)
        end_pos = x2 | (y2 << 16)
        # root.info('PostMessage(%d, WM_LBUTTONDOWN, MK_LBUTTON, pos: (%d, %d))' % (handle, x1, y1))
        win32gui.PostMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, begin_pos)
        sleep(stay_time_before_move)
        begin_t = time()
        last_x = x1
        last_y = y1
        while time() - begin_t < stay_time_move:
            norm_t = min(time() - begin_t, stay_time_move) / stay_time_move
            new_x = int(x1 + (x2 - x1) * norm_t)
            new_y = int(y1 + (y2 - y1) * norm_t)
            if last_x != new_x or last_y != new_y:
                pos = new_x | (new_y << 16)
                # root.info('PostMessage(%d, WM_MOUSEMOVE, MK_LBUTTON, pos: (%d, %d))' % (handle, new_x, new_y))
                win32gui.SendMessage(handle, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, pos)
                last_x = new_x
                last_y = new_y
            sleep(0.002)
        sleep(stay_time_after_move)
        # root.info('PostMessage(%d, WM_LBUTTONUP, MK_LBUTTON, pos: (%d, %d))' % (handle, x2, y2))
        win32gui.PostMessage(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, end_pos)
