from attacher import MumuAttacher
from cv_positioning import *
from skimage.io import imsave


def main():
    attacher = MumuAttacher()
    # MAKE SURE YOU'RE IN BATTLE
    img = attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
    battle_button = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y1):
                        int(CV_SCREENSHOT_RESOLUTION_Y*CV_ATTACK_BUTTON_Y2),
                        int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X1):
                        int(CV_SCREENSHOT_RESOLUTION_X*CV_ATTACK_BUTTON_X2), :]
    imsave('../cv_data/attack_button.png', battle_button)


if __name__ == '__main__':
    main()
