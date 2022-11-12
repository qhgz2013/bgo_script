# attacher.adb_util
# Provides some util classes and IPC helpers for interacting with ADB server and ADB shell.
# Ver 1.1
# Changelog:
# 1.1: Added pickling support for ADBServer
# 1.0: Moved from util package.
from typing import *
from util import spawn_process, find_path, SingletonMeta
from logging import getLogger
import os
import threading
from time import sleep
from functools import partial
import re
from io import BufferedIOBase, StringIO
import subprocess
from uuid import uuid4

__all__ = ['spawn', 'MSG_TYPE', 'find_adb_path', 'ADBServer', 'ADBShell']

logger = getLogger('bgo_script.attacher.adb')
_cache_adb_path_not_found = object()
_cache_adb_path = None
_DEVICE_PATTERN = re.compile(r'^(?P<device_name>[^\s]+)\s+(?P<device_type>device)$')
MSG_TYPE = Literal['stdout', 'stderr']
_PIPE = subprocess.PIPE
_T = TypeVar('_T', bound=AnyStr)
SPAWN_FUNC_PROTOTYPE = Callable[..., Tuple[int, _T, _T]]
ADB_DEFAULT_LISTENING_PORT = 5037


def spawn(*cmds: str, spawn_fn: SPAWN_FUNC_PROTOTYPE = spawn_process,
          raise_exc: bool = False, log: bool = True, ignore_stderr: bool = False) -> _T:
    ret_code, stdout, stderr = spawn_fn(cmds)
    if ret_code != 0:
        try:
            msg = f'ADB call exited with non-zero returned value: {ret_code} ({ret_code:#x})'
        except TypeError:
            # got a non-reproducible error here, it's freak
            msg = f'ADB call exited with non-zero returned value: {ret_code} ({ret_code!r})'
        if log:
            logger.warning(msg)
        if raise_exc:
            raise RuntimeError(msg)
    if not ignore_stderr and len(stderr) > 0:
        msg = f'ADB call exited with stderr output: {stderr!r}'
        if log:
            logger.warning(msg)
        if raise_exc:
            raise RuntimeError(msg)
    return stdout


def find_adb_path() -> Optional[str]:
    """Find adb executable in ``PATH`` environment.

    :return: Absolute path for adb executable (if found) or None
    """
    global _cache_adb_path
    if _cache_adb_path is None:
        _cache_adb_path = find_path('adb.exe') or _cache_adb_path_not_found
        if _cache_adb_path == _cache_adb_path_not_found:
            logger.warning('ADB executable not found in PATH environment')
        else:
            logger.debug('ADB executable path: %s', _cache_adb_path)
    if _cache_adb_path == _cache_adb_path_not_found:
        return None
    return _cache_adb_path


class ADBShell:
    def __init__(self, adb_path: str, target_device: Optional[str] = None):
        """A wrapper for ADB shell commands with mux functionality. It is capable of running multiple commands within
        same ADB shell process, rather than spawning new process to run exact one command, which may introduce too much
        process creation overhead.

        :param adb_path: ADB executable path.
        :param target_device: Device name to be interacted with, which equals to "adb shell -s target_device".
            Leave None to use default device (if only one device is connected). Use "adb devices" command or call
            ADBServer.list_devices() to list all available devices.
        """
        if target_device is None:
            cmd = [adb_path, 'shell']
        else:
            cmd = [adb_path, '-s', target_device, 'shell']
        self._target_device = target_device
        self._adb_proc = subprocess.Popen(cmd, stdin=_PIPE, stdout=_PIPE, stderr=_PIPE)
        self._mutex = threading.RLock()
        self._session_id = None
        self._stdout_buf = StringIO()
        self._stderr_buf = StringIO()
        self._session_started = threading.Event()
        self._session_finished = threading.Event()
        self._session_exit_code = None
        self._wait_session = None
        self._sync_event = threading.Event()
        self._stdout_thread = threading.Thread(target=self._handle_shell_output, daemon=True,
                                               args=(self._adb_proc.stdout, 'stdout', self._stdout_buf))
        self._stdout_thread.start()
        self._stderr_thread = threading.Thread(target=self._handle_shell_output, daemon=True,
                                               args=(self._adb_proc.stderr, 'stderr', self._stderr_buf))
        self._stderr_thread.start()
        self._self_testing()

    def _self_testing(self):
        # run self testing
        rnd_str = uuid4().bytes.hex()
        logger.debug(f'Self-test started with random string "{rnd_str}"')
        try:
            exit_code, stdout, stderr = self.interact(['echo', rnd_str])
            self_repr = f'{self.__class__.__name__!r} self-test failed:'
            if exit_code != 0:
                logger.warning(f'{self_repr} abnormal exit code {exit_code}')
            if len(stderr) != 0:
                logger.warning(f'{self_repr} unexpected stderr "{stderr}"')
            if stdout.strip() != rnd_str:
                logger.warning(f'{self_repr} expected output "{rnd_str}", but got "{stdout}", functionality maybe'
                               f' incorrect')
        finally:
            logger.debug('Self-test finished, results are logged as warning if corrupted')

    def _handle_shell_output(self, shell_output: BufferedIOBase, msg_type: MSG_TYPE, stream_out: StringIO):
        # read output from shell (shell_output), escape session boundaries, and extract payload to stream_out
        while self._adb_proc.poll() is None:  # loop until terminated
            data = shell_output.readline().decode('utf8').rstrip()
            if len(data) == 0:
                continue
            if msg_type == 'stderr':
                # a rarely occur scenario: stderr handles earlier than any stdout (i.e., the session start boundary from
                # stdout is not handled yet), caused by thread scheduling
                # so here stderr needs to wait until stdout handling started
                self._sync_event.wait()
            with self._mutex:
                logger.debug(f'[PID {self._adb_proc.pid}] {msg_type}: {data}')
                if self._session_id is None:
                    # the output does not belong to any session since the session is not started yet, drop it
                    continue
                if self._session_started.is_set():
                    # when a new session arrives (event session_started set to true), we expect to receive the boundary
                    # text coming first, because we've already printed the session identifier before executing any
                    # commands (view also: method "interact")
                    if data != self._session_id:
                        # logger.warning('Adb shell session error: unexpected output "%s", ignored.', data)
                        continue
                    self._session_started.clear()  # make sure it is triggered only once per session
                    if msg_type == 'stdout':
                        self._sync_event.set()
                    if not self._wait_session:
                        # if not waiting for the execution output, set to finished directly
                        self._session_finished.set()
                    # since we've verified the session, the next line of output will be the payload generated
                    # by the command itself (or another session boundary if no output produced)
                    continue
                elif data.startswith(self._session_id):
                    # another session boundary: end of session, fetching execution result (exit code)
                    if data == self._session_id + '-s':
                        # success
                        self._session_exit_code = 0
                        self._session_finished.set()
                        continue
                    elif data.startswith(self._session_id + '-f'):
                        # failed: exit code is appended after "-f"
                        self._session_exit_code = int(data[len(self._session_id) + 2:])
                        self._session_finished.set()
                        continue
                # copy remain output text (boundaries are excluded) to "stream_out"
                stream_out.write(data + '\n')

    @staticmethod
    def _build_command(args: Sequence[Any]) -> str:
        if len(args) == 0:
            return ''
        # adb commands are generated like:
        # $ arg0 'arg1' 'arg2' 'arg3' ...
        # therefore, the char ' (single quote) must be translated into '"'"'
        buf = StringIO()
        buf.write(str(args[0]))
        for arg in args[1:]:
            buf.write(" '")
            buf.write(str(arg).replace("'", "'\"'\"'"))
            buf.write("'")
        return buf.getvalue()

    def interact(self, cmd: Union[str, Sequence[Any]], wait: bool = True) -> Optional[Tuple[int, str, str]]:
        """Interact with ADB shell, just like ``adb shell`` command.

        :param cmd: Command string or command sequence.
        :param wait: Wait for the execution complete (for non-termination command like "su", set it to false).
        :return: A tuple of (exit_code, stdout, stderr) if wait is true, or None if false.
        """
        if self._adb_proc.returncode is not None:
            raise RuntimeError('ADB shell process has exited')
        if not isinstance(cmd, str):
            cmd = self._build_command(cmd)
        boundary = '--' + os.urandom(8).hex()
        # this is how mux works: print boundary before command execution, as well as print the execution result after
        # execution (even if the command failed)
        cmd = f'echo {boundary} && ((({cmd}) && echo {boundary}-s) || echo {boundary}-f$?)'
        if len(cmd) == 0:
            return 0, '', ''  # ignore empty command
        with self._mutex:
            self._session_id = boundary
            logger.debug(f'[PID {self._adb_proc.pid}] stdin: {cmd}')
            cmd = cmd.encode('utf8') + b'\n'
            self._session_exit_code = None
            self._wait_session = wait
            self._sync_event.clear()
            self._stdout_buf.seek(0)
            self._stderr_buf.seek(0)
            self._stdout_buf.truncate(0)
            self._stderr_buf.truncate(0)

            self._adb_proc.stdin.write(cmd)
            self._adb_proc.stdin.flush()
            self._session_started.set()
        self._session_finished.wait()
        self._session_finished.clear()
        if not wait:
            return None
        with self._mutex:
            stdout = self._stdout_buf.getvalue()
            stderr = self._stderr_buf.getvalue()
        # noinspection PyTypeChecker
        return self._session_exit_code, stdout, stderr

    def kill(self) -> None:
        """Kill ADB shell process"""
        self._adb_proc.terminate()
        self._adb_proc.wait()

    def is_alive(self) -> bool:
        """Check the ADB shell is alive or not."""
        return self._adb_proc.returncode is None

    @property
    def target_device(self) -> Optional[str]:
        return self._target_device

    def __repr__(self):
        try:
            repr_str = f'{self.__class__.__name__} for ADB Process ID {self._adb_proc.pid!r}'
            if self._target_device is not None:
                repr_str += f' (device: {self._target_device})'
            return f'<{repr_str}>'
        except AttributeError:
            return f'<{self.__class__.__name__} (uninitialized)>'


class ADBServer(metaclass=SingletonMeta):
    """A singleton class for ADB server. All hooks before/after ADB server can be implemented via class inheritance."""
    _mutex = threading.RLock()
    _started = False  # all the subclasses share this state

    def _check_adb_daemon_alive_socket_impl(self) -> bool:
        import socket
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            skt.connect(('localhost', self.adb_server_port))
            skt.close()
            logger.debug(f'Check ADB daemon status: alive')
            return True
        except (ConnectionRefusedError, ConnectionResetError):
            logger.debug(f'Check ADB daemon status: offline')
            return False

    def __init__(self, adb_executable_path: Optional[str] = None, adb_server_port: int = ADB_DEFAULT_LISTENING_PORT):
        if adb_executable_path is None:
            adb_executable_path = find_adb_path()
        if adb_executable_path is None:
            raise RuntimeError('Could not find adb executable automatically in PATH variable')
        if not os.path.isfile(adb_executable_path):
            raise RuntimeError(f'Adb executable "{adb_executable_path}" is not a file')
        self.adb_executable = adb_executable_path
        self.adb_server_port = adb_server_port
        # use the legacy method to set the ADB listening port
        os.putenv('ANDROID_ADB_SERVER_PORT', str(self.adb_server_port))
        ADBServer._started = self._check_adb_daemon_alive_socket_impl()
        logger.debug('Checking ADB server daemon')
        # self.stop(force=True)
        self.start()
        # setting up adb server shut down thread
        thd = threading.Thread(target=self._shutdown_adb_server, daemon=False)
        thd.start()

    def stop(self, force: bool = False):
        """(Forcibly) shut down existing ADB server daemon process."""
        with ADBServer._mutex:
            if force or ADBServer._started:
                self._stop_internal()
                ADBServer._started = False

    def _stop_internal(self):
        spawn(self.adb_executable, 'kill-server', log=False)

    def start(self):
        """Start ADB server."""
        with ADBServer._mutex:
            if ADBServer._started:
                return
            self._start_internal()
            ADBServer._started = True

    def _start_internal(self):
        spawn(self.adb_executable, 'start-server', ignore_stderr=True, raise_exc=True)

    def restart(self, force: bool = False):
        """Kill the existing ADB server and restart it."""
        self.stop(force)
        self.start()

    def _shutdown_adb_server(self):
        spawn_func = partial(spawn_process, timeout=5.)  # added default timeout 5 secs
        while threading.main_thread().is_alive():
            sleep(0.2)
        logger.info('Main thread exited, shutting down adb server')
        spawn(self.adb_executable, 'kill-server', spawn_fn=spawn_func)

    def get_shell(self, device: Optional[Union[int, str]] = None) -> ADBShell:
        self.start()
        if isinstance(device, int):
            device = self.list_devices()[device]
        return ADBShell(self.adb_executable, target_device=device)

    def execute(self, *cmds: Any, timeout: Optional[float] = None, timeout_retry: int = 5) -> Tuple[int, str, str]:
        self.start()
        return spawn_process((self.adb_executable,) + cmds, timeout=timeout, timed_out_retry=timeout_retry)

    def list_devices(self) -> List[str]:
        self.start()
        stdout = spawn(self.adb_executable, 'devices', raise_exc=True)
        header = 'List of devices attached'
        if stdout.startswith(header):
            stdout = stdout[len(header):].lstrip()
        devices = []
        for line in stdout.split('\n'):
            line = line.rstrip()
            if len(line) == 0:
                continue
            result = re.match(_DEVICE_PATTERN, line)
            if result is not None:
                devices.append(result.group('device_name'))
            else:
                logger.info(f'Failed to parse ADB devices command result: Unknown output {line}')
        return devices

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__}{" (started)" if ADBServer._started else ""}>'
        except AttributeError:
            return f'<{self.__class__.__name__} (uninitialized)>'

    # hooks for multiprocessing: state is checked from socket
    def __getstate__(self):
        return self.adb_executable, self.adb_server_port

    def __setstate__(self, state):
        self.adb_executable, self.adb_server_port = state
        os.putenv('ANDROID_ADB_SERVER_PORT', str(self.adb_server_port))
        ADBServer._mutex = threading.RLock()
        ADBServer._started = self._check_adb_daemon_alive_socket_impl()
