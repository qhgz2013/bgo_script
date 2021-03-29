from threading import RLock
from typing import *

_value_uninitialized = object()


class LazyValue:
    """
    A wrapper class for lazy value initialization
    """
    def __init__(self, func: Callable[[Any], Any]):
        self.value = _value_uninitialized
        self.func = func
        self.mt_lock = RLock()

    def __call__(self, *args, **kwargs):
        with self.mt_lock:
            if self.value == _value_uninitialized:
                self.value = self.func(*args, **kwargs)
            return self.value
