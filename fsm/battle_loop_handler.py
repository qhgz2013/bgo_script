from .state_handler import StateHandler
from attacher import AbstractAttacher
from typing import *
from cv_positioning import *
from click_positioning import *
from time import time, sleep
import image_process
import numpy as np
from logging import root
import os
from matcher import ServantCommandCardMatcher
from team_config import FgoTeamConfiguration
from battle_action import FgoBattleAction
from util import mean_gray_diff_err


# DFS segmentation, original implemented in file fgo_detection.ipynb
def dfs_image(img_binary, x, y, visited, rect, group_idx=1):
    assert group_idx != 0
    if img_binary[y, x] < 128 or visited[y, x] != 0:
        return False
    # rect: in (y1, x1, y2, x2) formatted
    if y < rect[0]:
        rect[0] = y
    if y+1 > rect[2]:
        rect[2] = y+1
    if x < rect[1]:
        rect[1] = x
    if x+1 > rect[3]:
        rect[3] = x+1

    visited[y, x] = group_idx
    rect[4] = rect[4] + 1

    if y > 0 and visited[y-1, x] == 0:
        # up
        dfs_image(img_binary, x, y-1, visited, rect, group_idx)
    if y < img_binary.shape[0] - 1 and visited[y+1, x] == 0:
        # down
        dfs_image(img_binary, x, y+1, visited, rect, group_idx)
    if x > 0 and visited[y, x-1] == 0:
        # left
        dfs_image(img_binary, x-1, y, visited, rect, group_idx)
    if x < img_binary.shape[1] - 1 and visited[y, x+1] == 0:
        # right
        dfs_image(img_binary, x+1, y, visited, rect, group_idx)


_card_type_mapper = {1: 'Buster', 2: 'Quick', 3: 'Arts'}


class BattleLoopHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int, team_preset: FgoTeamConfiguration,
                 battle_loop_callback: Callable[[int, int, List[int], List[int], List[int],
                                                 FgoTeamConfiguration, FgoBattleAction], None], battle_digit_dir: str):
        self.attacher = attacher
        self.forward_state = forward_state
        self.battle_loop_callback = battle_loop_callback
        self._attack_button_anchor = np.mean(image_process.imread(CV_ATTACK_BUTTON_ANCHOR), -1)
        self._attack_button_mask = self._generate_attack_button_mask()
        self._attack_button_mask_available_pixel = np.sum(self._attack_button_mask)
        self._battle_digit_dir = battle_digit_dir
        self._battle_digits = self._handle_digits()
        self._servant_matcher = ServantCommandCardMatcher(CV_FGO_DATABASE_FILE)
        self.team_preset = team_preset
        self._current_turn_command_card_id = []
        self._current_turn_command_card_type = []
        self._current_turn_command_card_critical_star = []
        self._command_card_type_anchor = [image_process.imread(x) for x in CV_COMMAND_CARD_TYPE_FILES]

    @staticmethod
    def _generate_attack_button_mask() -> np.ndarray:
        dx = int(CV_SCREENSHOT_RESOLUTION_X * (CV_ATTACK_BUTTON_X2 - CV_ATTACK_BUTTON_X1))
        dy = int(CV_SCREENSHOT_RESOLUTION_Y * (CV_ATTACK_BUTTON_Y2 - CV_ATTACK_BUTTON_Y1))
        d = min(dx, dy)
        cx = dx / 2
        cy = dy / 2
        y, x = np.ogrid[:dx, :dy]
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - 5
        mask = r < (d / 2)
        return mask

    def _handle_digits(self):
        files = os.listdir(self._battle_digit_dir)
        digit_dict = {}
        for file in files:
            file_no_ext, _ = os.path.splitext(file)
            img = image_process.imread(os.path.join(self._battle_digit_dir, file))
            if len(img.shape) == 3:
                img = np.mean(img, -1)
            digit_dict[int(file_no_ext)] = img
        return digit_dict

    def _digit_recognize(self, digit_img: np.ndarray) -> int:
        min_digit = None
        min_error = float('inf')
        for candidate_digit in self._battle_digits:
            abs_err = np.mean(np.abs(digit_img.astype(np.float) - self._battle_digits[candidate_digit]))
            if abs_err < min_error:
                min_error = abs_err
                min_digit = candidate_digit
        return min_digit

    def run_and_transit_state(self) -> int:
        turn = 1
        last_battle = None
        action = FgoBattleAction(self.team_preset, self._apply_click_sequence, self._apply_command_card_changes)
        while True:
            if not self._wait_can_attack_or_exit_quest():
                return self.forward_state
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            battle, max_battle = self._get_current_battle(img)
            if last_battle is None or last_battle != battle:
                turn = 1  # Reset turn accumulator if battle changed
                last_battle = battle
            root.info('Detected quest info: Battle: %d / %d, Turn: %d' % (battle, max_battle, turn))
            self._apply_command_card_changes()
            action.reset()
            # do callback
            try:
                self.battle_loop_callback(battle, turn, self._current_turn_command_card_type,
                                          self._current_turn_command_card_id,
                                          self._current_turn_command_card_critical_star, self.team_preset, action)
            except Exception as ex:
                root.error('Error while calling callback function: %s' % str(ex), exc_info=ex)
                exit(1)
            sleep(1)
            turn += 1

    def _apply_command_card_changes(self):
        sleep(0.5)
        self.attacher.send_click(ATTACK_BUTTON_X, ATTACK_BUTTON_Y)
        sleep(0.5)
        img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        new_servant_id, new_card_type = self._get_command_card_info(img)
        self._current_turn_command_card_id.clear()
        self._current_turn_command_card_id.extend(new_servant_id)
        self._current_turn_command_card_type.clear()
        self._current_turn_command_card_type.extend(new_card_type)
        self._current_turn_command_card_critical_star.clear()
        self.attacher.send_click(ATTACK_BACK_BUTTON_X, ATTACK_BACK_BUTTON_Y)
        sleep(0.5)
        # implement critical star detection

    def _apply_click_sequence(self, click_sequence):
        for t, click_pos in click_sequence:
            if t == -1:
                if not self._wait_can_attack_or_exit_quest():
                    root.info('Unexpected exit quest state detected! Exit battle loop')
                    break
            elif t > 0:
                sleep(t)
            if click_pos is not None:
                x, y = click_pos
                self.attacher.send_click(x, y)

    def _can_attack(self, img: np.ndarray) -> bool:
        btn_area = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y1):
                       int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y2),
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X1):
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X2)]
        abs_gray_diff = np.abs(btn_area - self._attack_button_anchor)
        mean_abs_gray_diff = np.sum(abs_gray_diff * self._attack_button_mask) / \
            self._attack_button_mask_available_pixel / 255
        return mean_abs_gray_diff < CV_ATTACK_DIFF_THRESHOLD

    def _get_current_battle(self, img: np.ndarray) -> Tuple[int, int]:
        battle_ocr = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_BATTLE_DETECTION_Y1):
                         int(CV_SCREENSHOT_RESOLUTION_Y*CV_BATTLE_DETECTION_Y2),
                         int(CV_SCREENSHOT_RESOLUTION_X*CV_BATTLE_DETECTION_X1):
                         int(CV_SCREENSHOT_RESOLUTION_X*CV_BATTLE_DETECTION_X2), :]
        s = image_process.rgb_to_hsv(battle_ocr)[..., 2] > 128  # THRESHOLD
        s = s.astype('uint8') * 255
        # simplest digit recognition, directly applying subtraction and compare the difference
        # split digits, DFS based
        v = np.zeros_like(s, 'uint8')
        cnt = 1
        rects = []
        for y in range(s.shape[0]):
            for x in range(s.shape[1]):
                if s[y, x] > 127 and v[y, x] == 0:
                    rect = [y, x, y+1, x+1, 1]
                    dfs_image(s, x, y, v, rect, cnt)
                    rects.append(rect)
                    cnt += 1
        # re-order based on x position
        cx = [(x[1] + x[2]) / 2 for x in rects]
        rects = [x[1] for x in sorted(zip(cx, rects), key=lambda t: t[0]) if x[1][-1] > CV_BATTLE_FILTER_PIXEL_THRESHOLD]
        # root.info('Digit recognition rects: %s' % str(rects))
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

    @staticmethod
    def _save_img(img, fname):
        if len(img.shape) == 2:
            new_img = np.zeros([img.shape[0], img.shape[1], 3], 'uint8')
            for i in range(3):
                new_img[..., i] = img
            img = new_img
        import skimage.io
        skimage.io.imsave(fname, img)

    def _get_command_card_info(self, img: np.ndarray) -> Tuple[List[int], List[int]]:
        # 从者头像与指令卡的padding: Top 25px, Left 40px, Right 40px, Bottom 14px
        # 缩放比到时候根据指令卡边框大小算就ok
        t = time()
        servant_ids = []
        card_types = []
        for x1, x2 in zip(CV_COMMAND_CARD_X1S, CV_COMMAND_CARD_X2S):
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_COMMAND_CARD_Y):,
                               int(CV_SCREENSHOT_RESOLUTION_X*x1):int(CV_SCREENSHOT_RESOLUTION_X*x2), :]
            card_type = 0
            target_err = float('inf')
            y_offset = 0
            for idx, (command_card_type, offset) in enumerate(zip(self._command_card_type_anchor,
                                                                  CV_COMMAND_CARD_TYPE_OFFSET)):
                score = np.empty(30, np.float)
                h = command_card_type.shape[0]
                for i in range(30):
                    score[i] = mean_gray_diff_err(command_card[75+i:75+i+h, ...], command_card_type, None)
                min_score = np.min(score)
                if min_score < target_err:
                    card_type = idx
                    target_err = min_score
                    y_offset = (75 + np.argmin(score)) / CV_SCREENSHOT_RESOLUTION_Y - offset + CV_COMMAND_CARD_Y
            # y_offset = np.argmax(score)
            # Extend pixels
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y*(y_offset-0.03472)):
                               int(CV_SCREENSHOT_RESOLUTION_Y*(y_offset+0.01945+CV_COMMAND_CARD_HEIGHT)),
                               int(CV_SCREENSHOT_RESOLUTION_X*(x1-0.03125)):
                               int(CV_SCREENSHOT_RESOLUTION_X*(x2+0.03125)), :]
            # import matplotlib.pyplot as plt
            # plt.figure()
            # plt.imshow(command_card)
            # plt.show()
            servant_id = self._servant_matcher.match(command_card)
            servant_ids.append(servant_id)
            card_types.append(card_type + 1)
        root.info('Detected command card data: Servant: %s, Type: %s (used %f sec(s))' %
                  (str(servant_ids), str([_card_type_mapper[x] for x in card_types]), time() - t))
        return servant_ids, card_types

    @staticmethod
    def _is_exit_quest_scene(img: np.ndarray) -> bool:
        img = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_EXIT_QUEST_Y1):int(CV_SCREENSHOT_RESOLUTION_Y*CV_EXIT_QUEST_Y2),
                  int(CV_SCREENSHOT_RESOLUTION_X*CV_EXIT_QUEST_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_EXIT_QUEST_X2), :]
        img = img.copy()
        h, w = img.shape[:2]
        img[int(h*CV_EXIT_QUEST_TITLE_MASK_Y1):int(h*CV_EXIT_QUEST_TITLE_MASK_Y2),
            int(w*CV_EXIT_QUEST_TITLE_MASK_X1):int(w*CV_EXIT_QUEST_TITLE_MASK_Y2), :] = 0
        for i in range(len(CV_EXIT_QUEST_SERVANT_MASK_X1S)):
            img[int(h*CV_EXIT_QUEST_SERVANT_MASK_Y1):int(h*CV_EXIT_QUEST_SERVANT_MASK_Y2),
                int(w*CV_EXIT_QUEST_SERVANT_MASK_X1S[i]):int(w*CV_EXIT_QUEST_SERVANT_MASK_X2S[i]), :] = 0
        gray = np.mean(img, -1) < CV_EXIT_QUEST_GRAY_THRESHOLD
        return np.mean(gray) >= CV_EXIT_QUEST_GRAY_RATIO_THRESHOLD

    def _wait_can_attack_or_exit_quest(self) -> bool:
        t = time()
        try:
            while True:
                sleep(0.2)
                img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
                gray = np.mean(img, -1)
                blank_val = np.mean(np.less(gray, CV_IN_BATTLE_BLANK_SCREEN_THRESHOLD))
                # skip blank screen frame
                if blank_val >= CV_IN_BATTLE_BLANK_SCREEN_RATIO:
                    continue
                if self._can_attack(gray):
                    return True
                if self._is_exit_quest_scene(img):
                    return False
        finally:
            root.info('Wait attack or exit quest: waited %f sec(s)' % (time() - t))
