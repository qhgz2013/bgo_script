from abc import ABCMeta
from basic_class import Resolution, Rect, Point

__all__ = ['Resolution', 'AbstractResolutionMatchRule', 'ExactResolutionMatchRule', 'RangeResolutionMatchRule',
           'ExactWidthHeightRatioMatchRule', 'Rect', 'Point']


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
        return abs(resolution.width / resolution.height - self.width_height_ratio) < 0.01

    def __repr__(self):
        return f'<ExactWidthHeightRatioMatchRule({self.width_height_ratio})>'
