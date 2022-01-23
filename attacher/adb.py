from abc import ABC
from .abstract import AbstractAttacher
import numpy as np
from typing import *
import os
import logging
from util import spawn_process_raw, spawn_process, find_adb_path, AdbShellWrapper, LazyValue, find_path
import image_process
import struct
import threading
from time import sleep, time
import re
from enum import IntEnum
import subprocess

logger = logging.getLogger('bgo_script.attacher')
_cached_device_resolution = None


def _handle_adb_ipc_output(proc_output):
    if proc_output[0] != 0:
        logger.error('Adb process exited with non-zero value: %d' % proc_output[0])
    if len(proc_output[2]):
        logger.error('Adb process error output: %s' % str(proc_output[2]))
    return proc_output[1]


def get_device_resolution(fn: Callable, self: AbstractAttacher) -> Tuple[int, int]:
    global _cached_device_resolution
    if _cached_device_resolution is None:
        shape = fn(self).shape[:2]
        if shape[0] > shape[1]:
            # we only detect the device resolution once (since Screencap solution will cost a lot of time)
            # so make sure it's already in landscape orientation
            raise RuntimeError('Portrait orientation is unsupported (Please change to landscape orientation before '
                               'executing the script)')
        logger.debug('Device resolution: %s', str(shape))
        _cached_device_resolution = shape
    return _cached_device_resolution


class AdbScreenCaptureSolution(AbstractAttacher, ABC):
    def get_resolution(self):
        raise NotImplementedError

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        raise NotImplementedError


class AdbScreenCaptureNativeScreencap(AdbScreenCaptureSolution, ABC):
    def __init__(self, adb_executable: str, **kwargs):
        self._adb = adb_executable
        self._resolution = get_device_resolution(AdbScreenCaptureNativeScreencap.get_screenshot, self)

    def get_resolution(self):
        return self._resolution

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        # sometimes this command will halt, don't know why, so add timeout 5 secs here
        blob = _handle_adb_ipc_output(spawn_process_raw([self._adb, 'exec-out', 'screencap'], timeout=5,
                                                        timed_out_retry=5))
        width, height, pixel_format = struct.unpack('<3I', blob[:12])
        if pixel_format != 1:
            raise ValueError('Invalid screencap output format: Expected RGBA (0x1), but got %d' % pixel_format)
        begin_pos = 12
        unused_bytes = len(blob) - 12 - width * height * 4
        if unused_bytes == 4:
            # in newer android system, screencap will return w, h, f (pixel format), c (color space)
            # src code: https://github.com/aosp-mirror/platform_frameworks_base/blob/master/cmds/screencap/screencap.cpp
            begin_pos = 16
        elif unused_bytes != 0:
            raise ValueError('Invalid RGBA data array: length corrupted')
        img = np.frombuffer(blob[begin_pos:], 'uint8').reshape(height, width, 4)
        return img


class AdbScreenCaptureFFMpegStream(AdbScreenCaptureNativeScreencap, ABC):
    __warned_orientation = False

    def __init__(self, adb_executable: str, ffmpeg_executable: str):
        # whole pipeline:
        # ADB h264 video stream -> ADB stdout -> FFMpeg stdin -> FFMpeg decoder -> FFMpeg stdout -> raw RGB data
        super(AdbScreenCaptureFFMpegStream, self).__init__(adb_executable)
        self._ffmpeg = ffmpeg_executable
        self._active_adb_process = None
        self._last_decoded_frame = None
        self._has_decoded_frame = threading.Event()
        logger.debug('Calling FFMpeg process')
        self._ffmpeg_process = subprocess.Popen([self._ffmpeg, '-probesize', '32', '-f', 'h264', '-i', 'pipe:', '-f',
                                                 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:'], stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        terminator = threading.Thread(target=self._ffmpeg_process_terminator, name='FFMpeg process killer',
                                      daemon=False)
        terminator.start()
        decoder = threading.Thread(target=self._ffmpeg_decode_data_receiver, name='FFMpeg decode data receiver',
                                   daemon=True)
        decoder.start()

    def _ffmpeg_process_terminator(self):
        while threading.main_thread().is_alive():
            sleep(0.1)
        if self._ffmpeg_process.poll() is None:
            logger.info('Main thread exited, terminating FFMpeg process')
            self._ffmpeg_process.terminate()

    def _adb_pipe_forwarder(self):
        while self._active_adb_process.poll() is None:
            data = self._active_adb_process.stdout.read(4096)
            while len(data) > 0:
                self._ffmpeg_process.stdin.write(data)
                data = self._active_adb_process.stdout.read(4096)
        self._active_adb_process = None
        logger.debug('Adb screen record process exited (reached maximum record time limit)')

    def _ffmpeg_decode_data_receiver(self):
        resolution = self.get_resolution() + (3,)
        bytes_required = 1
        for dim in resolution:
            bytes_required *= dim
        while True:
            data = self._ffmpeg_process.stdout.read(bytes_required)
            if len(data) == 0:
                return
            img = np.frombuffer(data, dtype=np.uint8).reshape(resolution)
            self._last_decoded_frame = img
            self._has_decoded_frame.set()

    def _activate_adb_screen_record(self):
        if self._active_adb_process is None:
            logger.debug('Calling Adb screen record')
            self._has_decoded_frame.clear()
            self._active_adb_process = subprocess.Popen([self._adb, 'exec-out', 'screenrecord', '--output-format=h264',
                                                         '--bit-rate', '4000000', '-'], stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            pipe_forwarder = threading.Thread(target=self._adb_pipe_forwarder, daemon=True,
                                              name='Adb screen record pipe forwarder')
            pipe_forwarder.start()

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        self._has_decoded_frame.clear()
        while self._active_adb_process is None or not self._has_decoded_frame.wait(3):
            self._activate_adb_screen_record()
        img = self._last_decoded_frame
        return image_process.resize(img, width or img.shape[1], height or img.shape[0])


class AdbAdaptiveScreenCapture(AdbScreenCaptureSolution, ABC):
    def __init__(self, adb_path: str, **kwargs):
        ffmpeg_path = find_path('ffmpeg.exe')
        disable_ffmpeg = kwargs.pop('disable_ffmpeg', False)
        if disable_ffmpeg or ffmpeg_path is None or not os.path.isfile(ffmpeg_path):
            self._forwarder = AdbScreenCaptureNativeScreencap(adb_path)
        else:
            self._forwarder = AdbScreenCaptureFFMpegStream(adb_path, ffmpeg_path)

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        return self._forwarder.get_screenshot(width, height)

    def get_resolution(self):
        return self._forwarder.get_resolution()


class AdbAttacher(AbstractAttacher):
    """
    AdbAttacher provides interactions to smartphone through ADB (Android Debug Bridge) calls. DEVELOPER MODE, USB
    DEBUGGING (with safety option if it shows in the context) should be turned on
    """
    __warn_func_disabled = False
    _screen_orientation_ptn = re.compile(r'\s*SurfaceOrientation:\s*(\d+)')

    def __init__(self, adb_executable: Optional[str] = None, disable_ffmpeg: bool = False):
        self._adb = None
        if adb_executable is not None:
            assert os.path.isfile(adb_executable), 'Adb (Android Debug Bridge) executable not exists'
            self._adb = adb_executable
        else:
            self._adb = find_adb_path()
            if self._adb is None:
                raise RuntimeError('Could not find adb.exe in PATH, please specify it by parameter')
            logger.info('Found adb.exe in %s' % self._adb)
        spawn_process([self._adb, 'start-server'])
        self._hook_after_sever_started()
        self._adb_shell = AdbShellWrapper(self._adb)
        self._screen_cap_adapter = AdbAdaptiveScreenCapture(self._adb, disable_ffmpeg=disable_ffmpeg)
        thd = threading.Thread(target=self._shutdown_adb_server, daemon=False, name='Adb server shutdown thread')
        thd.start()
        self._sample_screenshot = None
        self._device_screen_size = self._screen_cap_adapter.get_resolution()
        self._16_9_screen_slice_x = LazyValue(self._get_screen_slice)
        self._orientation = LazyValue(self._get_screen_orientation)

    def _hook_after_sever_started(self):
        pass

    def _shutdown_adb_server(self):
        while threading.main_thread().is_alive():
            sleep(0.2)
        logger.info('Main thread exited, terminate adb server process')
        spawn_process_raw([self._adb, 'kill-server'])

    def _translate_normalized_coord(self, x: float, y: float) -> Tuple[int, int]:
        screen_slice_x = self._16_9_screen_slice_x()
        w = screen_slice_x.stop - screen_slice_x.start
        return screen_slice_x.start + int(round(x * w)), int(round(y * min(*self._device_screen_size)))

    def _get_screen_slice(self):
        x, y = self._device_screen_size
        w0, h = max(x, y), min(x, y)
        w = h / 9.0 * 16.0
        beg_x = int(round(w0 - w) / 2)
        return slice(beg_x, beg_x + int(round(w)))

    def _do_interact_no_stderr(self, cmd: Union[str, List[Any]]):
        ret_code, stdout, stderr = self._adb_shell.interact(cmd)
        if ret_code != 0:
            logger.error('Adb shell command returned exit code: %d', ret_code)
        if len(stderr) > 0:
            logger.error('Adb shell response error message: %s', stderr)
        return stdout

    def _get_screen_orientation(self):
        # todo: [prior = low] adaptive update screen orientation
        stdout = self._do_interact_no_stderr('dumpsys input|grep SurfaceOrientation').rstrip()
        match = re.match(self._screen_orientation_ptn, stdout)
        if match is None:
            logger.warning('Failed to get screen orientation: %s, assumes ROTATION_90', stdout)
            return 1
        return int(match.group(1))

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        img = self._screen_cap_adapter.get_screenshot()
        if img.shape[0] > img.shape[1]:
            img = np.swapaxes(img, 0, 1)
        img = img[:, self._16_9_screen_slice_x(), :]
        width = width or img.shape[1]
        height = height or img.shape[0]
        return image_process.resize(img, width, height)

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        px, py = self._translate_normalized_coord(x, y)
        stdout = self._do_interact_no_stderr('input touchscreen swipe %d %d %d %d %d' %
                                             (px, py, px, py, int(round(stay_time*1000))))
        if len(stdout) > 0:
            logger.debug('Adb output: %s' % stdout)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        p1 = self._translate_normalized_coord(*p_from)
        p2 = self._translate_normalized_coord(*p_to)
        if not self.__warn_func_disabled:
            self.__warn_func_disabled = True
            logger.warning('Param stay_time_before_move and stay_time_after_move is disabled for Adb attacher')
        stdout = self._do_interact_no_stderr('input touchscreen swipe %d %d %d %d %d' %
                                             (p1[0], p1[1], p2[0], p2[1], int(round(stay_time_move*1000))))
        if len(stdout) > 0:
            logger.debug('Adb output: %s' % stdout)


class EventType(IntEnum):
    EV_SYN = 0
    EV_ABS = 3
    EV_KEY = 1
    EV_SW = 5
    EV_FF = 0x15


class EventID(IntEnum):
    ABS_MT_TRACKING_ID = 0x39
    BTN_TOUCH = 0x14a
    ABS_MT_POSITION_X = 0x35
    ABS_MT_POSITION_Y = 0x36
    SYN_REPORT = 0


# TODO [PRIOR middle]: implement screen streaming based adb attacher
class AdbAttacherRootEnhanced(AdbAttacher):
    _landscape_rotation_ptn = re.compile(r'\s*mLandscapeRotation=(?:(\d+)|(?:ROTATION_(\d+)))')

    def __init__(self, adb_executable: Optional[str] = None, disable_ffmpeg: bool = False):
        super().__init__(adb_executable, disable_ffmpeg)
        self._root_available = LazyValue(self._get_root)
        self._input_device = LazyValue(self._get_input_device)
        self._landscape_rotation = LazyValue(self._get_device_landscape_rotation)

    def _get_root(self):
        if self._do_interact_no_stderr('whoami').rstrip() == 'root':
            return True
        self._adb_shell.interact('su', wait=False)
        # some simulator will hang up if su is not completely executed and new command goes to stdin, so wait 1 sec here
        sleep(1)
        is_root = self._do_interact_no_stderr('whoami').rstrip() == 'root'
        if not is_root:
            logger.warning('Root is required for AdbAttacherRootEnhanced, fall back to non-root solution')
        return is_root

    def _get_device_landscape_rotation(self):
        rotation = self._do_interact_no_stderr('dumpsys window|grep mLandscapeRotation').rstrip()
        match = re.search(self._landscape_rotation_ptn, rotation)
        if match is None:
            logger.warning('Failed to get default landscape rotation, assumes default: landscape')
            return 1
        if match.group(1) is not None:
            return int(match.group(1))
        elif match.group(2) is not None:
            return int(match.group(2)) // 90
        logger.warning('Failed to get default landscape rotation, assumes default: landscape')
        return 1

    def _translate_normalized_coord(self, x: float, y: float) -> Tuple[int, int]:
        x, y = AdbAttacher._translate_normalized_coord(self, x, y)
        if self._root_available():
            h, w = self._device_screen_size
            if self._landscape_rotation() & 1:
                w, h = h, w  # change to portrait
            d = {0: (x, y), 1: (w-y, x), 2: (w-x, h-y), 3: (y, h-x)}
            orientation = self._orientation()
            return d[orientation]
        return x, y

    def _get_input_device(self):
        target_event_type = {
            'ABS': {EventID.ABS_MT_POSITION_X.value, EventID.ABS_MT_POSITION_Y.value},
            'KEY': {EventID.BTN_TOUCH.value}
        }
        ret_code, stdout, stderr = self._adb_shell.interact(['getevent', '-p'])
        if ret_code != 0:
            raise RuntimeError('Adb getevent failed with exit code %d' % ret_code)
        if len(stderr) > 0:
            logger.warning('Unexpected error from getevent: %s' % stderr)
        add_device_line = re.compile(r'add\sdevice\s\d+:\s(/dev/input/event\d+)')
        device_prop_line = re.compile(r'\s{2}(\w+(?:\s\w+)*):\s?')
        feature_line = re.compile(r'\s+(?:([A-Z]+)\s+\([0-9a-f]{4}\):)?((?:\s+[0-9a-f]{4})+)')
        device = {}
        device_path = ''
        current_prop = ''
        current_event_type = ''
        for line in stdout.split('\n'):
            if len(line) == 0:
                continue
            add_device_match = re.match(add_device_line, line)
            if add_device_match is not None:
                device_path = add_device_match.group(1)
                device[device_path] = 0
                continue
            device_prop_match = re.match(device_prop_line, line)
            if device_prop_match is not None:
                current_prop = device_prop_match.group(1)
                continue
            if current_prop == 'events':
                feature_match = re.search(feature_line, line)
                if feature_match.group(1) is not None:
                    current_event_type = feature_match.group(1)
                for supported_event_id in {x for x in feature_match.group(2).split(' ') if len(x) > 0}:
                    event_id = int(supported_event_id, 16)
                    if event_id in target_event_type.get(current_event_type, {}):
                        device[device_path] = (device[device_path] << 1) | 1
        sorted_dict = sorted(device.items(), key=lambda kv: kv[1], reverse=True)
        best_device = sorted_dict[0][0]
        logger.info('Use input device: %s', best_device)
        return best_device

    def _send_event_touch_down(self, px: int, py: int):
        device = self._input_device()
        args = [
            f'sendevent {device} {EventType.EV_KEY.value} {EventID.BTN_TOUCH.value} 1',
            f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_X.value} {px}',
            f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_Y.value} {py}',
            f'sendevent {device} {EventType.EV_SYN.value} {EventID.SYN_REPORT.value} 0'
        ]
        self._hook_send_event_touch_down(device, args, px, py)
        self._do_interact_no_stderr(' && '.join(args))

    def _hook_send_event_touch_down(self, device: str, args: List[str], px: int, py: int):
        pass

    def _send_event_touch_up(self):
        device = self._input_device()
        args = [
            f'sendevent {device} {EventType.EV_KEY.value} {EventID.BTN_TOUCH.value} 0',
            f'sendevent {device} {EventType.EV_SYN.value} {EventID.SYN_REPORT.value} 0'
        ]
        self._hook_send_event_touch_up(device, args)
        self._do_interact_no_stderr(' && '.join(args))

    def _hook_send_event_touch_up(self, device: str, args: List[str]):
        pass

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        if self._root_available():
            px, py = self._translate_normalized_coord(x, y)
            self._send_event_touch_down(px, py)
            sleep(stay_time)
            self._send_event_touch_up()
        else:
            AdbAttacher.send_click(self, x, y, stay_time)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        x1, y1 = self._translate_normalized_coord(*p_from)
        x2, y2 = self._translate_normalized_coord(*p_to)
        self._send_event_touch_down(x1, y1)
        sleep(stay_time_before_move)
        begin_t = time()
        last_x = x1
        last_y = y1
        device = self._input_device()
        while time() - begin_t < stay_time_move:
            norm_t = min(time() - begin_t, stay_time_move) / stay_time_move
            new_x = int(x1 + (x2 - x1) * norm_t)
            new_y = int(y1 + (y2 - y1) * norm_t)
            send_event_args = []
            if last_x != new_x:
                send_event_args.append(f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_X.value} '
                                       f'{new_x}')
                last_x = new_x
            if last_y != new_y:
                send_event_args.append(f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_Y.value} '
                                       f'{new_y}')
                last_y = new_y
            if len(send_event_args) > 0:
                send_event_args.append(f'sendevent {device} {EventType.EV_SYN.value} {EventID.SYN_REPORT.value} 0')
                self._do_interact_no_stderr(' && '.join(send_event_args))
            sleep(0.002)
        send_event_args = []
        if last_x != x2:
            send_event_args.append(f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_X.value} '
                                   f'{x2}')
        if last_y != y2:
            send_event_args.append(f'sendevent {device} {EventType.EV_ABS.value} {EventID.ABS_MT_POSITION_Y.value} '
                                   f'{y2}')
        if len(send_event_args) > 0:
            send_event_args.append(f'sendevent {device} {EventType.EV_SYN.value} {EventID.SYN_REPORT.value} 0')
            self._do_interact_no_stderr(' && '.join(send_event_args))
        sleep(stay_time_after_move)
        self._send_event_touch_up()
