import numpy as np
from attacher import MumuAttacher
from team_config import FgoTeamConfiguration
from battle_action import FgoBattleAction
from matcher import ServantMatcher, CraftEssenceMatcher
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
        self._attack_button_cv_data = None
        # self.debug_output('Initializing servant matcher')
        self.servant_matcher = ServantMatcher()
        # self.debug_output('Initializing craft essence matcher')
        self.craft_essence_matcher = CraftEssenceMatcher()

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
            self.wait_fufu_running()
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
            self.wait_fufu_running()
            sleep(3)

    def wait_fufu_running(self):
        self.debug_output('[State] WaitFufuRunning')
        t = time()
        while True:
            screenshot = self.get_screenshot()
            fufu_area = np.sum(
                screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_FUFU_Y1):int(CV_SCREENSHOT_RESOLUTION_Y*CV_FUFU_Y2),
                           int(CV_SCREENSHOT_RESOLUTION_X*CV_FUFU_X1):int(CV_SCREENSHOT_RESOLUTION_X*CV_FUFU_X2), :],
                -1)
            ratio = np.average(fufu_area < CV_FUFU_BLANK_THRESHOLD)
            if ratio < CV_FUFU_BLANK_RATIO_THRESHOLD:
                break
            sleep(0.2)
        self.debug_output('Performance: waited %f second(s)' % (time() - t))

    def _init_attack_button_cv_data(self):
        dx = int(CV_SCREENSHOT_RESOLUTION_X * (CV_ATTACK_BUTTON_X2 - CV_ATTACK_BUTTON_X1))
        dy = int(CV_SCREENSHOT_RESOLUTION_Y * (CV_ATTACK_BUTTON_Y2 - CV_ATTACK_BUTTON_Y1))
        d = min(dx, dy)
        cx = dx / 2
        cy = dy / 2
        y, x = np.ogrid[:dx, :dy]
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        mask = r < (d / 2)
        sum_mask = np.sum(mask)
        self._attack_button_cv_data = {
            'anchor_img': np.mean(skimage.io.imread(CV_ATTACK_BUTTON_ANCHOR)[..., :3], -1),
            'mask': mask,
            'mask_sum': sum_mask
        }

    def wait_attack_button(self):
        self.debug_output('[State] WaitAttackButton')
        # test passed
        t = time()
        if self._attack_button_cv_data is None:
            self._init_attack_button_cv_data()
        while True:
            screenshot = np.mean(self.get_screenshot(), -1)
            btn_area = screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y1):
                                  int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y2),
                                  int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X1):
                                  int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X2)]
            abs_gray_diff = np.abs(btn_area - self._attack_button_cv_data['anchor_img'])
            mean_abs_gray_diff = np.sum(abs_gray_diff * self._attack_button_cv_data['mask']) / \
                self._attack_button_cv_data['mask_sum'] / 255
            if mean_abs_gray_diff < CV_ATTACK_DIFF_THRESHOLD:
                break
            sleep(0.2)
        self.debug_output('Performance: waited %f second(s)' % (time() - t))

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

    def select_support(self):
        self.debug_output('[State] SelectSupport')
        while True:
            screenshot = self.get_screenshot()
            support_servant = self.team_presets[self.current_team_preset_index].support_servant_id
            support_craft_essence = self.team_presets[self.current_team_preset_index].support_craft_essence_id
            current_support_servants, servant_icon_range_y = self.get_support_servant(screenshot=screenshot)
            current_craft_essences = []
            if type(support_craft_essence) == list or support_craft_essence > 0:
                current_craft_essences, _ = self.get_support_craft_essence(servant_icon_range_y, screenshot)
            servant_range_y = None
            for i in range(len(current_support_servants)):
                if support_servant == current_support_servants[i] and \
                        ((type(support_craft_essence) == list and support_craft_essence in current_craft_essences)
                         or (support_craft_essence == 0 or support_craft_essence == current_craft_essences[i])):
                    servant_range_y = servant_icon_range_y[i]
                    break
            if servant_range_y is not None:
                # 匹配到从者
                self.debug_output('Found required servant')
                self.send_click(0.5, (servant_range_y[1] + servant_range_y[0]) / 2 / CV_SCREENSHOT_RESOLUTION_Y)
                break
            _, end_pos = self.get_support_scrollbar_pos()
            # 选不到从者下拉助战列表，直到列表末尾
            if end_pos < 0.99:
                # 下拉助战列表
                self.scroll_down_servant_bar()
            else:
                # 到列表末尾都找不到从者，则进行刷新，并且按其他队进行配置
                # todo: 优先度调度
                self.refresh_support()
                self.current_team_preset_index += 1
                self.current_team_preset_index %= len(self.team_presets)
            sleep(1)

    def scroll_down_servant_bar(self):
        self.debug_output('[State] ScrollDownServantBar')
        x_from = 0.5
        y_from = 0.9
        y_to = y_from - SUPPORT_SCROLLDOWN_Y
        self.send_slide((x_from, y_from), (x_from, y_to))

    def get_support_servant(self, support_range: Union[None, List[Tuple[int, int]]] = None,
                            screenshot: Union[None, np.ndarray] = None) -> Tuple[List[int], List[Tuple[int, int]]]:
        self.debug_output('[State] GetSupportServant')
        if screenshot is None:
            screenshot = self.get_screenshot()
        if support_range is None:
            support_range = self.get_support_range(screenshot)
        x1 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X1)
        x2 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X2)
        t = time()
        ret = []
        for y1, y2 in support_range:
            servant_icon = screenshot[y1:y2, x1:x2, :]
            ret.append(self.servant_matcher.match_support(servant_icon))
        self.debug_output('Support servant ID: %s (Used time: %f s)' % (str(ret), time() - t))
        return ret, support_range

    def get_support_craft_essence(self, support_range: Union[None, List[Tuple[int, int]]] = None,
                                  screenshot: Union[None, np.ndarray] = None) \
            -> Tuple[List[int], List[Tuple[int, int]]]:
        self.debug_output('[State] GetSupportCraftEssence')
        if screenshot is None:
            screenshot = self.get_screenshot()
        if support_range is None:
            support_range = self.get_support_range(screenshot)
        x1 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X1)
        x2 = int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_SERVANT_X2)
        t = time()
        ret = []
        for y1, y2 in support_range:
            servant_icon = screenshot[y1:y2, x1:x2, :]
            ret.append(self.craft_essence_matcher.match_support(servant_icon))
        self.debug_output('Support craft essence ID: %s (Used time: %f s)' % (str(ret), time() - t))
        return ret, support_range

    def get_support_range(self, screenshot: Union[None, np.ndarray] = None) -> List[Tuple[int, int]]:
        self.debug_output('[State] GetSupportRange')
        import matplotlib.pyplot as plt
        if screenshot is None:
            screenshot = self.get_screenshot()
        support_check_part = screenshot[:, int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_X1):
                                        int(CV_SCREENSHOT_RESOLUTION_X * CV_SUPPORT_X2), :]
        # noinspection PyUnresolvedReferences
        support_check_hsv = cv2.cvtColor(support_check_part, cv2.COLOR_RGB2HSV)
        support_check_score = np.median(support_check_hsv[..., 1], -1)
        # plt.figure(figsize=(16, 9))
        # plt.imshow(support_check_hsv[..., 1])
        # plt.show()
        # plt.figure(figsize=(16, 9))
        # plt.plot(support_check_score)
        # plt.show()
        stage1_valid = np.logical_and(support_check_score >= CV_SUPPORT_S_STAGE1_LO,
                                      support_check_score < CV_SUPPORT_S_STAGE1_HI)
        stage2_valid = np.logical_and(support_check_score >= CV_SUPPORT_S_STAGE2_LO,
                                      support_check_score < CV_SUPPORT_S_STAGE2_HI)
        y = 0
        range_list = []
        while y < CV_SCREENSHOT_RESOLUTION_Y:
            while y < CV_SCREENSHOT_RESOLUTION_Y and not stage1_valid[y]:
                y += 1
            if y == CV_SCREENSHOT_RESOLUTION_Y:
                break
            begin_y = y
            while y < CV_SCREENSHOT_RESOLUTION_Y and stage1_valid[y]:
                y += 1
            end_y = y
            stage1_len = end_y - begin_y
            if stage1_len < CV_SUPPORT_STAGE1_LEN:
                continue
            lookahead_y = y
            begin_y2 = y
            while lookahead_y < CV_SCREENSHOT_RESOLUTION_Y:
                if not stage2_valid[lookahead_y]:
                    if lookahead_y - end_y < 5:
                        begin_y2 = lookahead_y + 1
                    else:
                        break
                lookahead_y += 1
            if begin_y2 - end_y >= 5:
                continue
            end_y2 = lookahead_y
            stage2_len = end_y2 - begin_y2
            if stage2_len < CV_SUPPORT_STAGE2_LEN:
                continue
            range_list.append((begin_y - 8, end_y2 + (18 if stage1_len < CV_SUPPORT_STAGE1_LEN2 else 8)))
            y = lookahead_y
        self.debug_output('Returned: %s' % (str(range_list)))
        return range_list

    def get_support_scrollbar_pos(self) -> Tuple[float, float]:
        self.debug_output('[State] GetSupportScrollbarPos')
        screenshot = self.get_screenshot()
        scrollbar = screenshot[int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_SCROLLBAR_Y1):
                               int(CV_SCREENSHOT_RESOLUTION_Y*CV_SUPPORT_SCROLLBAR_Y2),
                               int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SCROLLBAR_X1):
                               int(CV_SCREENSHOT_RESOLUTION_X*CV_SUPPORT_SCROLLBAR_X2), :]
        score = np.mean(np.mean(scrollbar, -1), -1) < CV_SUPPORT_BAR_GRAY_THRESHOLD
        scroll_len = score.shape[0]
        start_y = 0
        end_y = 0
        for y in range(scroll_len):
            if not score[y]:
                start_y = y
                break
        for y in range(start_y, scroll_len):
            if score[y]:
                break
            end_y = y
        self.debug_output('Start y: %d, End y: %d' % (start_y, end_y))
        return start_y / scroll_len, end_y / scroll_len

    def refresh_support(self):
        self.debug_output('[State] RefreshSupport')
        sleep(0.5)
        self.send_click(SUPPORT_REFRESH_BUTTON_X, SUPPORT_REFRESH_BUTTON_Y)
        sleep(1)
        self.send_click(SUPPORT_REFRESH_BUTTON_CONFIRM_X, SUPPORT_REFRESH_BUTTON_CONFIRM_Y)
        sleep(1)
        self.wait_fufu_running()
        sleep(0.5)

    def select_team_member(self):
        self.debug_output('[State] SelectTeamMember')
        self.debug_output('Not implemented, skipped')

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

    # wrapper function
    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        self.debug_output('[Simulator] Click (%f, %f) with t = %f s' % (x, y, stay_time))
        self.simulator.send_click(x, y, stay_time)

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        self.debug_output('[Simulator] Slide %s to %s with t = %f (pre-) / %f / %f (post-)' %
                          (str(p_from), str(p_to), stay_time_before_move, stay_time_move, stay_time_after_move))
        self.simulator.send_slide(p_from, p_to, stay_time_before_move, stay_time_move, stay_time_after_move)
