import logging
import numpy as np

__all__ = ['plot_rect', 'plot_point', 'plot']

logger = logging.getLogger(__name__)
_cache_plot_rect_func_names = set()
_cache_plot_point_func_names = set()


def plot_rect(f):
    logger.debug(f'plot_rect: add function {f.__name__}')
    _cache_plot_rect_func_names.add(f.__name__)
    return f


def plot_point(f):
    logger.debug(f'plot_point: add function {f.__name__}')
    _cache_plot_point_func_names.add(f.__name__)
    return f


def plot(img: np.ndarray) -> np.ndarray:
    from ._plot_util_impl import plot as _plot
    return _plot(img, _cache_plot_rect_func_names, _cache_plot_point_func_names)
