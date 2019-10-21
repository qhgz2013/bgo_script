from mumu_attach import MumuSimulatorAttacher
from battle_controller import FgoBattleController
from team_config import FgoTeamConfiguration
import cv2
import matplotlib.pyplot as plt
import numpy as np
from cv_positioning import *
import skimage.io

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


def main():
    # t()
    # plot_axis()
    team_preset = FgoTeamConfiguration([1, 2, 3, 4, 5], [0, 0, 0, 0, 0], 215, 0, 2)
    controller = FgoBattleController(141, [team_preset], None)
    controller.start_script()


if __name__ == '__main__':
    main()
