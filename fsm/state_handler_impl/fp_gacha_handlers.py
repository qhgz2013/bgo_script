from ..fgo_state import FgoState
from ..state_handler import StateHandler, WaitFufuStateHandler
from bgo_game import ScriptEnv
from time import sleep
from logging import getLogger
import image_process
import numpy as np

__all__ = ['CheckFriendPointGachaUIHandler', 'FriendPointGachaConfirmHandler', 'FriendPointGachaSkipHandler',
           'FriendPointGachaItemOverflowHandler']

logger = getLogger('bgo_script.fsm')


def _check_fp_usage_is_active(img: np.ndarray, env: ScriptEnv) -> bool:
    rect = env.detection_definitions.get_fp_active_rect()
    img = np.mean(img[rect.y1:rect.y2, rect.x1:rect.x2, :].astype(np.float32), -1)
    img_bin = np.greater_equal(img, env.detection_definitions.get_fp_active_gray_threshold())
    value = np.mean(img_bin)
    logger.debug(f'check_fp_usage_is_active: {value}, threshold: {env.detection_definitions.get_fp_active_gray_ratio_threshold()}')
    return value >= env.detection_definitions.get_fp_active_gray_ratio_threshold()


class CheckFriendPointGachaUIHandler(StateHandler):
    _anchor_file = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super(CheckFriendPointGachaUIHandler, self).__init__(env, forward_state)
        if self._anchor_file is None:
            self._anchor_file = image_process.imread(self.env.detection_definitions.get_fp_pool_ui_file())

    def run_and_transit_state(self) -> FgoState:
        img = self._get_screenshot_impl()
        # step 1: check anchor
        anchor_rect = self.env.detection_definitions.get_fp_pool_ui_rect()
        img_in_anchor = img[anchor_rect.y1:anchor_rect.y2, anchor_rect.x1:anchor_rect.x2, :]
        diff = image_process.mean_gray_diff_err(img_in_anchor, self._anchor_file)
        if diff > self.env.detection_definitions.get_fp_pool_ui_diff_threshold():
            logger.error('Friend point gacha UI not detected.')
            return FgoState.STATE_ERROR

        # step 2: double-check friend point is active (highlighted at the top of summon UI)
        if not _check_fp_usage_is_active(img, self.env):
            logger.error('Friend point gacha UI check failed: FP is not using')
            return FgoState.STATE_ERROR

        # all check passed: click gacha button and wait confirm
        button = self.env.click_definitions.fp_pool_gacha()
        self.env.attacher.send_click(button.x, button.y)

        # wait 0.5s
        sleep(0.5)
        return self.forward_state


class FriendPointGachaConfirmHandler(StateHandler):
    _anchor_file = None
    _fp_item_overflow_file = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super(FriendPointGachaConfirmHandler, self).__init__(env, forward_state)
        if self._anchor_file is None:
            self._anchor_file = image_process.imread(self.env.detection_definitions.get_fp_pool_gacha_confirm_file())
        if self._fp_item_overflow_file is None:
            self._fp_item_overflow_file = \
                image_process.imread(self.env.detection_definitions.get_fp_item_overflow_file())

    def run_and_transit_state(self) -> FgoState:
        img = self._get_screenshot_impl()
        anchor_rect = self.env.detection_definitions.get_fp_pool_gacha_confirm_rect()
        img_in_anchor = img[anchor_rect.y1:anchor_rect.y2, anchor_rect.x1:anchor_rect.x2, :]
        diff = image_process.mean_gray_diff_err(img_in_anchor, self._anchor_file)
        if diff > self.env.detection_definitions.get_fp_pool_gacha_confirm_diff_threshold():
            # check if item overflow
            overflow_rect = self.env.detection_definitions.get_fp_item_overflow_rect()
            img_in_anchor = img[overflow_rect.y1:overflow_rect.y2, overflow_rect.x1:overflow_rect.x2, :]
            diff = image_process.mean_gray_diff_err(img_in_anchor, self._fp_item_overflow_file)
            if diff > self.env.detection_definitions.get_fp_pool_gacha_confirm_diff_threshold():
                logger.error('Friend point gacha confirm UI check failed')
                return FgoState.STATE_ERROR
            else:
                return FgoState.STATE_FP_GACHA_ITEM_OVERFLOW

        # click confirm button
        button = self.env.click_definitions.fp_pool_gacha_confirm()
        self.env.attacher.send_click(button.x, button.y)

        # wait 0.5s
        sleep(0.5)

        # wait fufu
        wait_fufu_handler = WaitFufuStateHandler(self.env, self.forward_state)
        return wait_fufu_handler.run_and_transit_state()


class FriendPointGachaSkipHandler(StateHandler):
    _anchor_file = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super(FriendPointGachaSkipHandler, self).__init__(env, forward_state)
        if self._anchor_file is None:
            self._anchor_file = image_process.imread(self.env.detection_definitions.get_fp_pool_gacha_skip_diff_file())

    def run_and_transit_state(self) -> FgoState:
        click_point = self.env.click_definitions.fp_pool_gacha_skip_click()
        rect = self.env.detection_definitions.get_fp_pool_gacha_skip_check_button_rect()

        while True:
            img = self._get_screenshot_impl()

            img_in_rect = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
            diff = image_process.mean_gray_diff_err(img_in_rect, self._anchor_file)
            logger.debug(f'diff: {diff}')
            if diff >= self.env.detection_definitions.get_fp_pool_gacha_skip_diff_threshold():
                sleep(0.5)
                self.env.attacher.send_click(click_point.x, click_point.y)
                continue

            # check
            if not _check_fp_usage_is_active(img, self.env):
                logger.error('Friend point gacha UI check failed: FP is not using')
                return FgoState.STATE_ERROR

            sleep(0.5)
            continue_button = self.env.click_definitions.fp_pool_continuous_gacha()
            self.env.attacher.send_click(continue_button.x, continue_button.y)
            sleep(0.3)
            return self.forward_state


class FriendPointGachaItemOverflowHandler(StateHandler):
    # NOTE: forward_state is not used here, it uses 2 pre-defined conditional branches:
    # STATE_FP_GACHA_ITEM_OVERFLOW_SVT and STATE_FP_GACHA_ITEM_OVERFLOW_CE

    def run_and_transit_state(self) -> FgoState:
        synthesis_button = self.env.click_definitions.fp_overflow_synthesis()
        self.env.attacher.send_click(synthesis_button.x, synthesis_button.y)

        sleep(1)
        # the screen will blank for a while, don't know how long it is (at least 3 seconds)
        WaitFufuStateHandler(self.env, FgoState.STATE_FINISH).run_and_transit_state()
        sleep(1)

        rect = self.env.detection_definitions.get_craft_essence_synthesis_ui_rect()
        img = self._get_screenshot_impl()
        img = img[rect.y1:rect.y2, rect.x1:rect.x2, :]
        img = np.mean(img.astype(np.float32), -1)
        img_bin = img <= self.env.detection_definitions.get_craft_essence_synthesis_ui_gray_threshold()
        if np.mean(img_bin) >= self.env.detection_definitions.get_craft_essence_synthesis_ui_gray_ratio_threshold():
            return FgoState.STATE_FP_GACHA_ITEM_OVERFLOW_CE
        else:
            return FgoState.STATE_FP_GACHA_ITEM_OVERFLOW_SVT