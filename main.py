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
    a = skimage.io.imread(r'C:\Users\qhgz2\Documents\MuMu共享文件夹\MuMu20191017113537.png')[..., :3]
    a = cv2.resize(a, (1280, 720))
    # hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    # for i in range(3):
    #     a[:, :, i] = hsv[..., 2]
    a = a[155:545, 55:1225, :]
    # for i in range(0, a.shape[1], 10):
    #     a[:, i, 0] = 255
    # for j in range(0, a.shape[0], 10):
    #     a[j, :, 1] = 255
    a[15:50, 20:245, :] = 0
    a[75:365, 55:225, :] = 0
    a[75:365, 275:450, :] = 0
    a[75:365, 500:670, :] = 0
    a[75:365, 720:895, :] = 0
    a[75:365, 945:1115, :] = 0
    a = np.mean(a, -1)
    a = a < 25
    print(np.mean(a))
    plt.figure(figsize=(16, 9))
    plt.imshow(a)
    plt.show()
    plt.figure(figsize=(16, 9))
    # a = np.mean(a[..., 0], -1)
    # plt.plot(a)
    # plt.show()
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


# 龙牙本 3T
def team_one():
    team_preset = FgoTeamConfiguration([1, 2, 3, 4, 5], [0, 0, 0, 0, 0],
                                       svt_common['大英雄'], 0, 3)
    actions = FgoBattleAction(team_preset)
    # T1 大英雄自充 + 宝具
    actions.begin_turn()
    actions.use_skill(1, 2)
    actions.noble_phantasm(1).attack(2, 0).attack(2, 1)
    actions.remove_servant(1)
    actions.end_turn()
    # T2 大英雄自充 + 宝具
    actions.begin_turn()
    actions.use_support_skill(2)
    actions.support_noble_phantasm().attack(2, 0).attack(2, 1)
    actions.remove_servant(0)  # remove support
    actions.end_turn()
    # T3 海伦娜群充 + 魔放，魔总和x毛宝具
    actions.begin_turn()
    actions.use_skill(4, 0).use_skill(4, 2).use_skill(2, 0).use_skill(2, 2)
    actions.use_clothes_skill(1, 2)
    actions.noble_phantasm(2, 1).noble_phantasm(3).attack(3, 0)
    actions.end_turn()

    controller = FgoBattleController(141, [team_preset], [actions])
    controller.start_script()


def team_kinpika_fes():
    # 呆毛 孔明 孔明 cba 其他蹭羁绊的
    team_preset = FgoTeamConfiguration([svt_common['呆毛'], svt_common['孔'], svt_common['cba'],
                                        4, 5], [0, 0, 0, 0, 0], svt_common['孔'], 900, 2)
    actions = FgoBattleAction(team_preset)
    # use_skill(servant_id: int, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
    #           enemy_location: int = ENEMY_LOCATION_EMPTY)

    # T1: 呆毛宝石80 + 孔明加攻10 x 2
    actions.begin_turn()
    actions.use_skill(svt_common['呆毛'], 0)
    actions.use_skill(svt_common['孔'], 2).use_support_skill(2)
    actions.noble_phantasm(svt_common['呆毛']).attack(0).attack(1)
    actions.end_turn()
    # T2: 呆毛宝具20 + 孔明30 x 2 + 10 x 2
    actions.begin_turn()
    actions.use_support_skill(0, svt_common['呆毛']).use_skill(svt_common['孔'], 0, svt_common['呆毛'])
    actions.use_skill(svt_common['孔'], 1).use_support_skill(1)
    actions.noble_phantasm(svt_common['呆毛']).attack(0).attack(1)
    actions.end_turn()
    # T3: 呆毛宝具20 + 自充30 + 换人cba50
    actions.begin_turn()
    actions.use_skill(svt_common['呆毛'], 2)
    actions.use_clothes_skill(2, (svt_common['孔'], svt_common['cba']))
    actions.use_skill(svt_common['cba'], 2, svt_common['呆毛'])
    # cba降防 + 呆毛魔放 + 衣服攻击
    actions.use_skill(svt_common['cba'], 1).use_skill(svt_common['呆毛'], 1).use_clothes_skill(0)
    actions.noble_phantasm(svt_common['呆毛']).attack(0).attack(1)
    actions.end_turn()
    # 非的干不过欧的，哈吉马路哟
    controller = FgoBattleController(141, [team_preset], [actions])
    controller.start_script()


def main():
    team_kinpika_fes()


if __name__ == '__main__':
    main()
