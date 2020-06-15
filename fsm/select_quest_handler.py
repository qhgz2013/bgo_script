from .state_handler import StateHandler
from attacher import AbstractAttacher
from click_positioning import *
from logging import root
from time import time
from image_process import imread
from cv_positioning import *
from util import mean_gray_diff_err
from time import sleep


class SelectQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int, exit_if_eat_apple_ui_detected: bool = False):
        self.attacher = attacher
        self.forward_state = forward_state
        self._eat_apple_ui_anchor = imread(CV_EAT_APPLE_UI_FILE)
        self._last_enter_quest_time = None
        self._exit_if_eat_apple = exit_if_eat_apple_ui_detected

    def run_and_transit_state(self) -> int:
        # todo: implement quest select
        # input: 关卡颜色和顺序
        # algorithm:
        # 0. 将滚动条拖到最上方
        # 1. 截取x=[800, 1080]的图
        # 2. RGB -> HSV，选取S色域
        # 3. 离散处理：S<40=255，S>40=0
        # 4. 计算y轴的平均值
        # 5. 计算y轴的梯度图均值
        # 6. 得分=均值-梯度图均值*一个权重因子（默认1）
        # 7. 按得分阈值>40进行连续区间划分，选择区间长度和两区间距离符合bgo规律的区间（还没测）
        # 8. 用上面的候选计算大概的关卡的大概位置
        # 9. 根据候选位置计算关卡的背景颜色，与指定的关卡颜色比对，相同则计数+1
        # 10. 当计数=给定的关卡顺序时，搓进去，退出循环
        # 11. 屏幕往下拖，重复1.-10.操作

        # Timing debug (performance test)
        current = time()
        if self._last_enter_quest_time is not None:
            used = current - self._last_enter_quest_time
            root.info('Script performance: %f sec(s) / quest' % used)
        self._last_enter_quest_time = current
        # 现在默认是选择任务列表中最上面的那个本
        from .single_click_and_wait_fufu_handler import SingleClickAndWaitFufuHandler
        next_state = SingleClickAndWaitFufuHandler(self.attacher, FIRST_QUEST_X, FIRST_QUEST_Y, self.forward_state).\
            run_and_transit_state()
        # make sure it's not in eat apple ui
        img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        if mean_gray_diff_err(self._eat_apple_ui_anchor, img, 3):
            if self._exit_if_eat_apple:
                root.error('AP is not enough to enter quest, exit process (exit_if_eat_apple_ui_detected = True)')
                exit(0)
            root.warning('AP is not enough to enter quest, reset to AP_CHECK state')
            self.attacher.send_click(CANCEL_EAT_APPLE_BUTTON_X, CANCEL_EAT_APPLE_BUTTON_Y)
            sleep(0.5)
            from .fgo_state import STATE_CHECK_AP
            return STATE_CHECK_AP
        return next_state
