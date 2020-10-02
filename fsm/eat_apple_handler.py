from .state_handler import ConfigurableStateHandler, WaitFufuStateHandler
from attacher import AbstractAttacher
from cv_positioning import *
import numpy as np
import logging
from click_positioning import *
from time import sleep
from image_process import imread, mean_gray_diff_err
from .fgo_state import FgoState
from battle_control import ScriptConfiguration, EatAppleType

logger = logging.getLogger('bgo_script.fsm')


class EatAppleHandler(ConfigurableStateHandler):
    _eat_apple_ui_anchor = imread(CV_EAT_APPLE_UI_FILE)

    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        if self.is_in_eat_apple_ui(screenshot):
            if self._cfg.eat_apple_type == EatAppleType.GoldApple:
                # TODO: validate this behavior
                logger.info('Performing action: eat apple')
                self.attacher.send_click(EAT_APPLE_CLICK_X, EAT_APPLE_CLICK_Y)
                sleep(0.5)
                self.attacher.send_click(EAT_APPLE_CONFIRM_CLICK_X, EAT_APPLE_CONFIRM_CLICK_Y)
                sleep(0.5)
                # WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
                return WaitFufuStateHandler(self.attacher, self.forward_state).run_and_transit_state()
            elif self._cfg.eat_apple_type == EatAppleType.DontEatMyApple:
                logger.warning('AP is not enough to enter quest, exit')
                self.attacher.send_click(CANCEL_EAT_APPLE_BUTTON_X, CANCEL_EAT_APPLE_BUTTON_Y)
                sleep(0.5)
                return FgoState.STATE_FINISH
            else:
                logger.critical('Not implemented EatAppleType: %s' % str(self._cfg.eat_apple_type))
                return FgoState.STATE_ERROR
        else:
            logger.debug('Eat apple scene not presented, operation skipped')
            return self.forward_state

    @classmethod
    def is_in_eat_apple_ui(cls, img: np.ndarray):
        v = mean_gray_diff_err(cls._eat_apple_ui_anchor, img)
        logger.debug('DEBUG value: mean_gray_diff_err = %f' % v)
        return v < 3
