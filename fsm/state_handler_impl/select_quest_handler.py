from ..state_handler import StateHandler, SingleClickAndWaitFufuHandler
import logging
from time import time
from image_process import imread
import numpy as np
from bgo_game import ScriptEnv
from fsm.fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')


class SelectQuestHandler(StateHandler):
    _eat_apple_ui_anchor = None

    def __init__(self, env: ScriptEnv, forward_state: FgoState):
        super().__init__(env, forward_state)
        self._last_enter_quest_time = None
        if self._eat_apple_ui_anchor is None:
            self._eat_apple_ui_anchor = imread(self.env.detection_definitions.get_eat_apple_ui_file())

    def run_and_transit_state(self) -> FgoState:
        # todo [PRIOR: low]: implement quest select
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
            logger.info(f'Script performance: {current - self._last_enter_quest_time:.2f} sec(s) / quest')
        self._last_enter_quest_time = current
        self._estimate_ap()
        # 现在默认是选择任务列表中最上面的那个本
        first_quest = self.env.click_definitions.enter_first_quest()
        next_state = SingleClickAndWaitFufuHandler(self.env, self.forward_state, first_quest.x, first_quest.y).\
            run_and_transit_state()
        return next_state

    def _estimate_ap(self):
        screenshot = self._get_screenshot_impl()
        ap_bar_rect = self.env.detection_definitions.get_ap_bar_rect()
        img = screenshot[ap_bar_rect.y1:ap_bar_rect.y2, ap_bar_rect.x1:ap_bar_rect.x2, 1]
        g_val = np.average(img, 0)
        normalized_ap_val = np.average(g_val > self.env.detection_definitions.get_ap_green_threshold())
        # if normalized_ap_val < 0.02 or normalized_ap_val > 0.98:
        #     logger.info('The AP estimation may be incorrect since it is nearly empty or full')
        ap_correction = 0.8324 * normalized_ap_val + 0.0931  # linear correction, R^2=0.9998
        logger.info(f'Estimated current AP: {ap_correction * 100:.2f}% (Max AP not configured)')
