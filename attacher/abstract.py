import numpy as np
from typing import *
from util import LazyValue
import win32gui
import win32con
import win32ui
from time import sleep, time
import cv2


class AbstractAttacher:
    def __init__(self):
        self.handle = LazyValue(self.locate_handle)
    
    def locate_handle(self) -> int:
        """
        Locate the simulator handle, used for screenshot capturing and message sending
        :return: The handle of the simulator, if not found, returns 0
        """
        raise NotImplementedError()

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
            # noinspection PyUnresolvedReferences
            screenshot = cv2.resize(screenshot, (width, height), interpolation=cv2.INTER_CUBIC)
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
        left, top, right, bottom = win32gui.GetWindowRect(self.handle())
        height = bottom - top
        width = right - left
        x = int(x * width)
        y = int(y * height)
        pos = x | (y << 16)
        win32gui.PostMessage(self.handle(), win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
        sleep(stay_time)
        win32gui.PostMessage(self.handle(), win32con.WM_LBUTTONUP, 0, pos)

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
        left, top, right, bottom = win32gui.GetWindowRect(self.handle())
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
        win32gui.PostMessage(self.handle(), win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, begin_pos)
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
                win32gui.SendMessage(self.handle(), win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, pos)
            sleep(0.002)
        sleep(stay_time_after_move)
        win32gui.PostMessage(self.handle(), win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, end_pos)