from .state_handler import StateHandler
from cv_positioning import *
from attacher import AbstractAttacher
import numpy as np
from time import sleep


class WaitFufuStateHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int):
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> int:
        while True:
            screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            fufu_area = np.sum(
                screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_FUFU_Y1):int(CV_SCREENSHOT_RESOLUTION_Y*CV_FUFU_Y2),
                           int(CV_SCREENSHOT_RESOLUTION_X*CV_FUFU_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_FUFU_X2), :],
                -1)
            ratio = np.average(fufu_area < CV_FUFU_BLANK_THRESHOLD)
            if ratio < CV_FUFU_BLANK_RATIO_THRESHOLD:
                break
            sleep(0.2)
        return self.forward_state
