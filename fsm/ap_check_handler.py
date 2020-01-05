from .state_handler import StateHandler
from attacher import AbstractAttacher
from cv_positioning import *
from click_positioning import *
import numpy as np
from time import sleep
from logging import root
from .wait_fufu_handler import WaitFufuStateHandler


class ApCheckHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, max_ap: int, eat_apple_ap_threshold: int, forward_state: int):
        self.attacher = attacher
        self.max_ap = max_ap
        self.eat_apple_ap_threshold = eat_apple_ap_threshold
        self.forward_state = forward_state

    def run_and_transit_state(self) -> int:
        # check AP
        screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        img = screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_AP_BAR_Y1):int(CV_SCREENSHOT_RESOLUTION_Y*CV_AP_BAR_Y2),
                         int(CV_SCREENSHOT_RESOLUTION_X*CV_AP_BAR_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_AP_BAR_X2), 1]
        g_val = np.average(img, 0)
        normalized_ap_val = np.average(g_val > CV_AP_GREEN_THRESHOLD)
        ap_val = int(self.max_ap * normalized_ap_val)
        root.info('Estimated current AP: %d' % ap_val)
        # eat apple if needed
        if ap_val < self.eat_apple_ap_threshold:
            root.info('Eat apple')
            ap_bar_center_x = (CV_AP_BAR_X1 + CV_AP_BAR_X2) / 2
            ap_bar_center_y = (CV_AP_BAR_Y1 + CV_AP_BAR_Y2) / 2
            self.attacher.send_click(ap_bar_center_x, ap_bar_center_y)
            sleep(0.5)
            self.attacher.send_click(EAT_APPLE_CLICK_X, EAT_APPLE_CLICK_Y)
            sleep(0.5)
            self.attacher.send_click(EAT_APPLE_CONFIRM_CLICK_X, EAT_APPLE_CONFIRM_CLICK_Y)
            # wait fufu
            WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        return self.forward_state
