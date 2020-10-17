from .state_handler import ConfigurableStateHandler, WaitFufuStateHandler
from attacher import AbstractAttacher, MumuAttacher, AdbAttacher
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
import logging
from typing import *
from cv_positioning import *
from click_positioning import *
import image_process
import numpy as np
from time import sleep, time
from image_process import mean_gray_diff_err
from battle_control import ScriptConfiguration, SupportServantConfiguration
from .fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')


class SelectSupportHandler(ConfigurableStateHandler):
    _support_empty_img = image_process.imread(CV_SUPPORT_EMPTY_FILE)
    _support_craft_essence_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_FILE)
    _support_max_break_img = image_process.imread(CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_FILE)
    _scroll_down_y_mapper = {MumuAttacher: SUPPORT_SCROLLDOWN_Y_MUMU, AdbAttacher: SUPPORT_SCROLLDOWN_Y_ADB}

    servant_matcher = SupportServantMatcher(CV_FGO_DATABASE_FILE)
    craft_essence_matcher = SupportCraftEssenceMatcher(CV_FGO_DATABASE_FILE)

    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state
        self._support_svt = self._cfg.team_config.support_servant
        # noinspection PyTypeChecker
        self._scroll_down_y = self._scroll_down_y_mapper[type(attacher)]

    def run_and_transit_state(self) -> FgoState:
        suc = False
        while True:
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)[..., :3]
            support_range = self._split_support_image(img)
            svt_data = self.match_support_servant(img, support_range)
            for i in range(len(svt_data)):
                cur_svt_id = svt_data[i].svt_id
                cur_ce_id = svt_data[i].craft_essence_id
                cur_ce_max_break = svt_data[i].craft_essence_max_break
                cur_ce_friend = svt_data[i].friend_only
                if (self._support_svt.svt_id == 0 or self._support_svt.svt_id == cur_svt_id) and \
                        (self._support_svt.craft_essence_id == 0 or self._support_svt.craft_essence_id == cur_ce_id) \
                        and (not self._support_svt.craft_essence_max_break or cur_ce_max_break) and \
                        (not self._support_svt.friend_only or cur_ce_friend):
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
        # TODO: 修改为支持多段合并的识别模式（对上升沿和下降沿分别进行匹配）
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

    def match_support_servant(self, img: np.ndarray, range_list: List[Tuple[int, int]]) \
            -> List[SupportServantConfiguration]:
        # match servant
        def _servant_empty_check(img1, img2):
            v = mean_gray_diff_err(image_process.resize(img1, img2.shape[1], img2.shape[0]), img2)
            logger.debug('DEBUG value: empty support servant check: mean_gray_diff_err = %f' % v)
            return v < 10
        svt_id, t = self._wrap_call_matcher(self.servant_matcher.match, _servant_empty_check, img,
                                            self._support_empty_img, range_list)
        logger.info('Detected support servant ID: %s (used %f sec(s))' % (str(svt_id), t))

        # match craft essence
        def _craft_essence_empty_check(img1, img2):
            img1_h = int(img2.shape[1] / img1.shape[1] * img1.shape[0])
            img1 = image_process.resize(img1, img2.shape[1], img1_h)
            img1 = img1[-img2.shape[0]:, ...]
            v = mean_gray_diff_err(img1, img2)
            logger.debug('DEBUG value: empty support craft essence check: mean_gray_diff_err = %f' % v)
            return v < 10
        ce_id, t = self._wrap_call_matcher(self.craft_essence_matcher.match, _craft_essence_empty_check, img,
                                           self._support_craft_essence_img, range_list)
        logger.info('Detected support craft essence ID: %s (used %f sec(s))' % (str(ce_id), t))
        ret_list = [SupportServantConfiguration(x, y) for x, y in zip(svt_id, ce_id)]
        for i, (y1, y2) in enumerate(range_list):
            # detect craft essence max break state
            if ce_id[i] == 0:
                ret_list[i].craft_essence_max_break = False
            else:
                icon = img[y1:y2, CV_SUPPORT_SERVANT_X1:CV_SUPPORT_SERVANT_X2, :]
                icon = icon[CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y1:CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y2,
                            CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X1:CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X2, :]
                # icon = image_process.resize(icon, self._support_max_break_img.shape[1],
                #                             self._support_max_break_img.shape[0])
                anchor = image_process.resize(self._support_max_break_img, icon.shape[1], icon.shape[0])
                # err = mean_gray_diff_err(icon, anchor)
                hsv_err = image_process.mean_hsv_diff_err(icon, anchor)
                # logger.debug('DEBUG value: support craft essence max break check: gray_diff_err = %f, hsv_err = %f' %
                #              (err, hsv_err))
                ret_list[i].craft_essence_max_break = hsv_err < CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_THRESHOLD

            # detect friend state
            if svt_id[i] == 0:
                ret_list[i].friend_only = False  # use friend_only as is_friend indicator, TODO: use separate class
            else:
                friend_img = img[y1+CV_SUPPORT_FRIEND_DETECT_Y1:y1+CV_SUPPORT_FRIEND_DETECT_Y2,
                                 CV_SUPPORT_FRIEND_DETECT_X1:CV_SUPPORT_FRIEND_DETECT_X2, :]
                # omit B channel here
                friend_part_binary = np.greater_equal(np.mean(friend_img[..., :2], 2),
                                                      CV_SUPPORT_FRIEND_DISCRETE_THRESHOLD)
                is_friend = np.mean(friend_part_binary) > CV_SUPPORT_FRIEND_DETECT_THRESHOLD
                ret_list[i].friend_only = is_friend
        # TODO: implement skill level detection here (replacing [0, 0, 0])
        logger.debug('Detected support servant info: %s' % str(ret_list))
        return ret_list

    @staticmethod
    def _wrap_call_matcher(func: Callable[[np.ndarray], int],
                           empty_check_func: Callable[[np.ndarray, np.ndarray], bool],
                           img: np.ndarray, empty_img: Union[np.ndarray, None],
                           range_list: List[Tuple[int, int]]) -> Tuple[List[int], float]:
        t = time()
        ret = []
        for y1, y2 in range_list:
            icon = img[y1:y2, CV_SUPPORT_SERVANT_X1:CV_SUPPORT_SERVANT_X2, :]
            if empty_img is not None and empty_check_func(icon, empty_img):
                ret.append(0)
            else:
                ret.append(func(icon))
        return ret, time() - t
