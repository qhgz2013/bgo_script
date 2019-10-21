from mumu_attach import MumuSimulatorAttacher
from battle_controller import FgoBattleController
from team_config import FgoTeamConfiguration
from battle_action import FgoBattleAction
import cv2
import matplotlib.pyplot as plt
import numpy as np
from cv_positioning import *
import skimage.io

# 常用从者
svt_common = {
    # 四拐
    'cba': 215,
    '孔': 37,
    '梅': 150,
    '狐': 62,
    # 常用打手
    '呆毛': 2,
    '大英雄': 16,
    'stella': 16,
    '伯爵': None,
}

cs_common = {
    '宝石': 34,
    '虚数': 28,

}

def plot_axis():
    simulator = MumuSimulatorAttacher()
    a = simulator.get_screenshot()
    # a = skimage.io.imread(r'C:\Users\qhgz2\Documents\MuMu共享文件夹\MuMu20191017213531.png')
    a = cv2.resize(a, (1280, 720))
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    for i in range(3):
        a[:, :, i] = hsv[..., 2]
    for i in range(0, 1280, 10):
        a[:, i, 0] = 255
    for j in range(0, 720, 10):
        a[j, :, 1] = 255
    plt.figure(figsize=(16, 9))
    a = a[180:700, 1230:1250, :]
    plt.imshow(a)
    plt.show()
    plt.figure(figsize=(16, 9))
    a = np.mean(a[..., 0], -1)
    plt.plot(a)
    plt.show()
    # am2 = np.average(hsv[:, 770:830, 1], -1)
    # plt.figure(figsize=(16, 9))
    # plt.plot(am2)
    # plt.show()
    # print(am2[190:300:3])
    # am3 = np.average(am, -1)
    # plt.figure(figsize=(16, 9))
    # plt.plot(am3)
    # plt.show()

def t():
    from time import sleep
    sleep(1)
    sim = MumuSimulatorAttacher()
    # sim.send_click(0.5, 0.1)
    sim.send_slide((0.5, 0.5), (0.5, 0.1), 0.5, 2, 1)
    # a = skimage.io.imread(r'C:\Users\qhgz2\Documents\MuMu共享文件夹\MuMu20191017213531.png')[..., :3]
    # a = cv2.resize(a, (1280, 720))
    # from matcher import CraftEssenceMatcher
    # x = CraftEssenceMatcher()
    # print(x.match_support(a[195:375, 48:212, :]))


def team_one():
    # 龙牙本
    team_preset = FgoTeamConfiguration([1, 2, 3, 4, 5], [0, 0, 0, 0, 0],
                                       svt_common['大英雄'], 0, 3)
    actions = FgoBattleAction(team_preset)
    # T1 大英雄自充 + 宝具
    actions.begin_turn()
    actions.click_skill(1, 2)
    actions.go_fucking_noble_phantasm(1).go_fucking_attack(2, 0).go_fucking_attack(2, 1)
    actions.remove_servant(1)
    actions.end_turn()
    # T2 大英雄自充 + 宝具
    actions.begin_turn()
    actions.click_support_skill(2)
    actions.go_fucking_support_noble_phantasm().go_fucking_attack(2, 0).go_fucking_attack(2, 1)
    actions.remove_servant(0)  # remove support
    actions.end_turn()
    # T3 海伦娜群充 + 魔放，魔总和x毛宝具
    actions.begin_turn()
    actions.click_skill(4, 0).click_skill(4, 2).click_skill(2, 0).click_skill(2, 2)
    actions.use_clothes_skill(1, 2)
    actions.go_fucking_noble_phantasm(2, 1).go_fucking_noble_phantasm(3).go_fucking_attack(3, 0)
    actions.end_turn()

    controller = FgoBattleController(141, [team_preset], [actions])
    controller.start_script()


def main():
    # t()
    # plot_axis()
    # team_preset = FgoTeamConfiguration([1, 2, 3, 4, 5], [0, 0, 0, 0, 0], 215, 0, 2)
    # controller = FgoBattleController(141, [team_preset], None)
    # controller.start_script()
    team_one()


if __name__ == '__main__':
    main()
