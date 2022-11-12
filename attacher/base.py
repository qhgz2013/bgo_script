# attacher.base
# Basic definitions for interacting with external systems.
# Ver 1.2
# Changelog:
# 1.2: Added registry for string lookup
# 1.1: Changed definition of class Point for further multi-solution support, renamed AbstractAttacher to AttacherBase.
# 1.0: Split capturer and attacher into independent class, provide CombinedAttacher as backward-compatible class.
from abc import ABCMeta
import numpy as np
from typing import *
from basic_class import *
from util import HandlerRegistry

__all__ = ['ScreenCapturer', 'AttacherBase', 'CombinedAttacher', 'AttacherRegistry', 'CapturerRegistry']


class ScreenCapturer(metaclass=ABCMeta):
    """An abstract class for capturing screenshots from device / simulator"""

    def get_resolution(self) -> Resolution:
        """Get the default screenshot solution, in (height, width) tuple."""
        raise NotImplementedError

    def get_screenshot(self) -> np.ndarray:
        """Returns current screenshot as numpy array in (h, w, c) shape."""
        raise NotImplementedError


class AttacherBase(metaclass=ABCMeta):
    """``AttacherBase`` defines the basic interface to interact with the game application."""
    def send_click(self, x: int, y: int, stay_time: float = 0.1):
        raise NotImplementedError

    def send_slide(self, p_from: Point, p_to: Point, stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        raise NotImplementedError


class AttacherRegistry(HandlerRegistry[str, AttacherBase]):
    pass


class CapturerRegistry(HandlerRegistry[str, ScreenCapturer]):
    pass


_POINT_COMPATIBLE = Union[Point, Tuple[int, int]]
_STAY_TIME_COMPATIBLE = Optional[float]


# backward compatible class, will be removed in future version
class CombinedAttacher(ScreenCapturer, AttacherBase):
    """Same as the full version of Attacher before. For compatible usage."""
    def __init__(self, capturer: ScreenCapturer, attacher: AttacherBase):
        self.capturer = capturer
        self.attacher = attacher

    def get_resolution(self) -> Resolution:
        return self.capturer.get_resolution()

    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        img = self.capturer.get_screenshot()
        if width is None and height is None:
            return img
        import image_process
        return image_process.resize(img, width, height)

    def send_click(self, x: int, y: int, stay_time: float = 0.1):
        self.attacher.send_click(x, y, stay_time)

    def send_slide(self, p_from: _POINT_COMPATIBLE, p_to: _POINT_COMPATIBLE,
                   stay_time_before_move: _STAY_TIME_COMPATIBLE = None,
                   stay_time_move: _STAY_TIME_COMPATIBLE = None, stay_time_after_move: _STAY_TIME_COMPATIBLE = None):
        if not isinstance(p_from, Point):
            p_from = Point(*p_from)
        if not isinstance(p_to, Point):
            p_to = Point(*p_to)
        extra_args = {}
        # use the default value provided by implementation method if stay_time_* set to None
        if stay_time_before_move is not None:
            extra_args['stay_time_before_move'] = stay_time_before_move
        if stay_time_move is not None:
            extra_args['stay_time_move'] = stay_time_move
        if stay_time_after_move is not None:
            extra_args['stay_time_after_move'] = stay_time_after_move
        self.attacher.send_slide(p_from, p_to, **extra_args)
