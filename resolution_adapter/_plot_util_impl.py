import numpy as np
from .resolution_match_rule import Resolution, Rect, Point
import matplotlib.pyplot as plt
from io import BytesIO
from typing import *
from .factory import DetectionDefFactory, ClickDefFactory
from logging import getLogger

logger = getLogger(__name__)


# noinspection DuplicatedCode
def _plot_without_scaling(img: np.ndarray, plot_rect_func_names: Set[str], plot_point_func_names: Set[str],
                          dpi: float = 100.0, margin: int = 100):
    height, width = img.shape[:2]
    figsize = ((width + 2 * margin) / dpi, (height + 2 * margin) / dpi)
    left = margin / dpi / figsize[0]
    bottom = margin / dpi / figsize[1]

    gcf = plt.figure(figsize=figsize, dpi=dpi)
    gcf.subplots_adjust(left=left, bottom=bottom, right=1 - left, top=1 - bottom)

    plt.imshow(img)

    try:
        detection_handler = DetectionDefFactory.get_detection_def(Resolution(width, height))
        click_handler = ClickDefFactory.get_click_def(Resolution(width, height))
        for func_name in plot_rect_func_names:
            func = getattr(detection_handler, func_name)
            try:
                rects = func()
            except Exception as e:
                logger.error(f'plot_rect: {func_name} failed: {e}')
                continue
            if isinstance(rects, Rect):
                rects = [rects]
            elif not isinstance(rects, list):
                logger.warning(f'Method {func_name} returned {rects!r} which is not a Rect or a list or Rect')
                continue
            func_name = func_name.lstrip('_')
            if func_name.startswith('get_'):
                func_name = func_name[4:]
            for rect in rects:
                plt.gca().add_patch(plt.Rectangle((rect.x1, rect.y1), rect.width, rect.height, fill=False,
                                                  edgecolor='red', linewidth=1))
                plt.text(rect.x1 + 5, rect.y1 - 5, func_name, color='red')
        for func_name in plot_point_func_names:
            func = getattr(click_handler, func_name)
            try:
                points = func()
            except Exception as e:
                logger.error(f'plot_point: {func_name} failed: {e}')
                continue
            if isinstance(points, Point):
                points = [points]
            elif not isinstance(points, list):
                logger.warning(f'Method {func_name} returned {points!r} which is not a Point or a list or Point')
                continue
            func_name = func_name.lstrip('_')
            if func_name.startswith('get_'):
                func_name = func_name[4:]
            for point in points:
                plt.plot(point.x, point.y, 'go')
                plt.text(point.x + 5, point.y - 5, func_name, color='green')
    except ValueError:
        logger.warning(f'No handler found for resolution {width}x{height}, skip rectangle plotting')

    # plt.show()
    buf = BytesIO()
    gcf.savefig(buf, format='raw', dpi=dpi)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    img_arr = img_arr.reshape((int(figsize[1] * dpi), int(figsize[0] * dpi), -1))
    plt.close(gcf)
    return img_arr


def plot(img: np.ndarray, plot_rect_func_names: Set[str], plot_point_func_names: Set[str]) -> np.ndarray:
    return _plot_without_scaling(img, plot_rect_func_names, plot_point_func_names)
