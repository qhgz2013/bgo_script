# attacher._ffmpeg_util
# A file-like wrapper class for converting h264-encoded video stream provided by "attacher.adb.ADBScreenRecorder" to
# RGB stream using FFMpeg tool.
# Ver 1.0
# Changelog:
# 1.0: Split from original attacher class.
import threading
from types import TracebackType
from typing import *
from typing import IO
from io import UnsupportedOperation
from util import find_path
import os
import subprocess
from time import sleep
from logging import getLogger

__all__ = ['ADBScreenrecordFFMpegDecoder']

logger = getLogger('bgo_script.attacher.ffmpeg')
_WARN_MEMORY_BUFFER_THRESHOLD = 100 * 0x100000  # warn user if the script cannot keep up with ffmpeg, default: 100MB
_TERMINATE_MEMORY_BUFFER_THRESHOLD = 10 * _WARN_MEMORY_BUFFER_THRESHOLD  # terminate ffmpeg if buffer is too large
_warned_memory_buffer_size = False


# cmdline: ffmpeg -probesize 32 -f h264 -i pipe: -f rawvideo -pix_fmt rgb24 -filter:v fps=fps=10 pipe:
class ADBScreenrecordFFMpegDecoder(IO[bytes]):
    """Only works for ADB screenrecord that takes H264 encoded video as input and RGB image stream as output."""

    # <<< begin IO[bytes] implementation

    def close(self) -> None:
        with self._buffer_lock:
            if self._closed:
                return
            for stream in [getattr(self._ffmpeg_process, x) for x in ['stdin', 'stdout', 'stderr']]:
                if stream is not None:
                    stream.close()
            self._ffmpeg_process.terminate()
            self._closed = True

    def fileno(self) -> int:
        return self._encode_stream.fileno()

    def flush(self) -> None:
        raise UnsupportedOperation

    def isatty(self) -> bool:
        return False

    def read(self, n: int = -1) -> bytes:
        if n == 0:
            return b''
        with self._buffer_lock:
            if n < 0:
                return bytes(self._buffer)
            while len(self._buffer) < n and self._ffmpeg_process.poll() is None:
                # if available buffer does not satisfy n bytes, wait until process exited
                self._buffer_lock.release()
                self._write_event.wait()
                self._write_event.clear()
                self._buffer_lock.acquire()
            bytes_read = bytes(self._buffer[:n])
            del self._buffer[:n]
            return bytes_read

    def readable(self) -> bool:
        return not self._closed

    def readline(self, limit: int = -1) -> bytes:
        raise UnsupportedOperation

    def readlines(self, hint: int = -1) -> List[bytes]:
        raise UnsupportedOperation

    def seek(self, offset: int, whence: int = 0) -> int:
        raise UnsupportedOperation

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        raise UnsupportedOperation

    def truncate(self, size: Optional[int] = None) -> int:
        raise UnsupportedOperation

    def writable(self) -> bool:
        return False

    def write(self, s: bytes) -> int:
        raise UnsupportedOperation

    def writelines(self, lines: Iterable[bytes]) -> None:
        raise UnsupportedOperation

    def __next__(self) -> bytes:
        raise UnsupportedOperation

    def __iter__(self) -> Iterator[bytes]:
        return self

    def __enter__(self) -> IO[bytes]:
        return self

    def __exit__(self, t: Optional[Type[BaseException]], value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> Optional[bool]:
        self.close()
        return None

    @property
    def closed(self) -> bool:
        return self._closed

    # <<< end IO[bytes] implementation

    def __init__(self, encoded_stream: IO[bytes], ffmpeg_executable_path: Optional[str] = None,
                 fps: Optional[int] = 10):
        if ffmpeg_executable_path is None:
            ffmpeg_executable_path = find_path('ffmpeg.exe')
        if ffmpeg_executable_path is None:
            raise RuntimeError('FFMpeg executable not found')
        if not os.path.isfile(ffmpeg_executable_path):
            raise RuntimeError(f'FFMpeg path "{ffmpeg_executable_path}" is not a file')
        self.ffmpeg_executable = ffmpeg_executable_path
        if not encoded_stream.readable():
            raise RuntimeError(f'Encode stream {encoded_stream!r} is not readable')
        self._encode_stream = encoded_stream
        cmd = [self.ffmpeg_executable, '-probesize', '32', '-f', 'h264', '-i', 'pipe:', '-f', 'rawvideo', '-pix_fmt',
               'rgb24']
        if fps is not None:
            # fps specified
            cmd.extend(['-filter:v', f'fps=fps={fps}'])
        cmd.append('pipe:')
        self._buffer_lock = threading.RLock()
        self._buffer = bytearray()  # work as FIFO bytes array
        self._closed = False
        self._write_event = threading.Event()
        self._ffmpeg_process = subprocess.Popen(cmd, stdin=self._encode_stream, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, bufsize=0)
        self._stderr_handler = threading.Thread(target=self._handle_stderr, daemon=True)
        self._stderr_handler.start()
        self._stdout_handler = threading.Thread(target=self._handle_stdout, daemon=True)
        self._stdout_handler.start()
        self._ffmpeg_shutdown_thread = threading.Thread(target=self._shut_down_ffmpeg_callback)
        self._ffmpeg_shutdown_thread.start()

    @property
    def ffmpeg_process(self) -> Optional[subprocess.Popen]:
        return self._ffmpeg_process

    def _handle_stdout(self):
        # redirect stdout to _buffer
        while self._ffmpeg_process.poll() is None:
            bytes_read = self._ffmpeg_process.stdout.read(65536)
            if len(bytes_read) > 0:
                with self._buffer_lock:
                    self._buffer.extend(bytes_read)
                    self._write_event.set()
                    global _warned_memory_buffer_size
                    if len(self._buffer) > _WARN_MEMORY_BUFFER_THRESHOLD and not _warned_memory_buffer_size:
                        logger.warning(f'{self.__class__.__name__} has detected that the downstream process speed '
                                       f'cannot keep up with the decoder output, this will increase memory usage and '
                                       f'the program will crash some time later. (This warning will be logged once)')
                        _warned_memory_buffer_size = True
                    if len(self._buffer) > _TERMINATE_MEMORY_BUFFER_THRESHOLD:
                        break
        self.close()

    def _handle_stderr(self):
        # ignore stderr
        while self._ffmpeg_process.poll() is None:
            try:
                data = self._ffmpeg_process.stderr.read(4096)
            except ValueError:
                # I/O operation on closed file
                break
            # if len(data) > 0:
            #     print(str(data, 'utf8'))
        self.close()

    def _shut_down_ffmpeg_callback(self):
        while threading.main_thread().is_alive():
            sleep(0.5)
        if self._ffmpeg_process.poll() is None:
            logger.info('Main thread exited, shutting down existing FFMpeg process')
            self._ffmpeg_process.terminate()

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__} for Process ID {self._ffmpeg_process.pid}' \
                   f'{" (exited)" if self._ffmpeg_process.returncode is not None else ""}>'
        except AttributeError:
            return f'<{self.__class__.__name__} (uninitialized)>'
