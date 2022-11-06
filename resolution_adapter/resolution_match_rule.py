from abc import ABCMeta
from dataclasses import dataclass

__all__ = ['Resolution', 'AbstractResolutionMatchRule', 'ExactResolutionMatchRule', 'RangeResolutionMatchRule',
           'ExactWidthHeightRatioMatchRule', 'Rect', 'Point']


@dataclass(order=True, unsafe_hash=True)
class Resolution:
    width: int
    height: int


@dataclass(unsafe_hash=True, order=True)
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1


@dataclass(unsafe_hash=True, order=True)
class Point:
    x: int
    y: int


class AbstractResolutionMatchRule(metaclass=ABCMeta):
    def match(self, resolution: Resolution) -> bool:
        raise NotImplementedError


class ExactResolutionMatchRule(AbstractResolutionMatchRule):
    def __init__(self, resolution: Resolution):
        self.resolution = resolution

    def match(self, resolution: Resolution) -> bool:
        return resolution == self.resolution

    def __repr__(self):
        return f'<ExactResolutionMatchRule({self.resolution})>'


class RangeResolutionMatchRule(AbstractResolutionMatchRule):
    def __init__(self, min_resolution: Resolution, max_resolution: Resolution):
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution

    def match(self, resolution: Resolution) -> bool:
        return self.min_resolution.width <= resolution.width <= self.max_resolution.width and \
                self.min_resolution.height <= resolution.height <= self.max_resolution.height

    def __repr__(self):
        return f'<RangeResolutionMatchRule({self.min_resolution}, {self.max_resolution})>'


class ExactWidthHeightRatioMatchRule(AbstractResolutionMatchRule):
    def __init__(self, width_height_ratio: float):
        self.width_height_ratio = width_height_ratio

    def match(self, resolution: Resolution) -> bool:
        return abs(resolution.width / resolution.height - self.width_height_ratio) < 0.001

    def __repr__(self):
        return f'<ExactWidthHeightRatioMatchRule({self.width_height_ratio})>'
