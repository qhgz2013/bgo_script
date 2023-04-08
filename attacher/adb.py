# attacher.adb
# Provides interactions (e.g., capturing screenshot, sending clicks and slides) between script and ADB-capable devices.
# Ver 1.1
# Changelog:
# 1.1: Added multiprocessing based ADBScreenrecorderCapturer
# 1.0: Re-implement ADB attacher module (screenshot capture and interactions are split now).
import re
import math
from .adb_util import spawn, ADBServer, ADBShell
from typing import *
from typing import IO
from .base import ScreenCapturer, AttacherBase, AttacherRegistry, CapturerRegistry
import numpy as np
from enum import IntEnum
from collections import Counter
from logging import getLogger
from functools import partial
import struct
from time import sleep, time
from util import spawn_process_raw, LazyValue, register_handler
import threading
import subprocess
from ._ffmpeg_util import ADBScreenrecordFFMpegDecoder
import multiprocessing as mp
from basic_class import PointF, Resolution
import image_process

__all__ = ['ADBScreenCapturer', 'ADBScreenrecordCapturer', 'ADBAttacher', 'ADBRootAttacher', 'EventID', 'EventType',
           'ADBScreenrecordCapturerThreaded', "ADBScreenrecordCapturerMP"]

# constants
_WM_SOLUTION_PATTERN = re.compile(r'(?P<width>\d+)x(?P<height>\d+)$')
_LANDSCAPE_ORIENTATION_PATTERN = re.compile(r'mLandscapeRotation=(?:(?P<val>\d+)|(?P<var>ROTATION_(\d+)))')
_SURFACE_ORIENTATION_PATTERN = re.compile(r'SurfaceOrientation:\s*(\d+)')
_SURFACE_ORIENTATION_PATTERN_NEW = re.compile(r'orientation=\s*(\d+)')
_NAN = float('nan')
_PIPE = subprocess.PIPE
# variables (user-defined)
logger = getLogger('bgo_script.attacher.adb')
_PROCESS_SPEED_CHECK_INTERVAL = 5  # the duration and interval (in seconds) to check the process speed of FFMpeg output
_FFMPEG_PROCESS_FPS = 10  # Video FPS, passed to FFMpeg wrapper
_WARN_PROCESS_SPEED_THRESHOLD = 0.8  # if process speed is less than this value, a warning will be logged per interval
# variables (auto-controlled)
_warned_screencap_arg = False


class SurfaceOrientation(IntEnum):
    """Android surface orientation definitions, same as ``android.view.surface.Surface``."""
    ROTATION_0 = 0
    ROTATION_90 = 1
    ROTATION_180 = 2
    ROTATION_270 = 3


class ADBScreencapTransferFormat(IntEnum):
    Raw = 1
    PNG = 2


def get_landscape_orientation(shell: ADBShell) -> SurfaceOrientation:
    """Get the device orientation for landscape mode."""
    output = spawn('dumpsys window|grep mLandscapeRotation', spawn_fn=shell.interact, raise_exc=True)
    match = re.search(_LANDSCAPE_ORIENTATION_PATTERN, output.rstrip())
    if match is None:
        raise ValueError(f'Could not get landscape orientation: invalid output "{output}"')
    if match.group('val') is not None:
        return SurfaceOrientation(int(match.group('val')))
    return getattr(SurfaceOrientation, match.group('var'))


def _gen_landscape_orientation(output: str, pattern: re.Pattern) -> SurfaceOrientation:
    def _gen_internal():
        for line in output.split('\n'):
            line = line.rstrip()
            if len(line) == 0:
                continue
            match = re.search(pattern, line)
            if match is None:
                # raise ValueError(f'Could not get landscape orientation: invalid output {line}')
                continue
            yield SurfaceOrientation(int(match.group(1)))
    # since the output maybe multi-lined (from several device), we need to further determine if they are the same
    values = Counter(_gen_internal())
    if len(values) == 0:
        raise ValueError('No orientation detected')
    if len(values) > 1:
        raise ValueError('Multiple orientation detected, it is not supported')
    return next(iter(values.keys()))  # returns the unique value


def get_surface_orientation(shell: ADBShell) -> SurfaceOrientation:
    """Get the current device orientation (aka surface orientation)."""
    # not work for android 13 (at least my new device is not working)
    ret_val, output, _ = shell.interact('dumpsys input|grep SurfaceOrientation')
    if ret_val == 0:
        return _gen_landscape_orientation(output, _SURFACE_ORIENTATION_PATTERN)
    ret_val, output, _ = shell.interact('dumpsys input|grep orientation')
    if ret_val == 0:
        return _gen_landscape_orientation(output, _SURFACE_ORIENTATION_PATTERN_NEW)
    raise ValueError('Could not get device surface orientation')


# NOTE: old version of ADB will incur malformed output even exec-out is used
@register_handler(CapturerRegistry, 'adb_native')
class ADBScreenCapturer(ScreenCapturer):
    def __init__(self, adb_server: Optional[ADBServer] = None, device: Optional[Union[int, str]] = None,
                 transfer_format: ADBScreencapTransferFormat = ADBScreencapTransferFormat.Raw):
        """Initiate a screen capturer using builtin ADB ``screencap`` command. The screenshot will be rotated to
        landscape orientation adaptively.

        :param adb_server: ADB server.
        :param device: Specify which device to be captured (device name or index), leave None to use default device.
        :param transfer_format: The format of the screenshot.
        """
        super(ADBScreenCapturer, self).__init__()
        self._adb_server = adb_server or ADBServer()
        self._adb_shell = self._adb_server.get_shell(device)
        self._device = self._adb_shell.target_device
        self._device_solution = LazyValue(self._get_solution_impl)
        self._landscape_orientation = LazyValue(self._get_landscape_orientation)
        self._terminated = False
        self._transfer_format = transfer_format

    def _get_solution_native_impl(self) -> Resolution:
        output = spawn('wm size', spawn_fn=self._adb_shell.interact, raise_exc=True)
        match = re.search(_WM_SOLUTION_PATTERN, output)
        if match is None:
            raise RuntimeError(f'Could not match resolution from output "{output}"')
        h, w = int(match.group('height')), int(match.group('width'))
        return Resolution(h, w)

    def _get_landscape_orientation(self) -> SurfaceOrientation:
        try:
            return get_landscape_orientation(self._adb_shell)
        except Exception as ex:
            logger.warning(f'Failed to get landscape orientation: {ex!r}')
            # when failed to get landscape orientation, we assume the condition "width > height" still holds true
            solution = self._get_solution_native_impl()
            if solution.width > solution.height:
                return SurfaceOrientation.ROTATION_0
            else:
                return SurfaceOrientation.ROTATION_90

    def _get_solution_impl(self) -> Resolution:
        # always returns the landscape solution here
        solution = self._get_solution_native_impl()
        if (self._landscape_orientation() & 1) == 1:
            # setting landscape orientation needs to rotate -/+ 90 deg
            return Resolution(solution.width, solution.height)
        return solution

    def get_resolution(self) -> Resolution:
        if not self._adb_shell.is_alive():
            raise RuntimeError('ADB shell process is gone')
        return self._device_solution()

    def _get_screenshot_impl_raw(self) -> np.ndarray:
        # sometimes this command will halt, don't know why, so add timeout 5 secs here
        func = partial(spawn_process_raw, timeout=5., timed_out_retry=5)
        blob = spawn(self._adb_server.adb_executable, 'exec-out', 'screencap', spawn_fn=func)
        width, height, pixel_format = struct.unpack('<3I', blob[:12])
        if pixel_format != 1:
            raise ValueError(f'Invalid screencap output format: Expected RGBA (0x1), but got {pixel_format:#x}')
        begin_pos = 12
        unused_bytes = len(blob) - 12 - width * height * 4
        if unused_bytes == 4:
            # in newer android system, screencap will return w, h, f (pixel format), c (color space)
            # src code: https://github.com/aosp-mirror/platform_frameworks_base/blob/master/cmds/screencap/screencap.cpp
            begin_pos = 16
        elif unused_bytes != 0:
            raise ValueError('Invalid RGBA data array: length corrupted, '
                             'check your device, connection cable and ADB version!')
        img = np.frombuffer(blob[begin_pos:], 'uint8').reshape((height, width, 4))
        return img

    def _get_screenshot_impl_png(self) -> np.ndarray:
        func = partial(spawn_process_raw, timeout=5., timed_out_retry=5)
        blob = spawn(self._adb_server.adb_executable, 'exec-out', 'screencap', '-p', spawn_fn=func)
        try:
            return image_process.imdecode(blob)
        except Exception as e:
            raise RuntimeError(f'Failed to decode PNG image: {e!r}, '
                               f'check your device, connection cable and ADB version!')

    def _get_screenshot_impl(self) -> np.ndarray:
        if self._transfer_format == ADBScreencapTransferFormat.Raw:
            return self._get_screenshot_impl_raw()
        else:
            return self._get_screenshot_impl_png()

    def get_screenshot(self) -> np.ndarray:
        # always returns the landscape-orientated screenshot
        if not self._adb_shell.is_alive():
            raise RuntimeError('ADB shell process is gone')
        while True:
            try:
                # make sure the orientation does not change during capturing the screen
                orientation_before = get_surface_orientation(self._adb_shell)
                screenshot = self._get_screenshot_impl()
                orientation_after = get_surface_orientation(self._adb_shell)
                if orientation_after != orientation_before:
                    # if orientation changed, retry after 0.2s
                    sleep(0.2)
                    continue
                landscape_orientation = self._landscape_orientation()
                # to landscape orientation
                rotation = (landscape_orientation - orientation_after) % 4
                # screencap treated ROTATION_0 and ROTATION_180 as same, so as ROTATION_90 and ROTATION_270
                # if rotation & 2:
                #     screenshot = screenshot[::-1, ::-1, :]
                if rotation & 1:
                    screenshot = np.swapaxes(screenshot, 0, 1)[::-1, :, :]
                return np.ascontiguousarray(screenshot)
            except Exception as ex:
                logger.warning(f'Failed to get orientation-independent screenshot, fall back to default mode: '
                               f'exception "{ex!r}"')
                screenshot = self._get_screenshot_impl()
                if screenshot.shape[0] > screenshot.shape[1]:
                    # rotate 90 deg, ensure x-axis is the longest
                    return np.ascontiguousarray(np.swapaxes(screenshot, 0, 1)[::-1, :, :])

    def __repr__(self):
        if self._device is None:
            return f'<{self.__class__.__name__} for {self._adb_server!r}>'
        return f'<{self.__class__.__name__} for {self._adb_server!r} (device {self._device})>'

    def kill(self):
        """Terminate the underlying ADB shell process."""
        if not self._terminated:
            self._terminated = True
            self._adb_shell.kill()

    @property
    def transfer_format(self) -> ADBScreencapTransferFormat:
        return self._transfer_format


# adb exec-out screenrecord --size wxh --bit-rate bitrate --time-limit secs --output-format=h264 -
# performance hint: DO NOT USE "raw-frames" as output format, it is extremely slow
class ADBScreenrecordCapturerThreaded(ADBScreenCapturer):

    def __init__(self, adb_server: Optional[ADBServer] = None, bitrate: Optional[int] = None,
                 time_limit: Optional[int] = None, resolution: Optional[Resolution] = None,
                 device: Optional[str] = None, ffmpeg_executable_path: Optional[str] = None):
        """Instantiating a screen capturer via ADB screenrecord. Compared with screencap, this solution has low latency
        with more resource usage. If the video decoding speed or process speed cannot keep up, use the screencap
        implementation.

        :param adb_server: Instance of ADB server.
        :param bitrate: The bitrate of video stream, in bit-per-second (bps) format, default value: 4000000 (4Mbps).
        :param time_limit: The time limitation of screen record, in seconds, default and maximum value: 180 (3 minutes).
            It is impossible to set it to infinite since it is hard-coded in Android framework. The workaround is to
            restart recording after time limit exceeded to make it "pseudo infinite".
        :param resolution: The resolution of video output, leave None to use native device solution.
        :param device: Specify which device should be connected.
        :param ffmpeg_executable_path: Path of FFMpeg executable file, leave None to search in PATH variable.
        """
        super(ADBScreenrecordCapturerThreaded, self).__init__(adb_server, device)

        cmds = [self._adb_server.adb_executable]
        if device is not None:
            if isinstance(device, int):
                device = self._adb_server.list_devices()[device]
            cmds.extend(['-s', device])
        cmds.extend(['exec-out', 'screenrecord'])
        if resolution is not None:
            cmds.extend(['--size', f'{resolution.width}x{resolution.height}'])
        self._resolution = resolution
        if bitrate is not None:
            cmds.extend(['--bit-rate', str(bitrate)])
        if time_limit is not None:
            cmds.extend(['--time-limit', str(time_limit)])
        cmds.extend(['--output-format=h264', '-'])
        self._screenrecord_spawn_args = cmds
        self._screenrecord_proc = None
        self._ffmpeg_executable_path = ffmpeg_executable_path
        self._restarter = threading.Thread(target=self._tle_restarter, daemon=False,
                                           name='ADBScreenRecordRestarterDaemon')
        self._frame = None  # stores the first decoded frame after frame_request being set
        self._frame_request = threading.Event()
        self._frame_response = threading.Event()
        self._started = False

    def _handle_decoder_output(self, decode_stream: IO[bytes]):
        solution = self._resolution or self._get_solution_native_impl()
        expected_buffer_size = solution.width * solution.height * 3  # RGB format, raw stream
        frame_cnt = 0
        first_frame_time = 0
        while True:
            bytes_read = decode_stream.read(expected_buffer_size)
            if len(bytes_read) == 0:
                break  # got nothing, possibly the process is terminated
            if len(bytes_read) != expected_buffer_size:
                # in this case, shall we restart the process?
                logger.warning(f'Expected to read {expected_buffer_size} bytes from decoder output, '
                               f'but got {len(bytes_read)} bytes, terminating ADB screenrecord process')
                self._screenrecord_proc.terminate()
                break
            frame = np.frombuffer(bytes_read, dtype=np.uint8).reshape((solution.height, solution.width, 3))
            # performance tracking
            if frame_cnt == 0:
                first_frame_time = time()
            dt = time() - first_frame_time
            if dt > _PROCESS_SPEED_CHECK_INTERVAL:
                expected_frame_decoded = _PROCESS_SPEED_CHECK_INTERVAL * _FFMPEG_PROCESS_FPS
                if frame_cnt / expected_frame_decoded < _WARN_PROCESS_SPEED_THRESHOLD:
                    logger.warning(f'{self.__class__.__name__} cannot keep up with FFMpeg output, expected to process '
                                   f'{expected_frame_decoded} frames / {_PROCESS_SPEED_CHECK_INTERVAL} second(s), but '
                                   f'only processed {frame_cnt} frames.')
                # reset counter
                frame_cnt = 0
                first_frame_time = time()
            frame_cnt += 1
            # output
            if self._frame_request.is_set():
                self._frame = frame
                self._frame_request.clear()
                self._frame_response.set()

    def _restart_screenrecord(self):
        logger.debug('Starting ADB screenrecord process')
        self._screenrecord_proc = subprocess.Popen(self._screenrecord_spawn_args, stdout=_PIPE, stderr=_PIPE, bufsize=0)
        logger.debug(f'Started as PID {self._screenrecord_proc.pid}')
        # ffmpeg also needs to be restarted, otherwise a decode error will be logged and cause lagging
        logger.debug('Starting FFMpeg decoder')
        decoder = ADBScreenrecordFFMpegDecoder(self._screenrecord_proc.stdout, self._ffmpeg_executable_path,
                                               fps=_FFMPEG_PROCESS_FPS)
        logger.debug(f'Started as PID {decoder.ffmpeg_process.pid}')
        handler = threading.Thread(target=self._handle_decoder_output, daemon=True, name='FFMpegOutputHandler',
                                   args=(decoder,))
        handler.start()

    def _tle_restarter(self):
        # restart adb screen record once time limit exceeded
        while threading.main_thread().is_alive():
            if self._screenrecord_proc is None or self._screenrecord_proc.poll() is not None:
                self._restart_screenrecord()
            try:
                self._screenrecord_proc.wait(0.5)
                continue
            except subprocess.TimeoutExpired:
                pass
        if self._screenrecord_proc.poll() is not None:
            logger.info('Shutting down ADB screenrecord process')
            self._screenrecord_proc.terminate()

    def _start_daemon(self):
        if not self._started:
            self._restarter.start()
            self._started = True

    def _get_screenshot_impl(self) -> np.ndarray:
        self._start_daemon()
        self._frame_request.set()
        self._frame_response.wait()
        self._frame_response.clear()
        frame = self._frame
        self._frame = None
        return frame


# multiprocessing solution
@register_handler(CapturerRegistry, 'adb')
class ADBScreenrecordCapturerMP(ADBScreenCapturer):
    def __init__(self, adb_server: Optional[ADBServer] = None, bitrate: Optional[int] = None,
                 time_limit: Optional[int] = None, resolution: Optional[Resolution] = None,
                 device: Optional[str] = None, ffmpeg_executable_path: Optional[str] = None):
        """Instantiating a screen capturer via ADB screenrecord. Compared with screencap, this solution has low latency
        with more resource usage. If the video decoding speed or process speed cannot keep up, use the screencap
        implementation.

        :param adb_server: Instance of ADB server.
        :param bitrate: The bitrate of video stream, in bit-per-second (bps) format, default value: 4000000 (4Mbps).
        :param time_limit: The time limitation of screen record, in seconds, default and maximum value: 180 (3 minutes).
            It is impossible to set it to infinite since it is hard-coded in Android framework. The workaround is to
            restart recording after time limit exceeded to make it "pseudo infinite".
        :param resolution: The solution of video output, leave None to use native device solution.
        :param device: Specify which device should be connected.
        :param ffmpeg_executable_path: Path of FFMpeg executable file, leave None to search in PATH variable.
        """
        ScreenCapturer.__init__(self)
        self._args = (adb_server, bitrate, time_limit, resolution, device, ffmpeg_executable_path)
        self._event_queue = mp.SimpleQueue()
        self._sig_req = mp.Event()
        self._sig_resp = mp.Event()
        self._proc = mp.Process(target=self._run, args=(self._args, self._event_queue, self._sig_req, self._sig_resp))
        self._proc.start()
        self._mutex = threading.RLock()

    # only pickle required variables
    @staticmethod
    def _run(args, event_queue, sig_req, sig_resp):
        # hook logging for child process
        try:
            import _logging_config
            _logging_config.bootstrap()
        except ImportError:
            _logging_config = None

        instance = ADBScreenrecordCapturerThreaded(*args)
        while True:
            sig_req.wait()
            sig_req.clear()
            req = event_queue.get()
            if req == 'terminate':
                instance.kill()
                sig_resp.set()
                break
            elif req == 'resolution':
                sig_resp.set()
                event_queue.put(instance.get_resolution())
            elif req == 'screenshot':
                sig_resp.set()
                event_queue.put(instance.get_screenshot())
            else:
                logger.warning(f'Unknown command: {req}')

    def _send_request(self, name: str, retrieve_value: bool = True):
        with self._mutex:
            self._event_queue.put(name)
            self._sig_req.set()
            self._sig_resp.wait()
            self._sig_resp.clear()
            if retrieve_value:
                return self._event_queue.get()

    def get_resolution(self) -> Resolution:
        return self._send_request('resolution')

    def get_screenshot(self) -> np.ndarray:
        return self._send_request('screenshot')

    def kill(self):
        self._send_request('terminate', retrieve_value=False)


# backward naming compatibility, use multiprocessing solution here
ADBScreenrecordCapturer = ADBScreenrecordCapturerMP


@register_handler(AttacherRegistry, 'adb')
class ADBAttacher(AttacherBase):
    def __init__(self, adb_server: Optional[ADBServer] = None, device: Optional[str] = None):
        """An ADB-based attacher. To enable automation, please check the USB debugging in developer setting is turned
        on.

        :param adb_server: ADB server.
        :param device: Specify which device to be controlled.
        """
        self._adb_server = adb_server or ADBServer()
        self._adb_shell = self._adb_server.get_shell(device)
        self._device = self._adb_shell.target_device
        # since all interactions use a normalized coordination within [0, 1], we need to obtain the device resolution
        # first
        cap = ADBScreenCapturer(self._adb_server, self._device)
        self._solution = cap.get_resolution()
        cap.kill()
        del cap

    @property
    def input_solution(self) -> Resolution:
        """Returns the solution of input space (in pixels)."""
        return self._solution

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        """Send click event to a point ``(x, y)``, where ``x`` and ``y`` are pixel coordinates where the coordinates at
        left-top corner are zeros. ``x`` should be ``[0, width)`` and ``y`` should be ``[0, height)``.

        :param x: The normalized coordinate x.
        :param y: The normalized coordinate y.
        :param stay_time: Time duration (in seconds) between pressing and releasing.
        """
        # input touchscreen swipe <x> <y> <x> <y> <t> (x, y: px, t: ms)
        # note: <x> and <y> are orientation-related. <x> for <width> axis and <y> for <height> axis
        px, py = int(round(self.input_solution.width * x)), int(round(self.input_solution.height * y))
        t = int(round(stay_time * 1000))
        spawn(f'input touchscreen swipe {px} {py} {px} {py} {t}', spawn_fn=self._adb_shell.interact, raise_exc=True)

    def send_slide(self, p_from: PointF, p_to: PointF, stay_time_before_move: float = _NAN, stay_time_move: float = 2.0,
                   stay_time_after_move: float = _NAN):
        """Send slide event from point ``p_from`` to ``p_to``.

        :param p_from: A normalized point specifying where the slice begins
        :param p_to: A normalized point specifying  where the slice ends
        :param stay_time_before_move: The duration between pressing and the beginning of sliding (unavailable for
            current implementation, keep it NAN).
        :param stay_time_move: The duration of sliding (in seconds).
        :param stay_time_after_move: The duration between the ending of sliding and releasing (unavailable for current
            implementation, keep it NAN).
        """
        # input touchscreen swipe <x1> <y1> <x2> <y2> <t>, similar to the above method
        # noinspection DuplicatedCode
        x1 = int(round(self.input_solution.width * p_from.x))
        y1 = int(round(self.input_solution.height * p_from.y))
        x2 = int(round(self.input_solution.width * p_to.x))
        y2 = int(round(self.input_solution.height * p_to.y))
        t = int(round(stay_time_move * 1000))
        global _warned_screencap_arg
        if (not math.isnan(stay_time_before_move) or not math.isnan(stay_time_after_move)) \
                and not _warned_screencap_arg:
            logger.warning(f'Parameter "stay_time_before_move" and "stay_time_after_move" is disabled for method'
                           f' {self.send_slide!r}. This message will be logged once.')
            _warned_screencap_arg = True
        spawn(f'input touchscreen swipe {x1} {y1} {x2} {y2} {t}', spawn_fn=self._adb_shell.interact, raise_exc=True)


# Some constants for "sendevent" command
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


@register_handler(AttacherRegistry, 'adb_root')
class ADBRootAttacher(ADBAttacher):
    def __init__(self, adb_server: Optional[ADBServer] = None, device: Optional[str] = None):
        """An ADB-based attacher with root implementation for sending slide event via ``sendevent`` command.
        This attacher will fall back to basic ``ADBAttacher`` if root is unavailable.

        :param adb_server: ADB server.
        :param device: Specify which device to be controlled.
        """
        super(ADBRootAttacher, self).__init__(adb_server, device)
        self._rooted = LazyValue(self._check_root)
        self._input_device = LazyValue(self._get_input_device)

    def _check_root(self) -> bool:
        if spawn('whoami', spawn_fn=self._adb_shell.interact, raise_exc=True).strip() == 'root':
            return True
        self._adb_shell.interact('su', wait=False)
        sleep(0.3)
        result = spawn('whoami', spawn_fn=self._adb_shell.interact, raise_exc=True).strip()
        logger.debug(f'Root check: whoami returned "{result}"')
        return result == 'root'

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

    def _send_event_touch_down(self, device: str, px: int, py: int):
        args = [
            f'sendevent {device} {EventType.EV_KEY} {EventID.BTN_TOUCH} 1',
            f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_X} {px}',
            f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_Y} {py}',
            f'sendevent {device} {EventType.EV_SYN} {EventID.SYN_REPORT} 0'
        ]
        self._hook_send_event_touch_down(device, args, px, py)
        spawn(' && '.join(args), spawn_fn=self._adb_shell.interact, raise_exc=True)

    def _hook_send_event_touch_down(self, device: str, args: List[str], px: int, py: int):
        pass

    def _send_event_touch_up(self, device: str):
        args = [
            f'sendevent {device} {EventType.EV_KEY} {EventID.BTN_TOUCH} 0',
            f'sendevent {device} {EventType.EV_SYN} {EventID.SYN_REPORT} 0'
        ]
        self._hook_send_event_touch_up(device, args)
        spawn(' && '.join(args), spawn_fn=self._adb_shell.interact, raise_exc=True)

    def _hook_send_event_touch_up(self, device: str, args: List[str]):
        pass

    def _send_slide_impl(self, x1: int, y1: int, x2: int, y2: int, stay_time_before_move: float = 0.1,
                         stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        device = self._input_device()
        self._send_event_touch_down(device, x1, y1)
        sleep(stay_time_before_move)
        begin_t = time()
        last_x = x1
        last_y = y1
        while time() - begin_t < stay_time_move:
            norm_t = min(time() - begin_t, stay_time_move) / stay_time_move
            new_x = int(x1 + (x2 - x1) * norm_t)
            new_y = int(y1 + (y2 - y1) * norm_t)
            send_event_args = []
            if last_x != new_x:
                send_event_args.append(f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_X} {new_x}')
                last_x = new_x
            if last_y != new_y:
                send_event_args.append(f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_Y} {new_y}')
                last_y = new_y
            if len(send_event_args) > 0:
                send_event_args.append(f'sendevent {device} {EventType.EV_SYN} {EventID.SYN_REPORT} 0')
                spawn(' && '.join(send_event_args), spawn_fn=self._adb_shell.interact, raise_exc=True)
            sleep(0.002)
        send_event_args = []
        if last_x != x2:
            send_event_args.append(f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_X} {x2}')
        if last_y != y2:
            send_event_args.append(f'sendevent {device} {EventType.EV_ABS} {EventID.ABS_MT_POSITION_Y} {y2}')
        if len(send_event_args) > 0:
            send_event_args.append(f'sendevent {device} {EventType.EV_SYN} {EventID.SYN_REPORT} 0')
            spawn(' && '.join(send_event_args), spawn_fn=self._adb_shell.interact, raise_exc=True)
        sleep(stay_time_after_move)
        self._send_event_touch_up(device)

    def send_slide(self, p_from: PointF, p_to: PointF, stay_time_before_move: float = 0.1, stay_time_move: float = 0.8,
                   stay_time_after_move: float = 0.1):
        if self._rooted():
            try:
                # noinspection DuplicatedCode
                x1 = int(round(self.input_solution.width * p_from.x))
                y1 = int(round(self.input_solution.height * p_from.y))
                x2 = int(round(self.input_solution.width * p_to.x))
                y2 = int(round(self.input_solution.height * p_to.y))
                self._send_slide_impl(x1, y1, x2, y2, stay_time_before_move, stay_time_move, stay_time_after_move)
                return
            except Exception as ex:
                logger.warning(f'Failed to execute root implementation: {ex!r}, fall back to default implementation')
                self._rooted.value = False
        # fall back to non-root solution
        super(ADBRootAttacher, self).send_slide(p_from, p_to, stay_time_before_move, stay_time_move,
                                                stay_time_after_move)
