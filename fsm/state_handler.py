__all__ = ['StateHandler', 'ConfigurableStateHandler', 'WaitFufuStateHandler', 'DirectStateForwarder',
           'SingleClickHandler', 'SingleClickAndWaitFufuHandler']
from abc import ABC
from bgo_game import ScriptConfig
from .fgo_state import FgoState
from attacher import CombinedAttacher
from time import sleep, time
import logging
from cv_positioning import *
import numpy as np

logger = logging.getLogger('bgo_script.fsm')


class StateHandler:
    def run_and_transit_state(self) -> FgoState:
        raise NotImplementedError()


class ConfigurableStateHandler(StateHandler, ABC):
    def __init__(self, cfg: ScriptConfig):
        self._cfg = cfg


class DirectStateForwarder(StateHandler):
    def __init__(self, forward_state: FgoState):
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        return self.forward_state


class WaitFufuStateHandler(StateHandler):
    def __init__(self, attacher: CombinedAttacher, forward_state: FgoState):
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        begin_timing = time()
        logger.debug('Started waiting fufu')
        while True:
            screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            fufu_area = np.sum(screenshot[CV_FUFU_Y1:CV_FUFU_Y2, CV_FUFU_X1:CV_FUFU_X2, :3], -1)
            ratio = np.average(fufu_area < CV_FUFU_BLANK_THRESHOLD)
            if ratio < CV_FUFU_BLANK_RATIO_THRESHOLD:
                break
            sleep(0.2)
        sleep(1)
        logger.debug('Ended waiting fufu, waited %f sec(s)' % (time() - begin_timing))
        return self.forward_state


class SingleClickHandler(StateHandler):
    def __init__(self, attacher: CombinedAttacher, x: float, y: float, next_state: FgoState, t_before_click: float = 0,
                 t_after_click: float = 1):
        self.attacher = attacher
        self.x = x
        self.y = y
        self.next_state = next_state
        self.t_before_click = t_before_click
        self.t_after_click = t_after_click

    def run_and_transit_state(self) -> FgoState:
        if self.t_before_click > 0:
            sleep(self.t_before_click)
        self.attacher.send_click(self.x, self.y)
        if self.t_after_click > 0:
            sleep(self.t_after_click)
        return self.next_state


class SingleClickAndWaitFufuHandler(StateHandler):
    def __init__(self, attacher: CombinedAttacher, x: float, y: float, next_state: FgoState, t_before_click: float = 0):
        self.attacher = attacher
        self._click_handler = SingleClickHandler(attacher, x, y, next_state, t_before_click)

    def run_and_transit_state(self) -> FgoState:
        next_state = self._click_handler.run_and_transit_state()
        return WaitFufuStateHandler(self.attacher, next_state).run_and_transit_state()
