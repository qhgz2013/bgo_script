from attacher import MumuAttacher
from skimage.io import imsave
import numpy as np
import image_process
import resolution_adapter
from basic_class import Resolution, Rect


def _generate_attack_button_mask(button_rect: Rect) -> np.ndarray:
    dx = button_rect.width
    dy = button_rect.height
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
    img = attacher.get_screenshot()
    detection_defs = resolution_adapter.DetectionDefFactory.get_detection_def(Resolution(img.shape[0], img.shape[1]))
    target_resolution = detection_defs.get_target_resolution()
    if target_resolution is not None:
        img = image_process.resize(img, target_resolution.width, target_resolution.height)
    button_rect = detection_defs.get_attack_button_rect()
    battle_button = img[button_rect.y1:button_rect.y2, button_rect.x1:button_rect.x2, :]
    mask = _generate_attack_button_mask(button_rect)
    battle_button = np.concatenate([battle_button, np.expand_dims(mask, 2)], 2)
    imsave('../cv_data/attack_button.png', battle_button)


if __name__ == '__main__':
    main()
