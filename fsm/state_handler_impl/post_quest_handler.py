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
        cls = type(self)
        if cls._support_anchor is None:
            cls._support_anchor = image_process.imread(self.env.detection_definitions.get_request_support_ui_file())

    def _is_in_requesting_friend_ui(self) -> bool:
        img = self._get_screenshot_impl()
        if img.shape[0] != self._support_anchor.shape[0]:
            raise ValueError(f'The height of anchor image {self._support_anchor.shape[0]} does not match the image '
                             f'returned by capturer: {img.shape[0]}')
        if img.shape[1] > self._support_anchor.shape[1]:
            width_diff_half = (img.shape[1] - self._support_anchor.shape[1]) // 2
            # for other resolutions with ratio > 16 / 9
            img = img[:, width_diff_half:width_diff_half+self._support_anchor.shape[1], ...]
        elif img.shape[1] < self._support_anchor.shape[1]:
            # this situation should be handled by capturer (ratio < 16 / 9)
            raise ValueError(f'{self.__class__.__name__} currently does not support image with shape {img.shape}')
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
        cls = type(self)
        if cls._anchor is None:
            cls._anchor = image_process.imread(
                self.env.detection_definitions.get_continuous_battle_ui_file())

    def _is_in_continuous_battle_confirm_ui(self) -> bool:
        img = self._get_screenshot_impl()
        rect = self.env.detection_definitions.get_continuous_battle_ui_rect()
        img_in_rect = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        v = image_process.mean_gray_diff_err(self._anchor, img_in_rect)
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
