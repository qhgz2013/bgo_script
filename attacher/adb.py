from .abstract import AbstractAttacher
import numpy as np
from typing import *
import sys
import os
import logging
from util import spawn_process_raw, spawn_process
import image_process
import struct

logger = logging.getLogger('bgo_script.attacher')


def _handle_adb_ipc_output(proc_output):
    if proc_output[0] != 0:
        logger.error('Adb process exited with non-zero value: %d' % proc_output[0])
    if len(proc_output[2]):
        logger.error('Adb process error output: %s' % str(proc_output[2]))
    return proc_output[1]


class AdbAttacher(AbstractAttacher):
    """
    AdbAttacher provides interactions to smartphone through ADB (Android Debug Bridge) calls. DEVELOPER MODE, USB
    DEBUGGING (with safety option if it shows in the context) should be turned on
    """
    __warn_func_disabled = False

    def __init__(self, adb_executable: Optional[str] = None, crop_16_9: bool = True):
        self._adb = None
        if adb_executable is not None:
            assert os.path.isfile(adb_executable), 'Adb (Android Debug Bridge) executable not exists'
            self._adb = adb_executable
        else:
            candidate_paths = list(sys.path)
            candidate_paths.extend(os.getenv('PATH').split(os.pathsep))
            for path in candidate_paths:
                candidate_file = os.path.join(path, 'adb.exe')
                if os.path.isfile(candidate_file):
                    self._adb = candidate_file
                    break
            if self._adb is None:
                raise RuntimeError('Could not find adb.exe in PATH, please specify it by parameter')
            logger.info('Found adb.exe in %s' % self._adb)
        spawn_process([self._adb, 'kill-server'])
        spawn_process([self._adb, 'start-server'])
        self._crop_16_9 = False
        self._device_screen_size = self._get_screenshot_internal().shape
        logger.debug('Device resolution: %s' % str(self._device_screen_size[1::-1]))
        self._crop_16_9 = crop_16_9
        w = self._device_screen_size[0] / 9.0 * 16.0
        beg_x = int(round(self._device_screen_size[1] - w) / 2)
        self._16_9_screen_slice_x = slice(beg_x, beg_x + int(round(w)))

    def _translate_normalized_coord(self, x: float, y: float) -> Tuple[int, int]:
        if self._crop_16_9:
            w = self._16_9_screen_slice_x.stop - self._16_9_screen_slice_x.start
            return self._16_9_screen_slice_x.start + int(round(x * w)), int(round(y * self._device_screen_size[0]))
        else:
            return int(round(x * self._device_screen_size[1])), int(round(y * self._device_screen_size[0]))

    def _get_screenshot_internal(self) -> np.ndarray:
        blob = _handle_adb_ipc_output(spawn_process_raw([self._adb, 'exec-out', 'screencap']))
        width, height, pixel_format = struct.unpack('<3I', blob[:12])
        if pixel_format != 1:
            raise ValueError('Invalid screencap output format: Expected RGBA (0x1), but got %d' % pixel_format)
        if len(blob) - 12 != width * height * 4:
            raise ValueError('Invalid RGBA data array: length corrupted')
        img = np.frombuffer(blob[12:], 'uint8').reshape(height, width, 4)
        # In-game detection: for most of mobile devices, condition "height < width" holds true
        if img.shape[0] > img.shape[1]:
            img = np.swapaxes(img, 0, 1)
        # crop to 16:9 if enabled
        if self._crop_16_9:
            img = img[:, self._16_9_screen_slice_x, :]
        return img

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        img = self._get_screenshot_internal()
        width = width or img.shape[1]
        height = height or img.shape[0]
        return image_process.resize(img, width, height)

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        px, py = self._translate_normalized_coord(x, y)
        stdout = _handle_adb_ipc_output(spawn_process('adb shell input touchscreen swipe %d %d %d %d %d' %
                                                      (px, py, px, py, int(round(stay_time*1000)))))
        if len(stdout) > 0:
            logger.debug('Adb output: %s' % stdout)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        p1 = self._translate_normalized_coord(*p_from)
        p2 = self._translate_normalized_coord(*p_to)
        if not self.__warn_func_disabled:
            self.__warn_func_disabled = True
            logger.warning('Param stay_time_before_move and stay_time_after_move is disabled for Adb attacher')
        stdout = _handle_adb_ipc_output(spawn_process(['adb', 'shell', 'input touchscreen swipe %d %d %d %d %d' %
                                                       (p1[0], p1[1], p2[0], p2[1], int(round(stay_time_move*1000)))]))
        if len(stdout) > 0:
            logger.debug('Adb output: %s' % stdout)
