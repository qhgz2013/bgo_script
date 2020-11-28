__all__ = ['backend_call', 'backend_support', 'backend_determine']
from typing import *
import logging

logger = logging.getLogger('bgo_script.image_process')


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


# Annotation support
# Usage:
# @backend_support('imread', 1)
# def _imread_opencv_internal_call(img_path: str):
#     # internal function
#     return cv2.imread(img_path, cv2.IMREAD_COLOR)
#
# def imread(img_path: str):
#     # exposed function to public domain
#     return backend_call('imread', img_path)
def backend_support(group_name: str, call_priority: int = -1):
    """
    Add a image process backend to provide function redundancy

    :param group_name: The name of redundancy group
    :param call_priority: Call priority, starting from highest integer to 0, then the default value -1. Func with same
     priority are ordered by binding time
    :return: null
    """
    def internal_call(func: Callable):
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)
        wrapped.__name__ = func.__name__
        if group_name not in _cached_backend_funcs:
            _cached_backend_funcs[group_name] = {}
        func_list = _cached_backend_funcs[group_name]
        if call_priority not in func_list:
            func_list[call_priority] = []
        func_list[call_priority].append(func)
        logger.debug(f'Adding function {str(func)} to group "{group_name}" with priority {call_priority}')
        return wrapped
    return internal_call


_cached_backend_funcs = {}  # type: Dict[str, Dict[int, List[Callable]]]
_determined_funcs = {}  # type: Dict[str, Any]


def backend_call(group_name: str, *args, **kwargs):
    func = _determined_funcs.get(group_name, None)
    if func is None:
        func_prior_dict = _cached_backend_funcs.get(group_name, None)
        if func_prior_dict is None:
            raise KeyError(f'Group {group_name} is not presented, check your annotations.')
        func_list = []
        for prior in sorted(func_prior_dict.keys(), reverse=True):
            func_list.extend(func_prior_dict[prior])
        if len(func_list) == 0:
            raise ValueError(f'Group {group_name} has no available function.')
        func, ret_val = backend_determine(func_list, args, kwargs)
        _determined_funcs[group_name] = func
        logger.debug(f'Selected {str(func)} for group "{group_name}"')
        return ret_val
    else:
        return func(*args, **kwargs)
