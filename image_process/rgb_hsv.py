import numpy as np
from ._backend_determine import *


@backend_support('rgb_to_hsv', 0)
def _rgb_to_hsv_skimage(img: np.ndarray) -> np.ndarray:
    import skimage.color
    return np.round(skimage.color.rgb2hsv(img) * 255).astype('uint8')


@backend_support('hsv_to_rgb', 0)
def _hsv_to_rgb_skimage(img: np.ndarray) -> np.ndarray:
    import skimage.color
    return np.round(skimage.color.hsv2rgb(img) * 255).astype('uint8')


@backend_support('rgb_to_hsv', 1)
def _rgb_to_hsv_opencv(img: np.ndarray) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.cvtColor(img, cv2.COLOR_RGB2HSV)


@backend_support('hsv_to_rgb', 1)
def _hsv_to_rgb_opencv(img: np.ndarray) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.cvtColor(img, cv2.COLOR_HSV2RGB)


def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    return backend_call('rgb_to_hsv', img=img)


def hsv_to_rgb(img: np.ndarray) -> np.ndarray:
    return backend_call('hsv_to_rgb', img=img)


def benchmark():
    a = np.round(np.random.uniform(0, 255, [128, 128, 3])).astype('uint8')
    from time import time
    t1 = time()
    for _ in range(1000):
        b = _rgb_to_hsv_opencv(a)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        c = _rgb_to_hsv_skimage(a)
    t2 = time() - t2
    t3 = time()
    for _ in range(1000):
        d = _hsv_to_rgb_opencv(a)
    t3 = time() - t3
    t4 = time()
    for _ in range(1000):
        e = _hsv_to_rgb_skimage(a)
    t4 = time() - t4
    print('rgb to hsv conversion (opencv) time: %f' % t1)
    print('rgb to hsv conversion (skimage) time: %f' % t2)
    print('hsv to rgb conversion (opencv) time: %f' % t3)
    print('hsv to rgb conversion (skiamge) time: %f' % t4)
    # noinspection PyUnboundLocalVariable
    print('rgb to hsv mean abs diff: %f' % np.mean(np.abs(b.astype(np.float) - c)))
    # noinspection PyUnboundLocalVariable
    print('hsv to rgb mean abs diff: %f' % np.mean(np.abs(d.astype(np.float) - e)))
