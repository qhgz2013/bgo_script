from attacher import MumuAttacher
import matplotlib.pyplot as plt
from cv_positioning import *


if __name__ == '__main__':
    img = MumuAttacher().get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y).copy()
    for i in range(0, img.shape[0], 10):
        img[i, :, 0] = 255
    for i in range(0, img.shape[1], 10):
        img[:, i, 1] = 255

    dpi = plt.rcParams['figure.dpi']
    fig = plt.figure(figsize=(img.shape[1] / dpi * 1.1, img.shape[0] / dpi * 1.1))
    plt.imshow(img)
    plt.show()
