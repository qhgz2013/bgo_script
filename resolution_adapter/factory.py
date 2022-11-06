from util import HandlerRegistry
from .resolution_match_rule import AbstractResolutionMatchRule, Resolution
from .abstract_detection_def import AbstractDetectionDef
from .abstract_click_def import AbstractClickDef

__all__ = ['DetectionDefFactory', 'ClickDefFactory']


class DetectionDefFactory(HandlerRegistry[AbstractResolutionMatchRule, AbstractDetectionDef]):
    @classmethod
    def get_detection_def(cls, resolution: Resolution) -> AbstractDetectionDef:
        for rule, handler in cls._registered_handlers.items():
            if rule.match(resolution):
                return handler
        raise ValueError(f'No matching DetectionDef for resolution {resolution}')


class ClickDefFactory(HandlerRegistry[AbstractResolutionMatchRule, AbstractClickDef]):
    @classmethod
    def get_click_def(cls, resolution: Resolution) -> AbstractClickDef:
        for rule, handler in cls._registered_handlers.items():
            if rule.match(resolution):
                return handler
        raise ValueError(f'No matching ClickDef for resolution {resolution}')
