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


_card_type_mapper = {1: 'Buster (1)', 2: 'Quick (2)', 3: 'Arts (3)'}


class BattleLoopHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int, battle_loop_callback: Callable,
                 battle_digit_dir: str):
        self.attacher = attacher
        self.forward_state = forward_state
        self.battle_loop_callback = battle_loop_callback
        self._attack_button_anchor = np.mean(image_process.imread(CV_ATTACK_BUTTON_ANCHOR), -1)
        self._attack_button_mask = self._generate_attack_button_mask()
        self._attack_button_mask_available_pixel = np.sum(self._attack_button_mask)
        self._battle_digit_dir = battle_digit_dir
        self._battle_digits = self._handle_digits()
        self._servant_matcher = ServantCommandCardMatcher(CV_FGO_DATABASE_FILE)

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
        while True:
            if not self._wait_can_attack_or_exit_quest():
                return self.forward_state
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            battle, max_battle = self._get_current_battle(img)
            root.info('Detected quest info: Battle: %d / %d, Turn: %d' % (battle, max_battle, turn))
            sleep(0.5)
            self.attacher.send_click((CV_ATTACK_BUTTON_X1 + CV_ATTACK_BUTTON_X2) / 2,
                                     (CV_ATTACK_BUTTON_Y1 + CV_ATTACK_BUTTON_Y2) / 2)
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            command_card_data = self._get_command_card_info(img)
            # do callback
            sleep(1)
            turn += 1

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
        s = image_process.rgb_to_hsv(battle_ocr)[..., 1] < 12  # THRESHOLD
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
        rects = [x[1] for x in sorted(zip(cx, rects), key=lambda t: t[0]) if x[1][-1] > 20]  # filter out obj < 20 px
        root.info('Digit recognition rects: %s' % str(rects))
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
        import matplotlib.pyplot as plt
        t = time()
        servant_ids = []
        card_types = []
        for x1, x2 in zip(CV_COMMAND_CARD_X1S, CV_COMMAND_CARD_X2S):
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_COMMAND_CARD_Y):,
                               int(CV_SCREENSHOT_RESOLUTION_X*x1):int(CV_SCREENSHOT_RESOLUTION_X*x2), :]
            h = image_process.rgb_to_hsv(command_card)[..., 0]
            score = np.logical_and(h >= CV_COMMAND_CARD_TOP_BORDER_H_LO, h < CV_COMMAND_CARD_TOP_BORDER_H_HI)
            score = np.mean(score, -1)[:int(0.1*command_card.shape[0])]
            y_offset = np.argmax(score)
            # command_card = command_card[y_offset:y_offset+int(CV_SCREENSHOT_RESOLUTION_Y*CV_COMMAND_CARD_HEIGHT), ...]
            # Extend pixels
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y*(CV_COMMAND_CARD_Y-0.03472))+y_offset:
                               int(CV_SCREENSHOT_RESOLUTION_Y*(CV_COMMAND_CARD_Y+CV_COMMAND_CARD_HEIGHT+0.01945))
                               + y_offset,
                               int(CV_SCREENSHOT_RESOLUTION_X*(x1-0.03125)):
                               int(CV_SCREENSHOT_RESOLUTION_X*(x2+0.03125)), :]
            servant_id, card_type = self._servant_matcher.match(command_card)
            servant_ids.append(servant_id)
            card_types.append(card_type + 1)
            # plt.figure()
            # plt.imshow(command_card)
            # plt.show()
        root.info('Detected command card data: Servant: %s, Type: %s (used %f sec(s))' %
                  (str(servant_ids), str([_card_type_mapper[x] for x in card_types]), time() - t))
        return servant_ids, card_types

    def _is_exit_quest_scene(self, img: np.ndarray) -> bool:
        pass

    def _wait_can_attack_or_exit_quest(self) -> bool:
        t = time()
        try:
            while True:
                img = np.mean(self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y), -1)
                if self._can_attack(img):
                    return True
                if self._is_exit_quest_scene(img):
                    return False
                sleep(0.2)
        finally:
            root.info('Wait attack or exit quest: waited %f sec(s)' % (time() - t))
