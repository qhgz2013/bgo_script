from .state_handler import StateHandler
from attacher import AbstractAttacher
from click_positioning import *


class SelectQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int):
        self.attacher = attacher
        self.forward_state = forward_state

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

        # 现在默认是选择任务列表中最上面的那个本
        from .single_click_and_wait_fufu_handler import SingleClickAndWaitFufuHandler
        return SingleClickAndWaitFufuHandler(self.attacher, FIRST_QUEST_X, FIRST_QUEST_Y, self.forward_state).\
            run_and_transit_state()
