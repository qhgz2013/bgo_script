from fsm.state_handler import StateHandler, WaitFufuStateHandler
import numpy as np
import logging
from time import sleep
import image_process
from fsm.fgo_state import FgoState
from bgo_game import ScriptEnv, APRecoveryItemType

logger = logging.getLogger('bgo_script.fsm')

__all__ = ['EatAppleHandler']


class EatAppleHandler(StateHandler):
    _eat_apple_ui_anchor = None
    __warned_eat_saint_quartz = False

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super().__init__(env, forward_state)
        cls = type(self)
        if cls._eat_apple_ui_anchor is None:
            cls._eat_apple_ui_anchor = image_process.imread(self.env.detection_definitions.get_eat_apple_ui_file())
        self._y_mapper = {
            APRecoveryItemType.GoldApple: self.env.click_definitions.eat_gold_apple(),
            APRecoveryItemType.SilverApple: self.env.click_definitions.eat_silver_apple(),
            APRecoveryItemType.SaintQuartz: self.env.click_definitions.eat_saint_quartz(),
            APRecoveryItemType.BronzeSapling: self.env.click_definitions.eat_bronze_sapling()
            # TODO: implement bronze apple
        }

    def run_and_transit_state(self) -> FgoState:
        screenshot = self._get_screenshot_impl()
        if self.is_in_eat_apple_ui(screenshot):
            if self.env.ap_recovery_item_type == APRecoveryItemType.DontEatMyApple:
                logger.warning('AP is not enough to enter quest, exit')
                button = self.env.click_definitions.eat_apple_cancel()
                self.env.attacher.send_click(button.x, button.y)
                sleep(0.5)
                return FgoState.STATE_FINISH
            else:
                if self.env.ap_recovery_item_type == APRecoveryItemType.SaintQuartz \
                        and not self.__warned_eat_saint_quartz:
                    self.__warned_eat_saint_quartz = True
                    logger.warning('You are using saint quartz for ap recovery')
                logger.info('Performing action: ap recovery')
                click = self._y_mapper[self.env.ap_recovery_item_type]
                self.env.attacher.send_click(click.x, click.y)
                sleep(0.5)
                confirm = self.env.click_definitions.eat_apple_confirm()
                self.env.attacher.send_click(confirm.x, confirm.y)
                sleep(2)
                return WaitFufuStateHandler(self.env, self.forward_state).run_and_transit_state()
        else:
            logger.debug('Eat apple scene not presented, operation skipped')
            return self.forward_state

    def is_in_eat_apple_ui(self, img: np.ndarray):
        rect = self.env.detection_definitions.get_eat_apple_ui_rect()
        img = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        v = image_process.mean_gray_diff_err(self._eat_apple_ui_anchor, img)
        threshold = 5  # TODO: change this hard-coded value
        logger.debug(f'is_in_eat_apple_ui: diff: {v}, threshold: {threshold}')
        return v < threshold
