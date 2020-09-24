from typing import *


def backend_determine(call_func_list: List[Callable], args: tuple = tuple(), kwargs: dict = None) \
        -> Tuple[Callable, Any]:
    if kwargs is None:
        kwargs = {}
    for call_func in call_func_list:
        try:
            return call_func, call_func(*args, **kwargs)
        except ImportError:
            pass
    raise RuntimeError('All candidate functions are unavailable')
