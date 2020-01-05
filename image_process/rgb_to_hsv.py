import numpy as np
from ._backend_determine import backend_determine
from logging import root

_selected_default_func = None


def _rgb_to_hsv_skimage(img: np.ndarray) -> np.ndarray:
    import skimage.color
    return np.round(skimage.color.rgb2hsv(img) * 255).astype('uint8')


def _rgb_to_hsv_opencv(img: np.ndarray) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.cvtColor(img, cv2.COLOR_RGB2HSV)


def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    global _selected_default_func
    if _selected_default_func is not None:
        return _selected_default_func(img)
    func_list = [_rgb_to_hsv_skimage, _rgb_to_hsv_opencv]
    _selected_default_func, img = backend_determine(func_list, (img,))
    root.info('selected %s for image RGB to HSV conversion' % str(_selected_default_func))
    return img
