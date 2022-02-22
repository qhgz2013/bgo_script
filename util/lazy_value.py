from threading import RLock
from typing import *

_value_uninitialized = object()
_T = TypeVar('_T')


class LazyValue(Generic[_T]):
    """
    A wrapper class for lazy value initialization
    """
    def __init__(self, func: Callable[..., _T]):
        self.value = _value_uninitialized
        self.func = func
        self._mt_lock = RLock()

    def __call__(self, *args, **kwargs) -> _T:
        with self._mt_lock:
            if self.value == _value_uninitialized:
                self.value = self.func(*args, **kwargs)
            return self.value

    def __repr__(self):
        try:
            if self.value == _value_uninitialized:
                return f'<{self.__class__.__name__} (unload, callback: {self.func!r})>'
            return f'<{self.__class__.__name__} ({self.value!r})>'
        except AttributeError:
            return f'<{self.__class__.__name__} (bad initialization)>'
