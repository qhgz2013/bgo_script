from attacher import MumuAttacher
from cv_positioning import *
from skimage.io import imsave
import numpy as np


def _generate_attack_button_mask() -> np.ndarray:
    dx = CV_ATTACK_BUTTON_X2 - CV_ATTACK_BUTTON_X1
    dy = CV_ATTACK_BUTTON_Y2 - CV_ATTACK_BUTTON_Y1
    d = min(dx, dy)
    cx = dx / 2
    cy = dy / 2
    y, x = np.ogrid[:dx, :dy]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    mask = r < (d / 2)
    return mask.astype('uint8') * 255


def main():
    attacher = MumuAttacher()
    # MAKE SURE YOU'RE IN BATTLE
    img = attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
    battle_button = img[CV_ATTACK_BUTTON_Y1:CV_ATTACK_BUTTON_Y2, CV_ATTACK_BUTTON_X1:CV_ATTACK_BUTTON_X2, :]
    mask = _generate_attack_button_mask()
    battle_button = np.concatenate([battle_button, np.expand_dims(mask, 2)], 2)
    imsave('../cv_data/attack_button.png', battle_button)


if __name__ == '__main__':
    main()
