from .state_handler import ConfigurableStateHandler, SingleClickAndWaitFufuHandler
from attacher import AbstractAttacher
from click_positioning import *
import logging
from time import time
from image_process import imread
from cv_positioning import *
import numpy as np
from battle_control import ScriptConfiguration
from .fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')


class SelectQuestHandler(ConfigurableStateHandler):
    _eat_apple_ui_anchor = imread(CV_EAT_APPLE_UI_FILE)

    def __init__(self, attacher: AbstractAttacher, forward_state: FgoState, cfg: ScriptConfiguration):
        super().__init__(cfg)
        self.attacher = attacher
        self.forward_state = forward_state
        self._last_enter_quest_time = None

    def run_and_transit_state(self) -> FgoState:
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
            logger.info('Script performance: %f sec(s) / quest' % used)
        self._last_enter_quest_time = current
        self._estimate_ap()
        # 现在默认是选择任务列表中最上面的那个本
        next_state = SingleClickAndWaitFufuHandler(self.attacher, FIRST_QUEST_X, FIRST_QUEST_Y, self.forward_state).\
            run_and_transit_state()
        return next_state

    def _estimate_ap(self):
        screenshot = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
        img = screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_AP_BAR_Y1):int(CV_SCREENSHOT_RESOLUTION_Y*CV_AP_BAR_Y2),
                         int(CV_SCREENSHOT_RESOLUTION_X*CV_AP_BAR_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_AP_BAR_X2), 1]
        g_val = np.average(img, 0)
        normalized_ap_val = np.average(g_val > CV_AP_GREEN_THRESHOLD)
        if normalized_ap_val < 0.02 or normalized_ap_val > 0.98:
            logger.info('The AP estimation may be incorrect since it is nearly empty or full')
        ap_correction = 0.8324 * normalized_ap_val + 0.0931  # linear correction, R^2=0.9998
        if self._cfg.max_ap is not None:
            ap_val = ap_correction * self._cfg.max_ap
            logger.info('Estimated current AP: %d' % int(ap_val + 0.5))
        else:
            logger.info('Estimated current AP: %f%% (Max AP not configured)' % (ap_correction * 100))
