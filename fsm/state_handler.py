from abc import ABCMeta
from bgo_game import ScriptEnv
from .fgo_state import FgoState
from time import sleep, time
import logging
import numpy as np
import image_process

__all__ = ['StateHandler', 'WaitFufuStateHandler', 'DirectStateForwarder', 'SingleClickHandler',
           'SingleClickAndWaitFufuHandler']

logger = logging.getLogger('bgo_script.fsm')


class StateHandler(metaclass=ABCMeta):
    def run_and_transit_state(self) -> FgoState:
        raise NotImplementedError()

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        self.env = env
        self.forward_state = forward_state

    def _get_screenshot_impl(self):
        # get screenshot from capturer, resize to target resolution if given
        screenshot = self.env.capturer.get_screenshot()
        resolution = self.env.detection_definitions.get_target_resolution()
        if resolution is not None:
            screenshot = image_process.resize(screenshot, resolution.width, resolution.height)
        return screenshot


class DirectStateForwarder(StateHandler):
    def run_and_transit_state(self) -> FgoState:
        return self.forward_state


class WaitFufuStateHandler(StateHandler):
    def run_and_transit_state(self) -> FgoState:
        begin_timing = time()
        logger.debug('Started waiting fufu')
        fufu_rect = self.env.detection_definitions.get_fufu_rect()
        ratio_threshold = self.env.detection_definitions.get_fufu_blank_ratio_threshold()
        while True:
            screenshot = self._get_screenshot_impl()
            fufu_area = np.sum(screenshot[fufu_rect.y1:fufu_rect.y2, fufu_rect.x1:fufu_rect.x2, :3], -1)
            ratio = np.average(fufu_area < self.env.detection_definitions.get_fufu_blank_binarization_threshold())
            logger.debug(f'Wait fufu debug: mean: {np.mean(fufu_area)}, ratio: {ratio} (threshold: {ratio_threshold})')
            if ratio < ratio_threshold:
                break
            sleep(0.2)
        sleep(1)
        logger.debug(f'Ended waiting fufu, waited {time() - begin_timing:.2f} sec(s)')
        return self.forward_state


class SingleClickHandler(StateHandler):
    def __init__(self, env: ScriptEnv, forward_state: FgoState, x: int, y: int, t_before_click: float = 0,
                 t_after_click: float = 1):
        super(SingleClickHandler, self).__init__(env, forward_state)
        self.x = x
        self.y = y
        self.t_before_click = t_before_click
        self.t_after_click = t_after_click

    def run_and_transit_state(self) -> FgoState:
        if self.t_before_click > 0:
            sleep(self.t_before_click)
        self.env.attacher.send_click(self.x, self.y)
        if self.t_after_click > 0:
            sleep(self.t_after_click)
        return self.forward_state


class SingleClickAndWaitFufuHandler(SingleClickHandler):
    def run_and_transit_state(self) -> FgoState:
        next_state = super(SingleClickAndWaitFufuHandler, self).run_and_transit_state()
        return WaitFufuStateHandler(self.env, next_state).run_and_transit_state()
