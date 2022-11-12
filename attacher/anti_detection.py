# attacher.anti_detection
# The clicks are too ... precious and predictable? Don't worry, let's randomize it!
# Ver 1.0
# Changelog:
# 1.0: Implemented basic anti-detection mechanism: use truncated normal to add noise to input coordinate, and use
#      random uniform to add noise to the click interval.
from dataclasses import dataclass
from typing import *
from basic_class import Resolution, PointF
import numpy as np
from .base import AttacherBase
from time import sleep
from logging import getLogger

__all__ = ['AntiDetectionConfig', 'AntiDetectionAttacher', 'RandomSamplingFunctionType']

RandomSamplingFunctionType = Callable[[], float]
logger = getLogger('bgo_script.attacher.anti_detection')


def _truncated_normal(mean: float = 0.0, stddev: float = 1.0, clip: float = 10) -> float:
    return float(np.clip(np.random.normal(mean, stddev), -clip, clip))


def _uniform(lo: float = 0.0, hi: float = 0.5) -> float:
    return float(np.random.uniform(lo, hi))


@dataclass
class AntiDetectionConfig:
    """Config for anti-detection."""

    enable_random_offset: bool = False
    """Set to true to add random noise to original input point."""
    random_offset_sampling_func: RandomSamplingFunctionType = _truncated_normal

    enable_random_latency: bool = False
    """Set to true to add random latency to original input."""
    random_latency_sampling_func: RandomSamplingFunctionType = _uniform


class AntiDetectionAttacher(AttacherBase):
    """An intermediate attacher class for applying ``AntiDetectionConfig``."""
    def __init__(self, forward_attacher: AttacherBase, config: AntiDetectionConfig):
        self.forward_attacher = forward_attacher
        self.config = config

    @property
    def input_solution(self) -> Resolution:
        return self.forward_attacher.input_solution

    def _apply_random_latency(self):
        if not self.config.enable_random_latency:
            return
        try:
            sampled_latency = self.config.random_latency_sampling_func()
            if sampled_latency <= 0:
                logger.debug(f'Sampled latency "{sampled_latency}" is non-positive, skip.')
                return
            sleep(sampled_latency)
        except Exception as e:
            logger.error(f'Failed to sample latency, disable random latency. Error: {e!r}', exc_info=e)

    def _apply_random_offset(self, x: float, y: float) -> Tuple[float, float]:
        if not self.config.enable_random_offset:
            return x, y
        try:
            sampled_offset_x = self.config.random_offset_sampling_func()
            sampled_offset_y = self.config.random_offset_sampling_func()
            px, py = int(round(self.input_solution.width * x)), int(round(self.input_solution.height * y))
            px = np.clip(px + sampled_offset_x, 0, self.input_solution.width - 1)
            py = np.clip(py + sampled_offset_y, 0, self.input_solution.height - 1)
            return float(px / self.input_solution.width), float(py / self.input_solution.height)
        except Exception as e:
            logger.error(f'Failed to sample offset, disable random offset. Error: {e!r}', exc_info=e)
            return x, y

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        self._apply_random_latency()
        x, y = self._apply_random_offset(x, y)
        return self.forward_attacher.send_click(x=x, y=y, stay_time=stay_time)

    def send_slide(self, p_from: PointF, p_to: PointF, stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        self._apply_random_latency()
        x1, y1 = self._apply_random_offset(p_from.x, p_from.y)
        x2, y2 = self._apply_random_offset(p_to.x, p_to.y)
        return self.forward_attacher.send_slide(p_from=PointF(x1, y1), p_to=PointF(x2, y2),
                                                stay_time_before_move=stay_time_before_move,
                                                stay_time_move=stay_time_move,
                                                stay_time_after_move=stay_time_after_move)
