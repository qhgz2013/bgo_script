from ..state_handler import WaitFufuStateHandler, StateHandler
from typing import *
from fsm.fgo_state import FgoState
from time import sleep
import image_process
import numpy as np
import logging
from util import DigitRecognizer
from bgo_game import ScriptEnv
from fsm.battle_seq_executor import BattleSequenceExecutor

logger = logging.getLogger('bgo_script.fsm')

__all__ = ['EnterQuestHandler', 'WaitAttackOrExitQuestHandler', 'BattleLoopAttackHandler']


class EnterQuestHandler(StateHandler):
    def run_and_transit_state(self) -> FgoState:
        executor = BattleSequenceExecutor(self.env, self.env.runtime_var_store)
        self.env.runtime_var_store['EXECUTOR_INSTANCE'] = executor
        return WaitFufuStateHandler(self.env, self.forward_state).run_and_transit_state()


class WaitAttackOrExitQuestHandler(StateHandler):
    _attack_button_anchor = None
    _exit_quest_img = None

    def __init__(self, env: ScriptEnv):
        super().__init__(env, forward_state=FgoState.STATE_BATTLE_LOOP_ATK)
        cls = type(self)
        if cls._attack_button_anchor is None:
            cls._attack_button_anchor = [image_process.imread(file) for file in
                                         self.env.detection_definitions.get_attack_button_anchor_file()]
        if cls._exit_quest_img is None:
            cls._exit_quest_img = image_process.imread(self.env.detection_definitions.get_exit_quest_ui_file())

    def run_and_transit_state(self) -> FgoState:
        blank_threshold = self.env.detection_definitions.get_in_battle_blank_screen_threshold()
        blank_ratio = self.env.detection_definitions.get_in_battle_blank_screen_ratio_threshold()
        while True:
            sleep(0.2)
            img = self._get_screenshot_impl()[..., :3]
            gray = np.mean(img, -1)
            blank_val = np.mean(np.less(gray, blank_threshold))
            logger.debug(f'DEBUG value: blank_ratio: {blank_val}, threshold: {blank_ratio} '
                         f'(binarization threshold: {blank_threshold})')
            # skip blank screen frame
            if blank_val >= blank_ratio:
                continue
            if self._can_attack(gray):
                return FgoState.STATE_BATTLE_LOOP_ATK
            if self._is_exit_quest_scene(img):
                self.env.runtime_var_store['BATTLE_LOOP_NEXT_STATE'] = FgoState.STATE_EXIT_QUEST
                self.env.runtime_var_store['SGN_BATTLE_STATE_CHANGED'].set()
                return FgoState.STATE_EXIT_QUEST

    def _can_attack(self, img: np.ndarray) -> bool:
        button_rect = self.env.detection_definitions.get_attack_button_rect()
        btn_area = img[button_rect.y1:button_rect.y2, button_rect.x1:button_rect.x2]
        abs_gray_diff = [image_process.mean_gray_diff_err(btn_area, anchor) for anchor in self._attack_button_anchor]
        threshold = self.env.detection_definitions.get_attack_button_diff_threshold()
        logger.debug(f'DEBUG value: attack button abs_gray_diff_err: {abs_gray_diff}, threshold: {threshold}')
        return any(diff < threshold for diff in abs_gray_diff)

    def _is_exit_quest_scene(self, img: np.ndarray) -> bool:
        exit_quest_rect = self.env.detection_definitions.get_exit_quest_rect()
        img = img[exit_quest_rect.y1:exit_quest_rect.y2, exit_quest_rect.x1:exit_quest_rect.x2, :].copy()
        diff = image_process.mean_gray_diff_err(img, self._exit_quest_img)
        threshold = self.env.detection_definitions.get_exit_quest_diff_threshold()
        logger.debug(f'DEBUG value: exit_quest_diff: {diff}, threshold: {threshold}')
        return diff < threshold


class BattleLoopAttackHandler(StateHandler):

    def __init__(self, env: ScriptEnv):
        super().__init__(env, forward_state=FgoState.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT)
        self._digit_recognizer = DigitRecognizer(self.env.detection_definitions.get_battle_digit_dir())

    def _get_current_battle(self, img: np.ndarray) -> Tuple[int, int]:
        battle_digit_rect = self.env.detection_definitions.get_battle_digit_rect()
        img = img[battle_digit_rect.y1:battle_digit_rect.y2, battle_digit_rect.x1:battle_digit_rect.x2, :]
        threshold = self.env.detection_definitions.get_battle_digit_threshold()
        s = np.greater(image_process.rgb_to_hsv(img)[..., 2], threshold)
        s = s.astype('uint8') * 255
        # split digits
        rects = image_process.split_image(s)
        # re-order based on x position
        cx = [(x.min_x + x.max_x) / 2 for x in rects]
        pixel_threshold = self.env.detection_definitions.get_battle_filter_pixel_threshold()
        rects_filtered = [x[1] for x in sorted(zip(cx, rects), key=lambda t: t[0])
                          if x[1].associated_pixels.shape[0] > pixel_threshold]
        logger.debug(f'Digit rects: {rects_filtered} (before filter: {rects})')
        if len(rects) != 3:
            logger.warning(f'Detected {len(rects)} rects, it is incorrect')
        # TODO [PRIOR: low]: add rough shape check
        assert len(rects) == 3, 'Current implementation must meet that # of battles less than 10,' \
                                ' or maybe recognition corrupted'
        return self._digit_recognizer.recognize(rects[0].get_image_segment()), \
            self._digit_recognizer.recognize(rects[-1].get_image_segment())

    def run_and_transit_state(self) -> FgoState:
        var = self.env.runtime_var_store
        if not var['SKIP_QUEST_INFO_DETECTION']:
            img = self._get_screenshot_impl()[..., :3]
            cur_battle, max_battle, e = None, None, None
            for _ in range(5):
                try:
                    cur_battle, max_battle = self._get_current_battle(img)
                    break
                except AssertionError as e:
                    sleep(0.2)  # failed in some time, let's have another retry
            if cur_battle is None:
                raise ValueError('Could not determine battle status') from e
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
        exc = var['DELEGATE_THREAD_EXCEPTION']
        if exc is not None:
            # re-raise exception which is raised in delegate thread
            raise exc
        return FgoState.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT
