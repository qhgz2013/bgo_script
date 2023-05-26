import multiprocessing as mp
from .image_hash_cacher import ImageHashCacher
from typing import *
import numpy as np
from logging import getLogger
import sqlite3
from .imdecode import imdecode
import time
import threading

__all__ = ['IM_CMP_FUNCTION', 'MPImageMatcher']

IM_CMP_FUNCTION = Callable[[np.ndarray, np.ndarray], float]
KEY_TYPE = Union[str, Tuple[str, Any]]
logger = getLogger('bgo_script.image_process')
_cache_empty_value = object()
_DEBUG_MODE = False  # pycharm will raise a strange bug "Exception ignored in tp_clear of <class 'memoryview'>" when debugging


class _MPImageMatcherRuntimeConfig:
    def __init__(self, sql_file, image_keys, cmp_func, on_image_loaded=None, on_image_decoded=None,
                 before_cmp=None, after_cmp=None):
        self.sql_file = sql_file
        self.image_keys = image_keys
        self.cmp_func = cmp_func
        self.on_image_loaded = on_image_loaded
        self.on_image_decoded = on_image_decoded
        self.before_cmp = before_cmp
        self.after_cmp = after_cmp
        self.memory_buffer = dict()


def _load_images_to_memory(config: _MPImageMatcherRuntimeConfig):
    t0 = time.time()
    sql_conn = sqlite3.connect(config.sql_file)
    sql_cursor = sql_conn.cursor()
    try:
        for image_key in config.image_keys:
            if image_key in config.memory_buffer:
                continue
            if isinstance(image_key, str):
                image_value = None
            else:
                image_key, image_value = image_key
            sql_cursor.execute('SELECT image_data FROM image WHERE image_key=?', (image_key,))
            image_data = sql_cursor.fetchone()[0]
            if config.on_image_loaded is not None:
                image_data = config.on_image_loaded(image_key, image_value, image_data)
            image = imdecode(image_data)
            if config.on_image_decoded is not None:
                image = config.on_image_decoded(image_key, image_value, image)
            config.memory_buffer[image_key] = image, image_value
    finally:
        sql_cursor.close()
        sql_conn.close()
        logger.debug(f'Load images to memory: {time.time() - t0:.3f}s')


def _worker_callback(rank: int, p: mp.Pipe):
    logger.debug(f'MPImageMatcher worker callback: rank={rank}')
    try:
        runtime_config = p.recv()
        _load_images_to_memory(runtime_config)
        while True:
            candidate = p.recv()
            if candidate is None:
                break
            best_key, best_value, best_score = None, None, 0x7fffffff
            for image_key, (image, image_value) in runtime_config.memory_buffer.items():
                if runtime_config.before_cmp is not None:
                    candidate, image = runtime_config.before_cmp(candidate, image)
                score = runtime_config.cmp_func(candidate, image)
                if runtime_config.after_cmp is not None:
                    score = runtime_config.after_cmp(candidate, image, score)
                if score < best_score:
                    best_key, best_value, best_score = image_key, image_value, score
            p.send((best_key, best_value, best_score))
    except (EOFError, KeyboardInterrupt):
        pass
    except Exception as e:
        logger.critical(f'Worker callback error: {e!r}', exc_info=True)


class MPImageMatcher:
    def __init__(self, sql_file: str, image_keys: Iterable[KEY_TYPE], cmp_func: IM_CMP_FUNCTION,
                 processes: int = 0, cacher: Optional[ImageHashCacher] = None,
                 on_image_loaded: Optional[Callable[[str, Any, bytes], bytes]] = None,
                 on_image_decoded: Optional[Callable[[str, Any, np.ndarray], np.ndarray]] = None,
                 before_cmp: Optional[Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]] = None,
                 after_cmp: Optional[Callable[[np.ndarray, np.ndarray, float], float]] = None):
        self._sql_file = sql_file
        if processes == 0:
            processes = mp.cpu_count()
        self._processes = processes
        self._cacher = cacher
        self._image_keys = image_keys if isinstance(image_keys, list) else list(image_keys)
        self._cmp_func = cmp_func
        self._workload = []
        self._worker_pool = []

        workloads = [list() for _ in range(self._processes)]
        for i, key in enumerate(self._image_keys):
            workloads[i % self._processes].append(key)

        if _DEBUG_MODE:
            logger.warning(f'Debug mode is ON for {type(self).__name__}, performance will degrade')
            cls = threading.Thread
        else:
            cls = mp.Process

        for i in range(self._processes):
            master, worker = mp.Pipe()
            proc = cls(target=_worker_callback, args=(i, worker), daemon=True, name=f'image-matcher-worker-{i}')
            self._worker_pool.append((proc, master))
            proc.start()
        for i, (_, master) in enumerate(self._worker_pool):
            master.send(_MPImageMatcherRuntimeConfig(
                sql_file=self._sql_file, image_keys=workloads[i], cmp_func=self._cmp_func,
                on_image_loaded=on_image_loaded, on_image_decoded=on_image_decoded, before_cmp=before_cmp,
                after_cmp=after_cmp
            ))

    def match(self, img: np.ndarray) -> Tuple[str, Any, float]:
        if self._cacher is not None:
            cache_result = self._cacher.get(img, _cache_empty_value)
            if cache_result is not _cache_empty_value:
                return cache_result

        for _, p in self._worker_pool:
            p.send(img)

        k, v, s = None, None, 0xffffffff
        for _, p in self._worker_pool:
            result = p.recv()
            if result[2] < s:
                k, v, s = result
        if self._cacher is not None:
            self._cacher[img] = k, v, s
        return k, v, s
