from ..state_handler import StateHandler, WaitFufuStateHandler
from time import sleep
import image_process
import logging
from bgo_game import ScriptEnv
from ..fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')

__all__ = ['ExitQuestHandler', 'FriendUIHandler', 'ContinuousBattleHandler']


class ExitQuestHandler(StateHandler):

    def run_and_transit_state(self) -> FgoState:
        button = self.env.click_definitions.exit_battle_button()
        for _ in range(7):
            self.env.attacher.send_click(button.x, button.y)
            sleep(0.5)
        return WaitFufuStateHandler(self.env, self.forward_state).run_and_transit_state()


class FriendUIHandler(StateHandler):
    _support_anchor = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super().__init__(env, forward_state)
        if self._support_anchor is None:
            resolution = self.env.detection_definitions.get_target_resolution()
            self._support_anchor = image_process.resize(image_process.imread(
                self.env.detection_definitions.get_request_support_ui_file()), resolution.width, resolution.height)

    def _is_in_requesting_friend_ui(self) -> bool:
        img = self._get_screenshot_impl()
        val = image_process.mean_gray_diff_err(image_process.resize(
            img, self._support_anchor.shape[1], self._support_anchor.shape[0]), self._support_anchor)
        logger.debug('DEBUG value friend_ui mean_gray_diff_err = %f' % val)
        return val < 15  # 10 is not enough: 10.914105

    def run_and_transit_state(self) -> FgoState:
        # 检查并跳过发送好友申请界面（用于选择非好友助战但好友未满时的情况）
        if self._is_in_requesting_friend_ui():
            logger.info('Detected friend request UI, skipped')
            skip_button = self.env.click_definitions.support_request_skip()
            self.env.attacher.send_click(skip_button.x, skip_button.y)
            sleep(2)
            return WaitFufuStateHandler(self.env, self.forward_state).run_and_transit_state()
        return self.forward_state


class ContinuousBattleHandler(StateHandler):
    _anchor = None

    def __init__(self, env: ScriptEnv, forward_state_pos: FgoState, forward_state_neg: FgoState):
        super().__init__(env, forward_state_pos)
        self.forward_state_pos = forward_state_pos
        self.forward_state_neg = forward_state_neg
        if self._anchor is None:
            resolution = self.env.detection_definitions.get_target_resolution()
            self._anchor = image_process.resize(image_process.imread(
                self.env.detection_definitions.get_continuous_battle_ui_file()), resolution.width, resolution.height)

    def _is_in_continuous_battle_confirm_ui(self) -> bool:
        img = self._get_screenshot_impl()
        v = image_process.mean_gray_diff_err(self._anchor, img)
        logger.debug('DEBUG value: is_in_continuous_battle_confirm_ui mean_gray_diff_err = %f' % v)
        return v < 10  # TODO: parameterize

    def run_and_transit_state(self) -> FgoState:
        cont_battle_confirm = self.env.click_definitions.continuous_battle_confirm()
        cont_battle_cancel = self.env.click_definitions.continuous_battle_cancel()
        if self.env.enable_continuous_battle:
            if self._is_in_continuous_battle_confirm_ui():
                logger.debug('Enable continuous battle')
                self.env.attacher.send_click(cont_battle_confirm.x, cont_battle_confirm.y)
                sleep(2)
                return WaitFufuStateHandler(self.env, self.forward_state_pos).run_and_transit_state()
            else:
                logger.error('Continuous battle scene not detected, assume quest is exited')
        self.env.attacher.send_click(cont_battle_cancel.x, cont_battle_cancel.y)
        sleep(1)
        return self.forward_state_neg
