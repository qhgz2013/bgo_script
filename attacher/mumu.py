from . import AbstractAttacher
import win32gui


class MumuAttacher(AbstractAttacher):
    def __init__(self):
        super(MumuAttacher, self).__init__()

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
        return window_handle
