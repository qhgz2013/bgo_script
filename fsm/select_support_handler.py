from .state_handler import ConfigurableStateHandler, WaitFufuStateHandler
from attacher import *
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
import logging
from typing import *
from cv_positioning import *
from click_positioning import *
import image_process
import numpy as np
from time import sleep, time
from image_process import mean_gray_diff_err
from bgo_game import ScriptConfig, ServantConfig
from .fgo_state import FgoState
from util import DigitRecognizer


logger = logging.getLogger('bgo_script.fsm')


# NOT implemented: NP level detection
class SupportServant(ServantConfig):
    def __init__(self, svt_id: int, craft_essence_id: int, craft_essence_max_break: bool = False,
                 is_friend: bool = False, skill_level: Optional[List[Optional[int]]] = None, np_lv: int = 0):
        super().__init__(svt_id)
        self.craft_essence_id = craft_essence_id
        self.craft_essence_max_break = craft_essence_max_break
        self.is_friend = is_friend
        self.skill_level = skill_level
        self.np_lv = np_lv

    def __repr__(self):
        s = '<SupportServant for svt: %d and craft essence: %d' % (self.svt_id, self.craft_essence_id)
        attr = []
        if self.craft_essence_max_break:
            attr.append('max break')
        if self.is_friend:
            attr.append('friend')
        if self.skill_level:
            attr.append('skill: %s' % str(self.skill_level))
        attr_str = ', '.join(attr)
        s += (' (%s)' % attr_str) if len(attr_str) > 0 else ''
        return s + '>'


class SelectSupportHandler(ConfigurableStateHandler):
    _support_empty_img = image_process.imread(CV_SUPPORT_EMPTY_FILE)
    _support_craft_essence_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_FILE)
    _support_craft_essence_img2 = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_FILE2)
    _support_craft_essence_img_resized = None  # assigned in run-time, resized _support_max_break_img
    _support_max_break_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_FILE)

    servant_matcher = SupportServantMatcher(CV_FGO_DATABASE_FILE)
    craft_essence_matcher = SupportCraftEssenceMatcher(CV_FGO_DATABASE_FILE)

    def __init__(self, attacher: CombinedAttacher, forward_state: FgoState, cfg: ScriptConfig):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state
        self._support_svt = self._cfg.team_config.support_servant
        # noinspection PyTypeChecker
        self._scroll_down_y = SUPPORT_SCROLLDOWN_Y_MUMU
        self._digit_recognizer = DigitRecognizer(CV_SUPPORT_SKILL_DIGIT_DIR)

    def run_and_transit_state(self) -> FgoState:
        suc = False
        while True:
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)[..., :3]
            support_range = self._split_support_image(img)
            svt_data = self.match_support_servant(img, support_range)
            for i in range(len(svt_data)):
                if self._check_config(svt_data[i]):
                    # servant matched
                    logger.info('Found required support')
                    self.attacher.send_click(0.5, (support_range[i][0] + support_range[i][1]) /
                                             2 / CV_SCREENSHOT_RESOLUTION_Y)
                    sleep(0.5)
                    suc = True
                    break
            if suc:
                break
            _, end_pos = self._get_scrollbar_pos(img)
            if 0.01 <= end_pos < 0.99:
                self._action_scroll_down()
            else:
                self.refresh_support()
        sleep(1)
        return self.forward_state

    def _check_config(self, detected_svt: SupportServant):
        required_svt = self._support_svt
        if required_svt is None:
            raise ValueError('Support servant is not configured in current team configuration')
        # servant match
        if required_svt.svt_id != 0 and self._support_svt.svt_id != detected_svt.svt_id:
            return False
        # friend match
        if required_svt.friend_only and (not detected_svt.is_friend):
            return False
        # skill level match
        if required_svt.skill_requirement is not None:
            required_skill = required_svt.skill_requirement
            detected_skill = detected_svt.skill_level
            for i in range(3):
                if required_skill[i] is None:
                    continue
                if detected_skill[i] is None or detected_skill[i] < required_skill[i]:
                    return False
        # multiple craft essence configuration support
        for craft_essence_cfg in required_svt.craft_essence_cfg:
            # if one of the config is satisfied, then return true
            craft_essence_id_matched = \
                craft_essence_cfg.id == 0 or craft_essence_cfg.id == detected_svt.craft_essence_id
            craft_essence_max_break_matched = (not craft_essence_cfg.max_break) or detected_svt.craft_essence_max_break
            craft_essence_matched = craft_essence_id_matched and craft_essence_max_break_matched
            if craft_essence_matched:
                return True
        return False

    def _action_scroll_down(self):
        logger.info('scrolling down')
        self.attacher.send_slide((0.5, 0.9), (0.5, 0.9 - self._scroll_down_y))
        sleep(1.5)

    @classmethod
    def _split_support_image(cls, img: np.ndarray) -> List[Tuple[int, int]]:
        # new detection result begins here
        part = img[:, CV_SUPPORT_DETECT_X1:CV_SUPPORT_DETECT_X2, :]
        gray = np.mean(part, axis=2)
        avg = np.mean(gray, axis=1)
        td = np.zeros_like(avg)
        td[:-CV_SUPPORT_TD_PIXEL] = avg[:-CV_SUPPORT_TD_PIXEL] - avg[CV_SUPPORT_TD_PIXEL:]
        # logger.debug('support split: temporal differentiate array:\n%s' % str(td))
        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.plot(td)
        # plt.show()
        y = 150
        range_list = []
        threshold = CV_SUPPORT_DETECT_DIFF_THRESHOLD
        # TODO [PRIOR: nice-to-have]: 修改为支持多段合并的识别模式（对上升沿和下降沿分别进行匹配）
        while y < CV_SCREENSHOT_RESOLUTION_Y:
            while y < CV_SCREENSHOT_RESOLUTION_Y and td[y] > -threshold:
                y += 1
            while y < CV_SCREENSHOT_RESOLUTION_Y and td[y] < -threshold:
                y += 1
            begin_y = y - 1
            while y < CV_SCREENSHOT_RESOLUTION_Y and td[y] < threshold:
                y += 1
            while y < CV_SCREENSHOT_RESOLUTION_Y and td[y] > threshold:
                y += 1
            end_y = y - 1
            if y == CV_SCREENSHOT_RESOLUTION_Y:
                break
            len_y = end_y - begin_y
            if CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_LO <= len_y <= CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_HI:
                range_list.append((begin_y, end_y))
                logger.debug('support detection: %d -> %d (len = %d)' % (begin_y, end_y, end_y-begin_y))
            else:
                logger.debug('support detection: %d -> %d (len = %d) (ignored)' % (begin_y, end_y, end_y-begin_y))
        return range_list

    @staticmethod
    def _get_scrollbar_pos(img: np.ndarray) -> Tuple[float, float]:
        scrollbar = img[CV_SUPPORT_SCROLLBAR_Y1:CV_SUPPORT_SCROLLBAR_Y2,
                        CV_SUPPORT_SCROLLBAR_X1:CV_SUPPORT_SCROLLBAR_X2, :]
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
        start_y /= score.shape[0]
        end_y /= score.shape[0]
        logger.debug('Scrollbar position: %f -> %f' % (start_y, end_y))
        return start_y, end_y

    def refresh_support(self):
        logger.info('Refreshing support')
        while True:
            sleep(0.5)
            self.attacher.send_click(SUPPORT_REFRESH_BUTTON_X, SUPPORT_REFRESH_BUTTON_Y)
            sleep(0.5)
            # Check clickable
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            img = image_process.rgb_to_hsv(img[..., :3])[
                  CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y1:CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y2,
                  CV_SUPPORT_REFRESH_REFUSED_DETECTION_X1:CV_SUPPORT_REFRESH_REFUSED_DETECTION_X2, 1]
            if np.mean(img) < CV_SUPPORT_REFRESH_REFUSED_DETECTION_S_THRESHOLD:
                self.attacher.send_click(SUPPORT_REFRESH_REFUSED_CONFIRM_X, SUPPORT_REFRESH_REFUSED_CONFIRM_Y)
                logger.info('Could not refresh support temporarily, retry in 5 secs')
                sleep(5)
            else:
                break
        sleep(0.5)
        self.attacher.send_click(SUPPORT_REFRESH_BUTTON_CONFIRM_X, SUPPORT_REFRESH_BUTTON_CONFIRM_Y)
        sleep(1)
        assert WaitFufuStateHandler(self.attacher, FgoState.STATE_BEGIN).run_and_transit_state() == FgoState.STATE_BEGIN
        sleep(0.5)

    def match_support_servant(self, img: np.ndarray, range_list: List[Tuple[int, int]]) -> List[SupportServant]:
        # match servant
        def _servant_empty_check(img1, img2):
            v = mean_gray_diff_err(image_process.resize(img1, img2.shape[1], img2.shape[0]), img2)
            logger.debug('DEBUG value: empty support servant check: mean_gray_diff_err = %f' % v)
            return v < 10
        svt_id, t = self._wrap_call_matcher(self.servant_matcher.match, _servant_empty_check, img,
                                            self._support_empty_img, range_list)
        logger.debug('Detected support servant ID: %s (used %f sec(s))' % (str(svt_id), t))

        # match craft essence
        def _craft_essence_empty_check(img1, img2):
            img1_h = int(img2.shape[1] / img1.shape[1] * img1.shape[0])
            img1 = image_process.resize(img1, img2.shape[1], img1_h)
            img1 = img1[-img2.shape[0]:, ...]
            v = mean_gray_diff_err(img1, img2)
            logger.debug('DEBUG value: empty support craft essence check: mean_gray_diff_err = %f' % v)
            return v < 10
        ce_id, t = self._wrap_call_matcher(self.craft_essence_matcher.match, _craft_essence_empty_check, img,
                                           [self._support_craft_essence_img, self._support_craft_essence_img2],
                                           range_list)
        logger.debug('Detected support craft essence ID: %s (used %f sec(s))' % (str(ce_id), t))
        ret_list = [SupportServant(x, y) for x, y in zip(svt_id, ce_id)]
        for i, (y1, y2) in enumerate(range_list):
            # detect craft essence max break state
            if ce_id[i] == 0:
                ret_list[i].craft_essence_max_break = False
            else:
                icon = img[y1:y2, CV_SUPPORT_SERVANT_X1:CV_SUPPORT_SERVANT_X2, :]
                icon = icon[CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y1:CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y2,
                            CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X1:CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X2, :]
                if self._support_craft_essence_img_resized is None:
                    # reduce unnecessary resize ops
                    anchor = image_process.resize(self._support_max_break_img, icon.shape[1], icon.shape[0])
                    self._support_craft_essence_img_resized = anchor
                else:
                    anchor = self._support_craft_essence_img_resized
                # err = mean_gray_diff_err(icon, anchor)
                hsv_err = image_process.mean_hsv_diff_err(icon, anchor)
                # logger.debug('DEBUG value: support craft essence max break check: gray_diff_err = %f, hsv_err = %f' %
                #              (err, hsv_err))
                ret_list[i].craft_essence_max_break = hsv_err < CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_THRESHOLD

            # skip when support servant is empty
            if svt_id[i] == 0:
                continue
            # detect friend state
            friend_img = img[y1+CV_SUPPORT_FRIEND_DETECT_Y1:y1+CV_SUPPORT_FRIEND_DETECT_Y2,
                             CV_SUPPORT_FRIEND_DETECT_X1:CV_SUPPORT_FRIEND_DETECT_X2, :]
            # omit B channel here
            friend_part_binary = np.greater_equal(np.mean(friend_img[..., :2], 2),
                                                  CV_SUPPORT_FRIEND_DISCRETE_THRESHOLD)
            is_friend = np.mean(friend_part_binary) > CV_SUPPORT_FRIEND_DETECT_THRESHOLD
            ret_list[i].is_friend = is_friend

            # skill level detection
            skill_img = img[y1+CV_SUPPORT_SKILL_BOX_OFFSET_Y:y1+CV_SUPPORT_SKILL_BOX_OFFSET_Y+CV_SUPPORT_SKILL_BOX_SIZE,
                            CV_SUPPORT_SKILL_BOX_OFFSET_X1:CV_SUPPORT_SKILL_BOX_OFFSET_X2, :3].copy()
            gray = np.mean(skill_img, -1)
            vertical_diff = np.zeros_like(gray, dtype=np.float32)
            step_size = CV_SUPPORT_SKILL_V_DIFF_STEP_SIZE  # pixel offset for computing abs difference
            vertical_diff[:-step_size, :] = np.abs(gray[:-step_size, :] - gray[step_size:, :])
            # just use the first several pixels and last several pixels to determine
            edge_size = CV_SUPPORT_SKILL_V_DIFF_EDGE_SIZE
            skills = []
            for j in range(3):
                begin_x = j * (CV_SUPPORT_SKILL_BOX_MARGIN_X + CV_SUPPORT_SKILL_BOX_SIZE)
                v_diff_current_skill = np.mean(vertical_diff[:, begin_x:begin_x+CV_SUPPORT_SKILL_BOX_SIZE], -1)
                max_v_diff = np.maximum(np.max(v_diff_current_skill[:edge_size]),
                                        np.max(v_diff_current_skill[-edge_size:]))
                logger.debug(f'DEBUG value: max_v_diff = {max_v_diff}')
                if max_v_diff > CV_SUPPORT_SKILL_V_DIFF_THRESHOLD:
                    # digit recognition, using SSIM metric, split by S (-> 0) and V (-> 255)
                    current_skill_img = skill_img[:, begin_x:begin_x + CV_SUPPORT_SKILL_BOX_SIZE, :]
                    hsv = image_process.rgb_to_hsv(current_skill_img).astype(np.float32)
                    img_digit_part = (1. - hsv[..., 1] / 255.) * (hsv[..., 2] / 255.)
                    img_digit_part = img_digit_part[30:, 3:30]
                    bin_digits = np.greater_equal(img_digit_part, CV_SUPPORT_SKILL_BINARIZATION_THRESHOLD)
                    digit_segments = image_process.split_image(bin_digits)
                    digits = []
                    for segment in sorted(digit_segments, key=lambda x: (x.max_x + x.min_x)):
                        if 50 < segment.associated_pixels.shape[0] < 150 \
                                and abs(segment.min_y + segment.max_y - 26) <= 3 \
                                and segment.max_x - segment.min_x < 14 <= segment.max_y - segment.min_y:
                            digits.append(self._digit_recognizer.recognize(segment.get_image_segment()))
                    if len(digits) == 2:
                        skill_lvl = digits[0] * 10 + digits[1]
                        if skill_lvl != 10:
                            logger.warning(f'Invalid 2 digits skill level: expected 10, but got {skill_lvl}, set to 10')
                            skill_lvl = 10
                    elif len(digits) == 0:
                        skill_lvl = None
                        logger.warning(f'Failed to detect skill level: no digit found (this mainly because of the low'
                                       f' resolution of screenshot)')
                    else:
                        skill_lvl = digits[0]
                        if skill_lvl == 0:
                            logger.warning(f'Invalid 1 digit skill level: expected 1~9, but got {skill_lvl}')
                    skills.append(skill_lvl)
                else:
                    # skill unavailable
                    skills.append(None)
            ret_list[i].skill_level = skills
        logger.info('Detected support servant info: %s' % str(ret_list))
        return ret_list

    @staticmethod
    def _wrap_call_matcher(func: Callable[[np.ndarray], int],
                           empty_check_func: Callable[[np.ndarray, np.ndarray], bool],
                           img: np.ndarray, empty_img: Optional[Union[np.ndarray, Sequence[np.ndarray]]],
                           range_list: List[Tuple[int, int]]) -> Tuple[List[int], float]:
        t = time()
        ret = []
        for y1, y2 in range_list:
            icon = img[y1:y2, CV_SUPPORT_SERVANT_X1:CV_SUPPORT_SERVANT_X2, :]
            if empty_img is not None:
                if isinstance(empty_img, np.ndarray):
                    empty_img = [empty_img]
                is_empty = False
                for img2 in empty_img:
                    if empty_check_func(icon, img2):
                        ret.append(0)
                        is_empty = True
                        break
                if not is_empty:
                    ret.append(func(icon))
        return ret, time() - t
