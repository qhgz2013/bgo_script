# attacher.base
# Basic definitions for interacting with external systems.
# Ver 1.0
# Changelog:
# 1.0: Split capturer and attacher into independent class, provide CombinedAttacher as backward-compatible class.
from abc import ABCMeta
import numpy as np
from typing import *

__all__ = ['ScreenCapturer', 'AbstractAttacher', 'Point', 'Solution', 'CombinedAttacher']


class Point(NamedTuple):
    x: float
    y: float


class Solution(NamedTuple):
    height: int
    width: int


class ScreenCapturer(metaclass=ABCMeta):
    """An abstract class for capturing screenshots from device / simulator"""

    def get_solution(self) -> Solution:
        """Get the default screenshot solution, in (height, width) tuple."""
        raise NotImplementedError

    def get_screenshot(self) -> np.ndarray:
        """Returns current screenshot as numpy array in (h, w, c) shape."""
        raise NotImplementedError


class AbstractAttacher(metaclass=ABCMeta):
    """AbstractAttacher defines the basic interface to interact with the game application."""
    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        raise NotImplementedError

    def send_slide(self, p_from: Point, p_to: Point, stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        raise NotImplementedError


_POINT_COMPATIBLE = Union[Point, Tuple[float, float]]


class CombinedAttacher(ScreenCapturer, AbstractAttacher):
    """Same as the full version of Attacher before. For compatible usage"""
    def __init__(self, capturer: ScreenCapturer, attacher: AbstractAttacher):
        self.capturer = capturer
        self.attacher = attacher

    def get_solution(self) -> Solution:
        return self.capturer.get_solution()

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        img = self.capturer.get_screenshot()
        if width is None and height is None:
            return img
        import image_process
        return image_process.resize(img, width, height)

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        self.attacher.send_click(x, y, stay_time)

    def send_slide(self, p_from: _POINT_COMPATIBLE, p_to: _POINT_COMPATIBLE, stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        if not isinstance(p_from, Point):
            p_from = Point(*p_from)
        if not isinstance(p_to, Point):
            p_to = Point(*p_to)
        self.attacher.send_slide(p_from, p_to, stay_time_before_move, stay_time_move, stay_time_after_move)
