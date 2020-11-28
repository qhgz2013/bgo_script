from .state_handler import ConfigurableStateHandler, WaitFufuStateHandler
from attacher import AbstractAttacher
from typing import *
from cv_positioning import *
from .fgo_state import FgoState
from time import sleep
import image_process
import numpy as np
import logging
import os
from battle_control import ScriptConfiguration
from .battle_seq_executor import BattleSequenceExecutor

logger = logging.getLogger('bgo_script.fsm')


def _handle_digits(battle_digit_dir: str):
    files = os.listdir(battle_digit_dir)
    digit_dict = {}
    for file in files:
        file_no_ext, _ = os.path.splitext(file)
        img = image_process.imread(os.path.join(battle_digit_dir, file))
        if len(img.shape) == 3:
            img = np.mean(img, -1)
        digit_dict[int(file_no_ext)] = img
    return digit_dict


class EnterQuestHandler(ConfigurableStateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> FgoState:
        executor = BattleSequenceExecutor(self.attacher, self._cfg)
        self._cfg.DO_NOT_MODIFY_BATTLE_VARS['EXECUTOR_INSTANCE'] = executor
        return WaitFufuStateHandler(self.attacher, self.forward_state).run_and_transit_state()


class WaitAttackOrExitQuestHandler(ConfigurableStateHandler):
    _attack_button_anchor = image_process.imread(CV_ATTACK_BUTTON_ANCHOR)

    def __init__(self, attacher: AbstractAttacher, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher

    def run_and_transit_state(self) -> FgoState:
        while True:
            sleep(0.2)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)[..., :3]
            gray = np.mean(img, -1)
            blank_val = np.mean(np.less(gray, CV_IN_BATTLE_BLANK_SCREEN_THRESHOLD))
            logger.debug('DEBUG VALUE: blank ratio: %f' % blank_val)
            # skip blank screen frame
            if blank_val >= CV_IN_BATTLE_BLANK_SCREEN_RATIO:
                continue
            if self._can_attack(gray):
                return FgoState.STATE_BATTLE_LOOP_ATK
            if self._is_exit_quest_scene(img):
                self._cfg.DO_NOT_MODIFY_BATTLE_VARS['BATTLE_LOOP_NEXT_STATE'] = FgoState.STATE_EXIT_QUEST
                self._cfg.DO_NOT_MODIFY_BATTLE_VARS['SGN_BATTLE_STATE_CHANGED'].set()
                return FgoState.STATE_EXIT_QUEST

    def _can_attack(self, img: np.ndarray) -> bool:
        btn_area = img[CV_ATTACK_BUTTON_Y1:CV_ATTACK_BUTTON_Y2, CV_ATTACK_BUTTON_X1:CV_ATTACK_BUTTON_X2]
        abs_gray_diff = image_process.mean_gray_diff_err(btn_area, self._attack_button_anchor)
        logger.debug('DEBUG value: attack button mean_gray_diff_err = %f' % abs_gray_diff)
        return abs_gray_diff < CV_ATTACK_DIFF_THRESHOLD

    @staticmethod
    def _is_exit_quest_scene(img: np.ndarray) -> bool:
        img = img[CV_EXIT_QUEST_Y1:CV_EXIT_QUEST_Y2, CV_EXIT_QUEST_X1:CV_EXIT_QUEST_X2, :].copy()
        h, w = img.shape[:2]
        img[int(h*CV_EXIT_QUEST_TITLE_MASK_Y1):int(h*CV_EXIT_QUEST_TITLE_MASK_Y2),
            int(w*CV_EXIT_QUEST_TITLE_MASK_X1):int(w*CV_EXIT_QUEST_TITLE_MASK_Y2), :] = 0
        for i in range(len(CV_EXIT_QUEST_SERVANT_MASK_X1S)):
            img[int(h*CV_EXIT_QUEST_SERVANT_MASK_Y1):int(h*CV_EXIT_QUEST_SERVANT_MASK_Y2),
                int(w*CV_EXIT_QUEST_SERVANT_MASK_X1S[i]):int(w*CV_EXIT_QUEST_SERVANT_MASK_X2S[i]), :] = 0
        gray = np.mean(img, -1) < CV_EXIT_QUEST_GRAY_THRESHOLD
        ratio = np.mean(gray)
        logger.debug('DEBUG value: exit quest gray ratio: %f' % ratio)
        return ratio >= CV_EXIT_QUEST_GRAY_RATIO_THRESHOLD


class BattleLoopAttackHandler(ConfigurableStateHandler):
    _battle_digits = _handle_digits(CV_BATTLE_DIGIT_DIRECTORY)

    def __init__(self, attacher: AbstractAttacher, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher

    def _digit_recognize(self, digit_img: np.ndarray) -> int:
        min_digit = None
        min_error = float('inf')
        for candidate_digit in self._battle_digits:
            abs_err = np.mean(np.abs(digit_img.astype(np.float) - self._battle_digits[candidate_digit]))
            if abs_err < min_error:
                min_error = abs_err
                min_digit = candidate_digit
        return min_digit

    def _get_current_battle(self, img: np.ndarray) -> Tuple[int, int]:
        img = img[CV_BATTLE_DETECTION_Y1:CV_BATTLE_DETECTION_Y2, CV_BATTLE_DETECTION_X1:CV_BATTLE_DETECTION_X2, :]
        s = np.greater(image_process.rgb_to_hsv(img)[..., 2], CV_BATTLE_DIGIT_THRESHOLD)
        s = s.astype('uint8') * 255
        # split digits
        rects = image_process.split_image(s)
        # re-order based on x position
        cx = [(x[1] + x[3]) / 2 for x in rects]
        rects = [x[1] for x in sorted(zip(cx, rects), key=lambda t: t[0])
                 if x[1][-1] > CV_BATTLE_FILTER_PIXEL_THRESHOLD]
        logger.debug('Digit rects: %s' % str(rects))
        if len(rects) != 3:
            logger.warning('Detected %d rects, it is incorrect' % len(rects))
        # TODO: add rough shape check
        assert len(rects) == 3, 'Current implementation must meet that # of battles less than 10,' \
                                ' or maybe recognition corrupted'
        return self._digit_recognize(self._normalize_image(s, rects[0], [20, 10])), \
            self._digit_recognize(self._normalize_image(s, rects[-1], [20, 10]))

    @staticmethod
    def _normalize_image(img: np.ndarray, rect: List[int], target_size: List[int]) -> np.ndarray:
        crop_img = img[rect[0]:rect[2], rect[1]:rect[3]]
        resized_img = image_process.resize(crop_img, target_size[1]-2, target_size[0]-2)
        extended_img = np.zeros([target_size[0], target_size[1]], dtype=crop_img.dtype)
        extended_img[1:-1, 1:-1] = resized_img
        return extended_img

    def run_and_transit_state(self) -> FgoState:
        var = self._cfg.DO_NOT_MODIFY_BATTLE_VARS
        if not var['SKIP_QUEST_INFO_DETECTION']:
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)[..., :3]
            cur_battle, max_battle = self._get_current_battle(img)
            if cur_battle != var['CURRENT_BATTLE']:
                var['TURN'] = 1  # reset turn
            else:
                var['TURN'] += 1
            var['CURRENT_BATTLE'], var['MAX_BATTLE'] = cur_battle, max_battle
            logger.info('Battle: %d / %d, Turn: %d' % (cur_battle, max_battle, var['TURN']))

        # transfer execution to controller
        var['BATTLE_LOOP_NEXT_STATE'] = FgoState.STATE_BATTLE_LOOP_ATK
        var['SGN_BATTLE_STATE_CHANGED'].set()
        # BattleController will be executed here!
        # once SGN_BATTLE_STATE_CHANGED is set, BattleSequenceExecutor will call corresponding BattleController to
        # perform user-defined actions (using skills, attacks, NPs, etc), until SGN_WAIT_STATE_TRANSITION is set by the
        # executor to transfer control back to the FSM.
        sgn = var['SGN_WAIT_STATE_TRANSITION']
        logger.debug('Wait SGN_WAIT_STATE_TRANSITION')
        sgn.wait()
        sgn.clear()
        return FgoState.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT
