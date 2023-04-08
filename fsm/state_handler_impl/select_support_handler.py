from ..state_handler import StateHandler, WaitFufuStateHandler
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
import logging
from typing import *
import image_process
import numpy as np
from time import sleep, time
from image_process import mean_gray_diff_err
from bgo_game import ScriptEnv, ServantConfig
from fsm.fgo_state import FgoState
from util import DigitRecognizer
from basic_class import PointF

logger = logging.getLogger('bgo_script.fsm')

__all__ = ['SelectSupportHandler']


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


class SelectSupportHandler(StateHandler):
    _support_empty_img = None
    _support_craft_essence_imgs = None
    _support_craft_essence_img_resized = None  # assigned in run-time, resized _support_max_break_img
    _support_max_break_img = None

    servant_matcher = None
    craft_essence_matcher = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super().__init__(env, forward_state)
        cls = type(self)
        self._support_svt = self.env.team_config.support_servant
        # noinspection PyTypeChecker
        self._scroll_down_y = self.env.click_definitions.support_scrolldown_y_mumu()
        self._digit_recognizer = DigitRecognizer(self.env.detection_definitions.get_support_skill_digit_dir())
        if cls._support_empty_img is None:
            cls._support_empty_img = image_process.imread(self.env.detection_definitions.get_support_empty_file())
        if cls._support_craft_essence_imgs is None:
            cls._support_craft_essence_imgs = [image_process.imread(x) for x in
                                               self.env.detection_definitions.get_support_empty_craft_essence_files()]
        if cls._support_max_break_img is None:
            cls._support_max_break_img = image_process.imread(self.env.detection_definitions.get_max_break_icon_file())
        if cls.servant_matcher is None:
            cls.servant_matcher = SupportServantMatcher(self.env.detection_definitions.get_database_file(), self.env)
        if cls.craft_essence_matcher is None:
            cls.craft_essence_matcher = SupportCraftEssenceMatcher(self.env.detection_definitions.get_database_file(),
                                                                   self.env)

    def run_and_transit_state(self) -> FgoState:
        suc = False
        resolution = self.env.detection_definitions.get_target_resolution()
        sleep(1)  # since the game may lag for a while after getting response
        while True:
            sleep(0.5)
            img = self._get_screenshot_impl()[..., :3]
            support_range = self._split_support_image(img)
            svt_data = self.match_support_servant(img, support_range)
            for i in range(len(svt_data)):
                if self._check_config(svt_data[i]):
                    # servant matched
                    logger.info('Found required support')
                    y = (support_range[i][0] + support_range[i][1]) / 2 / resolution.height
                    self.env.attacher.send_click(0.5, y)
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
        self.env.attacher.send_slide(PointF(0.5, 0.9), PointF(0.5, 0.9 - self._scroll_down_y))
        sleep(1.5)

    def _split_support_image(self, img: np.ndarray) -> List[Tuple[int, int]]:
        # new detection result begins here
        x1, x2 = self.env.detection_definitions.get_support_detection_x()
        part = img[:, x1:x2, :]
        gray = np.mean(part, axis=2)
        avg = np.mean(gray, axis=1)
        td = np.zeros_like(avg)
        grad_pixels = self.env.detection_definitions.get_support_detection_gray_grad_offset_pixel()
        td[:-grad_pixels] = avg[:-grad_pixels] - avg[grad_pixels:]
        # logger.debug('support split: temporal differentiate array:\n%s' % str(td))
        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.plot(td)
        # plt.show()
        y = 150
        range_list = []
        threshold = self.env.detection_definitions.get_support_detection_diff_threshold()
        # TODO [PRIOR: nice-to-have]: 修改为支持多段合并的识别模式（对上升沿和下降沿分别进行匹配）
        resolution = self.env.detection_definitions.get_target_resolution()
        y_len_lo, y_len_hi = self.env.detection_definitions.get_support_detection_y_len_threshold_range()
        while y < resolution.height:
            while y < resolution.height and td[y] > -threshold:
                y += 1
            while y < resolution.height and td[y] < -threshold:
                y += 1
            begin_y = y - 1
            while y < resolution.height and td[y] < threshold:
                y += 1
            while y < resolution.height and td[y] > threshold:
                y += 1
            end_y = y - 1
            if y == resolution.height:
                break
            len_y = end_y - begin_y
            if y_len_lo <= len_y <= y_len_hi:
                range_list.append((begin_y, end_y))
                logger.debug('support detection: %d -> %d (len = %d)' % (begin_y, end_y, end_y-begin_y))
            else:
                logger.debug('support detection: %d -> %d (len = %d) (ignored)' % (begin_y, end_y, end_y-begin_y))
        return range_list

    def _get_scrollbar_pos(self, img: np.ndarray) -> Tuple[float, float]:
        scrollbar_rect = self.env.detection_definitions.get_support_scrollbar_rect()
        scrollbar = img[scrollbar_rect.y1:scrollbar_rect.y2, scrollbar_rect.x1:scrollbar_rect.x2, :]
        score = np.mean(np.mean(scrollbar, -1), -1) < \
            self.env.detection_definitions.get_support_scrollbar_gray_threshold()
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
        refresh_button = self.env.click_definitions.support_refresh()
        refresh_refused_rect = self.env.detection_definitions.get_support_refresh_refused_detection_rect()
        refresh_refused_confirm = self.env.click_definitions.support_refresh_refused_confirm()
        refresh_confirm = self.env.click_definitions.support_refresh_confirm()
        while True:
            sleep(0.5)
            self.env.attacher.send_click(refresh_button.x, refresh_button.y)
            sleep(0.5)
            # Check clickable
            img = self._get_screenshot_impl()
            img = image_process.rgb_to_hsv(img[..., :3])[refresh_refused_rect.y1:refresh_refused_rect.y2,
                                                         refresh_refused_rect.x1:refresh_refused_rect.x2, 1]
            if np.mean(img) < self.env.detection_definitions.get_support_refresh_refused_detection_s_threshold():
                self.env.attacher.send_click(refresh_refused_confirm.x, refresh_refused_confirm.y)
                logger.info('Could not refresh support temporarily, retry in 5 secs')
                sleep(5)
            else:
                break
        sleep(0.5)
        self.env.attacher.send_click(refresh_confirm.x, refresh_confirm.y)
        sleep(1)
        WaitFufuStateHandler(self.env, self.forward_state).run_and_transit_state()
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
        if len(svt_id) == 0:
            import skimage.io
            import os
            os.makedirs('debug', exist_ok=True)
            skimage.io.imsave(f'debug/{int(time())}.png', img)

        # match craft essence
        def _craft_essence_empty_check(img1, img2):
            img1_h = int(img2.shape[1] / img1.shape[1] * img1.shape[0])
            img1 = image_process.resize(img1, img2.shape[1], img1_h)
            img1 = img1[-img2.shape[0]:, ...]
            v = mean_gray_diff_err(img1, img2)
            logger.debug('DEBUG value: empty support craft essence check: mean_gray_diff_err = %f' % v)
            return v < 10
        ce_id, t = self._wrap_call_matcher(self.craft_essence_matcher.match, _craft_essence_empty_check, img,
                                           self._support_craft_essence_imgs, range_list)
        logger.debug('Detected support craft essence ID: %s (used %f sec(s))' % (str(ce_id), t))
        ret_list = [SupportServant(x, y) for x, y in zip(svt_id, ce_id)]
        x1, x2 = self.env.detection_definitions.get_support_detection_servant_x()
        max_break_rect = self.env.detection_definitions.get_support_craft_essence_max_break_rect()
        max_break_threshold = self.env.detection_definitions.get_support_craft_essence_max_break_err_threshold()

        img_gray = np.mean(img, -1)
        vertical_diff = np.zeros_like(img_gray, dtype=np.float32)
        # pixel offset for computing abs difference
        step_size = self.env.detection_definitions.get_support_skill_v_diff_step_size()
        vertical_diff[:-step_size, :] = np.abs(img_gray[:-step_size, :] - img_gray[step_size:, :])

        for i, (y1, y2) in enumerate(range_list):
            # detect craft essence max break state
            if ce_id[i] == 0:
                ret_list[i].craft_essence_max_break = False
            else:
                icon = img[y1:y2, x1:x2, :]
                icon = icon[max_break_rect.y1:max_break_rect.y2, max_break_rect.x1:max_break_rect.x2, :]
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
                ret_list[i].craft_essence_max_break = hsv_err < max_break_threshold

            # skip when support servant is empty
            if svt_id[i] == 0:
                continue
            # detect friend state
            friend_rect = self.env.detection_definitions.get_support_friend_detect_rect()
            friend_img = img[y1+friend_rect.y1:y1+friend_rect.y2, friend_rect.x1:friend_rect.x2, :]
            # omit B channel here
            friend_part_binary = np.greater_equal(
                np.mean(friend_img[..., :2], 2),
                self.env.detection_definitions.get_support_friend_binarization_threshold())
            is_friend = np.mean(friend_part_binary) > \
                self.env.detection_definitions.get_support_friend_ratio_threshold()
            ret_list[i].is_friend = is_friend

            # skill level detection
            skill_box_rects = self.env.detection_definitions.get_support_skill_box_rect()
            # skill_img = img[y1+CV_SUPPORT_SKILL_BOX_OFFSET_Y:y1+CV_SUPPORT_SKILL_BOX_OFFSET_Y+CV_SUPPORT_SKILL_BOX_SIZE,
            #                 CV_SUPPORT_SKILL_BOX_OFFSET_X1:CV_SUPPORT_SKILL_BOX_OFFSET_X2, :3].copy()
            # just use the first several pixels and last several pixels to determine
            edge_size = self.env.detection_definitions.get_support_skill_v_diff_edge_size()
            skills = []
            for j, skill_box_rect in enumerate(skill_box_rects):
                # begin_x = j * (CV_SUPPORT_SKILL_BOX_MARGIN_X + CV_SUPPORT_SKILL_BOX_SIZE)
                v_diff_current_skill = np.mean(vertical_diff[y1+skill_box_rect.y1:y1+skill_box_rect.y2,
                                                             skill_box_rect.x1:skill_box_rect.x2], -1)
                max_v_diff = np.maximum(np.max(v_diff_current_skill[:edge_size]),
                                        np.max(v_diff_current_skill[-edge_size:]))
                logger.debug(f'DEBUG value: max_v_diff = {max_v_diff}')
                if max_v_diff > self.env.detection_definitions.get_support_skill_v_diff_threshold():
                    # digit recognition, using SSIM metric, split by S (-> 0) and V (-> 255)
                    current_skill_img = img[y1+skill_box_rect.y1:y1+skill_box_rect.y2,
                                            skill_box_rect.x1:skill_box_rect.x2, :]
                    hsv = image_process.rgb_to_hsv(current_skill_img).astype(np.float32)
                    img_digit_part = (1. - hsv[..., 1] / 255.) * (hsv[..., 2] / 255.)
                    img_digit_part = img_digit_part[15:, 3:25]
                    bin_digits = np.greater_equal(
                        img_digit_part, self.env.detection_definitions.get_support_skill_binarization_threshold())
                    digit_segments = image_process.split_image(bin_digits)
                    digits = []
                    for segment in sorted(digit_segments, key=lambda x: (x.max_x + x.min_x)):
                        if 40 < segment.associated_pixels.shape[0] < 100 \
                                and abs(segment.min_y + segment.max_y - 20) <= 3 \
                                and segment.max_x - segment.min_x < 12 <= segment.max_y - segment.min_y:
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

    def _wrap_call_matcher(self, func: Callable[[np.ndarray], int],
                           empty_check_func: Callable[[np.ndarray, np.ndarray], bool],
                           img: np.ndarray, empty_img: Optional[Union[np.ndarray, Sequence[np.ndarray]]],
                           range_list: List[Tuple[int, int]]) -> Tuple[List[int], float]:
        t = time()
        ret = []
        x1, x2 = self.env.detection_definitions.get_support_detection_servant_x()
        for y1, y2 in range_list:
            icon = img[y1:y2, x1:x2, :]
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
