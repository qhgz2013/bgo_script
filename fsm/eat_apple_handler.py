from .state_handler import ConfigurableStateHandler, WaitFufuStateHandler
from attacher import AbstractAttacher
from cv_positioning import *
import numpy as np
import logging
from click_positioning import *
from time import sleep
import image_process
from .fgo_state import FgoState
from bgo_game import ScriptConfig, EatAppleType

logger = logging.getLogger('bgo_script.fsm')


def _imread_to_screen_size(path):
    return image_process.resize(image_process.imread(path), CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)


class EatAppleHandler(ConfigurableStateHandler):
    _eat_apple_ui_anchor = _imread_to_screen_size(CV_EAT_APPLE_UI_FILE)
    _y_mapper = {EatAppleType.GoldApple: EAT_GOLD_APPLE_CLICK_Y, EatAppleType.SilverApple: EAT_SILVER_APPLE_CLICK_Y,
                 EatAppleType.BronzeApple: EAT_BRONZE_APPLE_CLICK_Y, EatAppleType.SaintQuartz: EAT_SAINT_QUARTZ_CLICK_Y}
    __warned_eat_saint_quartz = False

    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState, cfg: ScriptConfig):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        if self.is_in_eat_apple_ui(screenshot):
            if self._cfg.eat_apple_type == EatAppleType.DontEatMyApple:
                logger.warning('AP is not enough to enter quest, exit')
                self.attacher.send_click(CANCEL_EAT_APPLE_BUTTON_X, CANCEL_EAT_APPLE_BUTTON_Y)
                sleep(0.5)
                return FgoState.STATE_FINISH
            else:
                if self._cfg.eat_apple_type == EatAppleType.SaintQuartz and not self.__warned_eat_saint_quartz:
                    self.__warned_eat_saint_quartz = True
                    logger.warning('You are using saint quartz for ap recovery')
                logger.info('Performing action: ap recovery')
                self.attacher.send_click(EAT_APPLE_CLICK_X, self._y_mapper[self._cfg.eat_apple_type])
                sleep(0.5)
                self.attacher.send_click(EAT_APPLE_CONFIRM_CLICK_X, EAT_APPLE_CONFIRM_CLICK_Y)
                sleep(2)
                return WaitFufuStateHandler(self.attacher, self.forward_state).run_and_transit_state()
        else:
            logger.debug('Eat apple scene not presented, operation skipped')
            return self.forward_state

    @classmethod
    def is_in_eat_apple_ui(cls, img: np.ndarray):
        v = image_process.mean_gray_diff_err(cls._eat_apple_ui_anchor, img)
        logger.debug('DEBUG value: mean_gray_diff_err = %f' % v)
        return v < 3
