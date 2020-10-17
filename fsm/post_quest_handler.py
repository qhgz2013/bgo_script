from .state_handler import StateHandler, WaitFufuStateHandler, ConfigurableStateHandler
from attacher import AbstractAttacher
from click_positioning import *
from time import sleep
import image_process
from cv_positioning import *
from image_process import mean_gray_diff_err
import logging
from battle_control import ScriptConfiguration
from .fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')


def _imread_to_screen_size(path):
    return image_process.resize(image_process.imread(path), CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)


class ExitQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState):
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        for _ in range(7):
            self.attacher.send_click(BATTLE_EXIT_BUTTON_X, BATTLE_EXIT_BUTTON_Y)
            sleep(0.5)
        return WaitFufuStateHandler(self.attacher, self.forward_state).run_and_transit_state()


class FriendUIHandler(StateHandler):
    _support_anchor = _imread_to_screen_size(CV_REQUEST_SUPPORT_UI_FILE)

    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState):
        self.attacher = attacher
        self.forward_state = forward_state

    def _is_in_requesting_friend_ui(self) -> bool:
        img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        val = mean_gray_diff_err(image_process.resize(img, self._support_anchor.shape[1],
                                                      self._support_anchor.shape[0]), self._support_anchor)
        logger.debug('DEBUG value friend_ui mean_gray_diff_err = %f' % val)
        return val < 10

    def run_and_transit_state(self) -> FgoState:
        # 检查并跳过发送好友申请界面（用于选择非好友助战但好友未满时的情况）
        if self._is_in_requesting_friend_ui():
            logger.info('Detected friend request UI, skipped')
            self.attacher.send_click(SUPPORT_REQUEST_BUTTON_SKIP_X, SUPPORT_REQUEST_BUTTON_Y)
            sleep(2)
            return WaitFufuStateHandler(self.attacher, self.forward_state).run_and_transit_state()
        return self.forward_state


class ContinuousBattleHandler(ConfigurableStateHandler):
    _anchor = _imread_to_screen_size(CV_CONTINUOUS_BATTLE_UI_FILE)

    def __init__(self, attacher: AbstractAttacher, forward_state_pos: FgoState, forward_state_neg: FgoState,
                 cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state_pos = forward_state_pos
        self.forward_state_neg = forward_state_neg

    def _is_in_continuous_battle_confirm_ui(self) -> bool:
        img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        v = image_process.mean_gray_diff_err(self._anchor, img)
        logger.debug('DEBUG value: is_in_continuous_battle_confirm_ui mean_gray_diff_err = %f' % v)
        return v < 10

    def run_and_transit_state(self) -> FgoState:
        if self._cfg.enable_continuous_battle:
            if self._is_in_continuous_battle_confirm_ui():
                logger.debug('Enable continuous battle')
                self.attacher.send_click(CONTINUOUS_BATTLE_BUTTON_CONFIRM_X, CONTINUOUS_BATTLE_BUTTON_Y)
                next_state = WaitFufuStateHandler(self.attacher, self.forward_state_pos).run_and_transit_state()
            else:
                logger.error('Continuous battle scene not detected, assume quest is exited')
                self.attacher.send_click(CONTINUOUS_BATTLE_BUTTON_CANCEL_X, CONTINUOUS_BATTLE_BUTTON_Y)
                next_state = self.forward_state_neg
        else:
            self.attacher.send_click(CONTINUOUS_BATTLE_BUTTON_CANCEL_X, CONTINUOUS_BATTLE_BUTTON_Y)
            next_state = self.forward_state_neg
        sleep(0.5)
        return next_state
