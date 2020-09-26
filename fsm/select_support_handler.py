from .state_handler import StateHandler
from attacher import AbstractAttacher
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
import logging
from typing import List, Optional, Tuple, Callable, Union
from cv_positioning import *
from click_positioning import *
import image_process
import numpy as np
from time import sleep, time
from .wait_fufu_handler import WaitFufuStateHandler
from image_process import mean_gray_diff_err

logger = logging.getLogger('bgo_script.fsm')


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
                    logger.info('Found required support')
                    self.attacher.send_click(0.5, (support_range[i][0] + support_range[i][1]) / 2)
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
        self.attacher.send_slide((0.5, 0.9), (0.5, 0.9 - SUPPORT_SCROLLDOWN_Y))
        sleep(1.5)

    @classmethod
    def _split_support_image(cls, img: np.ndarray) -> List[Tuple[float, float]]:
        # new detection result begins here
        part = img[:, int(CV_SUPPORT_DETECT_X1*CV_SCREENSHOT_RESOLUTION_X):
                   int(CV_SUPPORT_DETECT_X2*CV_SCREENSHOT_RESOLUTION_X), :]
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
            len_y = end_y - begin_y
            if CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_LO <= len_y <= CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_HI:
                range_list.append((begin_y / CV_SCREENSHOT_RESOLUTION_Y, end_y / CV_SCREENSHOT_RESOLUTION_Y))
                logger.debug('support detection: %d -> %d (len = %d)' % (begin_y, end_y, end_y-begin_y))
            else:
                logger.debug('support detection: %d -> %d (len = %d) (ignored)' % (begin_y, end_y, end_y-begin_y))
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
        logger.debug('Scrollbar position: %d -> %d' % (start_y, end_y))
        return start_y / score.shape[0], end_y / score.shape[0]

    def refresh_support(self):
        logger.info('Refreshing support')
        while True:
            sleep(0.5)
            self.attacher.send_click(SUPPORT_REFRESH_BUTTON_X, SUPPORT_REFRESH_BUTTON_Y)
            sleep(0.5)
            # Check clickable
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            img = image_process.rgb_to_hsv(img)[
                int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y1):
                int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y2),
                int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_REFRESH_REFUSED_DETECTION_X1):
                int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_REFRESH_REFUSED_DETECTION_X2), 1]
            if np.mean(img) < CV_SUPPORT_REFRESH_REFUSED_DETECTION_S_THRESHOLD:
                self.attacher.send_click(SUPPORT_REFRESH_REFUSED_CONFIRM_X, SUPPORT_REFRESH_REFUSED_CONFIRM_Y)
                logger.info('Could not refresh support temporarily, retry in 5 secs')
                sleep(5)
            else:
                break
        sleep(0.5)
        self.attacher.send_click(SUPPORT_REFRESH_BUTTON_CONFIRM_X, SUPPORT_REFRESH_BUTTON_CONFIRM_Y)
        sleep(1)
        WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        sleep(0.5)

    def match_servant(self, img: np.ndarray, range_list: List[Tuple[float, float]]) -> List[Tuple[int, List[int]]]:
        def _empty_check(img1, img2):
            v = mean_gray_diff_err(image_process.resize(img1, img2.shape[1], img2.shape[0]), img2)
            logger.debug('DEBUG value: empty support servant check: mean_gray_diff_err = %f' % v)
            return v < 10
        ret, t = self._wrap_call_matcher(self.servant_matcher.match, _empty_check, img, self._support_empty_img,
                                         range_list)
        logger.info('Detected support servant ID: %s (used %f sec(s))' % (str(ret), t))
        # TODO: implement skill level detection here (replacing [0, 0, 0])
        return [(x, [0, 0, 0]) for x in ret]

    def match_craft_essence(self, img: np.ndarray, range_list: List[Tuple[float, float]]) -> List[Tuple[int, bool]]:
        def _empty_check(img1, img2):
            img1_h = int(img2.shape[1] / img1.shape[1] * img1.shape[0])
            img1 = image_process.resize(img1, img2.shape[1], img1_h)
            img1 = img1[-img2.shape[0]:, ...]
            v = mean_gray_diff_err(img1, img2)
            logger.debug('DEBUG value: empty support craft essence check: mean_gray_diff_err = %f' % v)
            return v < 10
        ret, t = self._wrap_call_matcher(self.craft_essence_matcher.match, _empty_check, img,
                                         self._support_craft_essence_img, range_list)
        logger.info('Detected support craft essence ID: %s (used %f sec(s))' % (str(ret), t))
        t = time()
        # detect craft essence max break state
        max_break = []
        for i, (y1, y2) in enumerate(range_list):
            if ret[i] == 0:
                max_break.append(False)
                continue
            icon = img[int(CV_SCREENSHOT_RESOLUTION_Y*y1):int(CV_SCREENSHOT_RESOLUTION_Y*y2),
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SERVANT_X1):
                       int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SERVANT_X2), :]
            icon = icon[-24:-4, 134:154, :]
            # import matplotlib.pyplot as plt
            # plt.figure()
            # plt.imshow(icon)
            # plt.show()
            # icon = image_process.resize(icon, self._support_max_break_img.shape[1],
            #                             self._support_max_break_img.shape[0])
            anchor = image_process.resize(self._support_max_break_img, icon.shape[1], icon.shape[0])
            # plt.figure()
            # plt.imshow(anchor)
            # plt.show()
            err = mean_gray_diff_err(icon, anchor)
            hsv_err = image_process.mean_hsv_diff_err(icon, anchor)
            logger.debug('DEBUG value: support craft essence max break check: gray_diff_err = %f, hsv_err = %f' %
                         (err, hsv_err))
            max_break.append(hsv_err < CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_THRESHOLD)
        logger.info('Detected support craft essence max break state: %s (used %f sec(s))' % (str(max_break), time() - t))
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
