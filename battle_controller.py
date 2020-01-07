import numpy as np
from attacher import MumuAttacher
from team_config import FgoTeamConfiguration
from battle_action import FgoBattleAction
from matcher import SupportServantMatcher, SupportCraftEssenceMatcher
import cv2
import matplotlib.pyplot as plt
from time import sleep
from typing import *
from cv_positioning import *
from click_positioning import *
import skimage.io
from time import time
from logging import root


# behavior definition
AP_EAT_APPLE_THRESHOLD = 0


class FgoBattleController:
    def __init__(self, max_ap: int, team_presets: List[FgoTeamConfiguration], battle_actions: List[FgoBattleAction]):
        from _version import VERSION
        root.info('==============================================================')
        root.info('* Fate / Grand Order Auto Battle Controller')
        root.info('* Version: ' + VERSION)
        root.info('* Licence: WTFPL (Do what the fuck you want to Public License)')
        root.info('* Author: qhgz2013 (Github: qhgz2013)')
        root.info('==============================================================')
        self.simulator = MumuAttacher()
        self.max_ap = max_ap
        self.team_presets = team_presets
        self.current_team_preset_index = 0
        self.battle_actions = battle_actions

    @staticmethod
    def debug_output(msg: str):
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('[%s] %s' % (now, msg))

    def get_screenshot(self):
        # get the screenshot from the simulator and resize the resolution to fit the script
        # noinspection PyUnresolvedReferences
        return self.simulator.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)

    def start_script(self):
        from fsm import FgoFSMFacade
        facade = FgoFSMFacade(self.simulator)
        # self.debug_output('[State] Script started')
        facade.run()
        while True:
            self.select_quest()
            sleep(0.5)
            # 等选助战的跑狗
            # self.wait_fufu_running()
            # 选助战
            sleep(2)
            self.select_support()
            sleep(1)
            # 确认编队
            self.select_team_member()
            sleep(1)
            # 进本
            self.enter_quest()
            # 按照预定的技能/指令卡顺序执行
            self.apply_battle_action()
            # 出本结算
            self.exit_quest()
            sleep(1)
            # self.wait_fufu_running()
            sleep(3)

    def select_quest(self):
        self.debug_output('[State] SelectQuest')
        # todo: 自动选本
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
        self.send_click(FIRST_QUEST_X, FIRST_QUEST_Y)

    def enter_quest(self):
        self.debug_output('[State] EnterQuest')
        # todo: check 队伍配置
        self.debug_output('TODO: implement team member check')
        self.send_click(ENTER_QUEST_BUTTON_X, ENTER_QUEST_BUTTON_Y)

    def apply_battle_action(self):
        self.debug_output('[State] ApplyBattleAction')
        action_sequence = self.battle_actions[self.current_team_preset_index].get_click_actions()
        turns = len(action_sequence)
        for i, turn in enumerate(action_sequence):
            self.debug_output('Turn %d / %d' % (i+1, turns))
            self.wait_attack_button()
            for t, click_pos in turn:
                if t == -1:
                    self.wait_attack_button()
                elif t > 0:
                    sleep(t)
                if click_pos is not None:
                    x, y = click_pos
                    self.send_click(x, y)

    def exit_quest(self):
        self.debug_output('[State] ExitQuest')
        # 等结算画面
        while True:
            screenshot = self.get_screenshot()
            screenshot = screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_EXIT_QUEST_Y1):
                                    int(CV_SCREENSHOT_RESOLUTION_Y*CV_EXIT_QUEST_Y2),
                                    int(CV_SCREENSHOT_RESOLUTION_X*CV_EXIT_QUEST_X1):
                                    int(CV_SCREENSHOT_RESOLUTION_X*CV_EXIT_QUEST_X2), :]
            h, w = screenshot.shape[:2]
            screenshot[int(h*CV_EXIT_QUEST_TITLE_MASK_Y1):int(h*CV_EXIT_QUEST_TITLE_MASK_Y2),
                       int(w*CV_EXIT_QUEST_TITLE_MASK_X1):int(w*CV_EXIT_QUEST_TITLE_MASK_Y2), :] = 0
            for i in range(len(CV_EXIT_QUEST_SERVANT_MASK_X1S)):
                screenshot[int(h*CV_EXIT_QUEST_SERVANT_MASK_Y1):int(h*CV_EXIT_QUEST_SERVANT_MASK_Y2),
                           int(w*CV_EXIT_QUEST_SERVANT_MASK_X1S[i]):int(w*CV_EXIT_QUEST_SERVANT_MASK_X2S[i]), :] = 0
            gray = np.mean(screenshot, -1) < CV_EXIT_QUEST_GRAY_THRESHOLD
            # plt.figure()
            # plt.imshow(gray)
            # plt.show()
            # print(np.mean(gray))
            sleep(0.2)
            if np.mean(gray) >= CV_EXIT_QUEST_GRAY_RATIO_THRESHOLD:
                break
        # 羁绊 -> master/衣服等级 -> 掉落
        for _ in range(6):
            sleep(0.5)
            self.send_click(BATTLE_EXIT_BUTTON_X, BATTLE_EXIT_BUTTON_Y)
