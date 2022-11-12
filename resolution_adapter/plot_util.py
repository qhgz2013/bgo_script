import logging
import numpy as np

__all__ = ['plot_rect', 'plot_point', 'plot_detection_rects_and_click_points']

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


def plot_detection_rects_and_click_points(img: np.ndarray, plot_detection_rects: bool = True,
                                          plot_click_points: bool = True) -> np.ndarray:
    from ._plot_util_impl import plot as _plot
    plot_rect_funcs = _cache_plot_rect_func_names if plot_detection_rects else set()
    plot_point_funcs = _cache_plot_point_func_names if plot_click_points else set()
    return _plot(img, plot_rect_funcs, plot_point_funcs)
