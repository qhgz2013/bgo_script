from .state_handler import StateHandler
from attacher import AbstractAttacher
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
from logging import root
from typing import List, Optional, Tuple, Callable, Union
from cv_positioning import *
from click_positioning import *
import image_process
import numpy as np
from time import sleep, time
from .wait_fufu_handler import WaitFufuStateHandler
from util import mean_gray_diff_err


# TODO: multiple support configuration support
class SelectSupportHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int, support_servant_id: int,
                 support_craft_essence_id: int, support_craft_essence_max_break: bool = False,
                 support_servant_minimal_skill: Optional[List[int]] = None):
        self.attacher = attacher
        self.forward_state = forward_state
        self.servant_id = support_servant_id
        self.craft_essence_id = support_craft_essence_id
        self.craft_essence_max_break = support_craft_essence_max_break
        self.servant_skill = support_servant_minimal_skill or [0, 0, 0]
        self.servant_matcher = SupportServantMatcher(CV_FGO_DATABASE_FILE)
        self.craft_essence_matcher = SupportCraftEssenceMatcher(CV_FGO_DATABASE_FILE)
        self._support_empty_img = image_process.imread(CV_SUPPORT_EMPTY_FILE)
        self._support_craft_essence_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_FILE)
        self._support_max_break_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_FILE)

    def run_and_transit_state(self) -> int:
        suc = False
        while True:
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            support_range = self._split_support_image(img)
            servant_ids = self.match_servant(img, support_range)
            if self.craft_essence_id > 0:
                craft_essence_ids = self.match_craft_essence(img, support_range)
            else:
                craft_essence_ids = []
            for i in range(len(servant_ids)):
                if servant_ids[i][0] == self.servant_id and \
                        (self.craft_essence_id == 0 or craft_essence_ids[i][0] == self.craft_essence_id) and \
                        (not self.craft_essence_max_break or craft_essence_ids[i][1]):
                    # servant matched
                    root.info('Found required support')
                    self.attacher.send_click(0.5, (support_range[i][0] + support_range[i][1]) / 2)
                    sleep(0.5)
                    suc = True
                    break
            if suc:
                break
            _, end_pos = self._get_scrollbar_pos(img)
            if end_pos < 0.99:
                self._action_scroll_down()
            else:
                self.refresh_support()
        sleep(1)
        return self.forward_state

    def _action_scroll_down(self):
        root.info('scrolling down')
        self.attacher.send_slide((0.5, 0.9), (0.5, 0.9 - SUPPORT_SCROLLDOWN_Y))
        sleep(1.5)

    @staticmethod
    def _split_support_image(img: np.ndarray) -> List[Tuple[float, float]]:
        part = img[:, int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_X2), :]
        hsv = image_process.rgb_to_hsv(part)
        # check the saturation value
        score = np.median(hsv[..., 1], -1)
        # two-stage detection
        stage1_valid = np.logical_and(score >= CV_SUPPORT_S_STAGE1_LO, score < CV_SUPPORT_S_STAGE1_HI)
        stage2_valid = np.logical_and(score >= CV_SUPPORT_S_STAGE2_LO, score < CV_SUPPORT_S_STAGE2_HI)
        y = 0
        range_list = []
        while y < CV_SCREENSHOT_RESOLUTION_Y:
            while y < CV_SCREENSHOT_RESOLUTION_Y and not stage1_valid[y]:
                y += 1
            if y == CV_SCREENSHOT_RESOLUTION_Y:
                break
            begin_s1_y = y
            while y < CV_SCREENSHOT_RESOLUTION_Y and stage1_valid[y]:
                y += 1
            end_s1_y = y
            s1_len = end_s1_y - begin_s1_y
            if s1_len < CV_SUPPORT_STAGE1_LEN:
                continue
            # STAGE 1 -> STAGE 2 is not continuous some time, here uses a look-ahead tolerance solution within 5 px
            begin_s2_y = y
            lookahead_y = y
            while lookahead_y < CV_SCREENSHOT_RESOLUTION_Y:
                if not stage2_valid[lookahead_y]:
                    if lookahead_y - end_s1_y < 5:
                        begin_s2_y = lookahead_y + 1
                    else:
                        break
                lookahead_y += 1
            if begin_s2_y - end_s1_y >= 5:
                continue
            end_s2_y = lookahead_y
            s2_len = end_s2_y - begin_s2_y
            if s2_len < CV_SUPPORT_STAGE2_LEN:
                continue
            # amend detection result
            range_list.append((begin_s1_y / CV_SCREENSHOT_RESOLUTION_Y - 0.0111111,
                               end_s2_y / CV_SCREENSHOT_RESOLUTION_Y +
                               (0.025 if s1_len < CV_SUPPORT_STAGE1_LEN2 else 0.0111111)))
        root.info('support detection result: %s' % str(range_list))
        return range_list

    @staticmethod
    def _get_scrollbar_pos(img: np.ndarray) -> Tuple[float, float]:
        scrollbar = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_SCROLLBAR_Y1):
                        int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_SCROLLBAR_Y2),
                        int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SCROLLBAR_X1):
                        int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SCROLLBAR_X2), :]
        score = np.mean(np.mean(scrollbar, -1), -1) < CV_SUPPORT_BAR_GRAY_THRESHOLD
        start_y, end_y = 0, 0
        for y in range(score.shape[0]):
            if not score[y]:
                start_y = y
                break
        for y in range(start_y, score.shape[0]):
            if score[y]:
                break
            end_y = y
        return start_y / score.shape[0], end_y / score.shape[0]

    def refresh_support(self):
        root.info('Refreshing support')
        sleep(0.5)
        self.attacher.send_click(SUPPORT_REFRESH_BUTTON_X, SUPPORT_REFRESH_BUTTON_Y)
        sleep(1)
        self.attacher.send_click(SUPPORT_REFRESH_BUTTON_CONFIRM_X, SUPPORT_REFRESH_BUTTON_CONFIRM_Y)
        sleep(1)
        WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        sleep(0.5)

    def match_servant(self, img: np.ndarray, range_list: List[Tuple[float, float]]) -> List[Tuple[int, List[int]]]:
        def _empty_check(img1, img2):
            return mean_gray_diff_err(image_process.resize(img1, img2.shape[1], img2.shape[0]), img2)
        ret, t = self._wrap_call_matcher(self.servant_matcher.match, _empty_check, img, self._support_empty_img,
                                         range_list)
        root.info('Detected support servant ID: %s (used %f sec(s))' % (str(ret), t))
        # TODO: implement skill level detection here (replacing [0, 0, 0])
        return [(x, [0, 0, 0]) for x in ret]

    def match_craft_essence(self, img: np.ndarray, range_list: List[Tuple[float, float]]) -> List[Tuple[int, bool]]:
        def _empty_check(img1, img2):
            img1_h = int(img2.shape[1] / img1.shape[1] * img1.shape[0])
            img1 = image_process.resize(img1, img2.shape[1], img1_h)
            img1 = img1[-img2.shape[0]:, ...]
            return mean_gray_diff_err(img1, img2)
        ret, t = self._wrap_call_matcher(self.craft_essence_matcher.match, _empty_check, img,
                                         self._support_craft_essence_img, range_list)
        root.info('Detected support craft essence ID: %s (used %f sec(s))' % (str(ret), t))
        t = time()
        # detect craft essence max break state
        max_break = []
        for y1, y2 in range_list:
            icon = img[int(CV_SCREENSHOT_RESOLUTION_Y*y1):int(CV_SCREENSHOT_RESOLUTION_Y*y2),
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SERVANT_X1):
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SERVANT_X2), :]
            icon = icon[-24:-4, 133:153, :]
            icon = image_process.resize(icon, self._support_max_break_img.shape[1],
                                        self._support_max_break_img.shape[0])
            max_break.append(mean_gray_diff_err(icon, self._support_max_break_img))
        root.info('Detected support craft essence max break state: %s (used %f sec(s))' % (str(max_break), time() - t))
        return list(zip(ret, max_break))

    @staticmethod
    def _wrap_call_matcher(func: Callable[[np.ndarray], int],
                           empty_check_func: Callable[[np.ndarray, np.ndarray], bool],
                           img: np.ndarray, empty_img: Union[np.ndarray, None],
                           range_list: List[Tuple[float, float]]) -> Tuple[List[int], float]:
        x1 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X1)
        x2 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X2)
        t = time()
        ret = []
        for y1, y2 in range_list:
            icon = img[int(CV_SCREENSHOT_RESOLUTION_Y*y1):int(CV_SCREENSHOT_RESOLUTION_Y*y2), x1:x2, :]
            if empty_img is not None and empty_check_func(icon, empty_img):
                ret.append(0)
            else:
                ret.append(func(icon))
        return ret, time() - t