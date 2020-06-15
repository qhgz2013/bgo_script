from .state_handler import StateHandler
from attacher import AbstractAttacher
from click_positioning import *
from .wait_fufu_handler import WaitFufuStateHandler
from time import sleep
import image_process
from cv_positioning import *
from util import mean_gray_diff_err
from logging import root


class ExitQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int):
        self.attacher = attacher
        self.forward_state = forward_state
        self._support_anchor = image_process.imread(CV_REQUEST_SUPPORT_UI_FILE)

    def run_and_transit_state(self) -> int:
        for _ in range(7):
            self.attacher.send_click(BATTLE_EXIT_BUTTON_X, BATTLE_EXIT_BUTTON_Y)
            sleep(0.5)
        WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        # 检查并跳过发送好友申请界面（用于选择非好友助战但好友未满时的情况）
        if self._is_in_requesting_friend_ui():
            root.info('Detected friend request UI, skipped')
            self.attacher.send_click(SUPPORT_REQUEST_BUTTON_SKIP_X, SUPPORT_REQUEST_BUTTON_Y)
            sleep(2)
            WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        return self.forward_state

    def _is_in_requesting_friend_ui(self) -> bool:
        img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        return mean_gray_diff_err(image_process.resize(img, self._support_anchor.shape[1],
                                                       self._support_anchor.shape[0]), self._support_anchor)
