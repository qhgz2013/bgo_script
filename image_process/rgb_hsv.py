import numpy as np
from ._backend_determine import backend_determine
import logging

_selected_rgb2hsv_func = None
_selected_hsv2rgb_func = None
logger = logging.getLogger('bgo_script.image_process')


def _rgb_to_hsv_skimage(img: np.ndarray) -> np.ndarray:
    import skimage.color
    return np.round(skimage.color.rgb2hsv(img) * 255).astype('uint8')


def _hsv_to_rgb_skimage(img: np.ndarray) -> np.ndarray:
    import skimage.color
    return np.round(skimage.color.hsv2rgb(img) * 255).astype('uint8')


def _rgb_to_hsv_opencv(img: np.ndarray) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.cvtColor(img, cv2.COLOR_RGB2HSV)


def _hsv_to_rgb_opencv(img: np.ndarray) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.cvtColor(img, cv2.COLOR_HSV2RGB)


def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    global _selected_rgb2hsv_func
    if _selected_rgb2hsv_func is not None:
        return _selected_rgb2hsv_func(img)
    func_list = [_rgb_to_hsv_skimage, _rgb_to_hsv_opencv]
    _selected_rgb2hsv_func, img = backend_determine(func_list, (img,))
    logger.debug('selected %s for image RGB to HSV conversion' % str(_selected_rgb2hsv_func))
    return img


def hsv_to_rgb(img: np.ndarray) -> np.ndarray:
    global _selected_hsv2rgb_func
    if _selected_hsv2rgb_func is not None:
        return _selected_hsv2rgb_func(img)
    func_list = [_hsv_to_rgb_skimage, _hsv_to_rgb_opencv]
    _selected_hsv2rgb_func, img = backend_determine(func_list, (img,))
    logger.debug('selected %s for image HSV to RGB conversion' % str(_selected_rgb2hsv_func))
    return img
