import win32gui
import win32ui
import win32con
import numpy as np
from time import sleep, time
from typing import *


def _print_window_detail(handle):
    if handle > 0:
        print('%d: [%s] %s' % (handle, win32gui.GetClassName(handle), win32gui.GetWindowText(handle)))
    else:
        print('0: [Unknown] Unknown')


class MumuSimulatorAttacher:
    def __init__(self):
        print('Finding handle of Mumu simulator window')
        # SPY++:
        # Qt5QWindowIcon, MuMu模拟器 or Game name
        # |- Qt5QWindowIcon, NemuPlayer
        #    |- canvasWin, canvas
        simulator_handle = win32gui.FindWindow('Qt5QWindowIcon', None)
        window_handle = 0
        while simulator_handle > 0:
            _print_window_detail(simulator_handle)
            window_handle = win32gui.FindWindowEx(simulator_handle, 0, 'Qt5QWindowIcon', 'NemuPlayer')
            if window_handle > 0:
                break
            else:
                simulator_handle = win32gui.FindWindowEx(0, simulator_handle, 'Qt5QWindowIcon', None)
        _print_window_detail(window_handle)
        assert window_handle > 0, 'Could not find child handle of Mumu simulator: NemuPlayer'
        # canvas_handle = win32gui.FindWindowEx(window_handle, 0, 'canvasWin', 'canvas')
        # _print_window_detail(canvas_handle)
        # assert canvas_handle > 0, 'Could not find canvas handle of Mumu simulator'
        # print('Done, handle located: %d' % canvas_handle)
        self.handle = window_handle

    def get_screenshot(self):
        left, top, right, bottom = win32gui.GetWindowRect(self.handle)
        height = bottom - top
        width = right - left
        handle_dc = win32gui.GetWindowDC(self.handle)
        new_dc = win32ui.CreateDCFromHandle(handle_dc)
        compat_dc = new_dc.CreateCompatibleDC()

        new_bitmap = win32ui.CreateBitmap()
        new_bitmap.CreateCompatibleBitmap(new_dc, width, height)
        compat_dc.SelectObject(new_bitmap)
        compat_dc.BitBlt((0, 0), (width, height), new_dc, (0, 0), win32con.SRCCOPY)
        # new_bitmap.SaveBitmapFile(compat_dc, 'filename')
        arr = new_bitmap.GetBitmapBits(True)
        arr = np.fromstring(arr, dtype='uint8').reshape([height, width, -1])
        new_dc.DeleteDC()
        compat_dc.DeleteDC()
        win32gui.ReleaseDC(self.handle, handle_dc)
        win32gui.DeleteObject(new_bitmap.GetHandle())
        return np.flip(arr[..., :3], -1)

    def send_click(self, x: float, y: float, stay_time: float = 0.05):
        left, top, right, bottom = win32gui.GetWindowRect(self.handle)
        height = bottom - top
        width = right - left
        x = int(x * width)
        y = int(y * height)
        pos = x | (y << 16)
        win32gui.PostMessage(self.handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
        sleep(stay_time)
        win32gui.PostMessage(self.handle, win32con.WM_LBUTTONUP, 0, pos)

    # noinspection DuplicatedCode
    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        left, top, right, bottom = win32gui.GetWindowRect(self.handle)
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
        win32gui.PostMessage(self.handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, begin_pos)
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
                win32gui.SendMessage(self.handle, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, pos)
            sleep(0.002)
        sleep(stay_time_after_move)
        win32gui.PostMessage(self.handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, end_pos)
