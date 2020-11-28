import numpy as np
from ._backend_determine import *


@backend_support('gauss_blur', 1)
def _gauss_blur_opencv(img: np.ndarray, radius: int) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    if radius & 1:
        return cv2.GaussianBlur(img, (radius, radius), 0)
    else:
        return cv2.blur(img, (radius, radius))


@backend_support('gauss_blur', 0)
def _gauss_blur_pil(img: np.ndarray, radius: int) -> np.ndarray:
    from PIL import Image, ImageFilter
    return np.asarray(Image.fromarray(img).filter(ImageFilter.GaussianBlur(radius)), dtype='uint8')


# NOTE 1: gauss blur between PIL and OpenCV is different!
# NOTE 2: gauss blur using PIL is much slower than OpenCV!
def gauss_blur(img: np.ndarray, radius: int) -> np.ndarray:
    return backend_call('gauss_blur', img=img, radius=radius)


def benchmark():
    rnd = np.round(np.random.uniform(50, 150, [512, 512, 4])).astype('uint8')
    # test with alpha
    from time import time
    t1 = time()
    for _ in range(1000):
        a = _gauss_blur_opencv(rnd, 3)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        b = _gauss_blur_pil(rnd, 3)
    t2 = time() - t2
    print('gauss blur (alpha) opencv time: %f' % t1)
    print('gauss blur (alpha) pil time: %f' % t2)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff: %f' % np.mean(np.abs(a.astype(np.float) - b)))
    # test without alpha
    t1 = time()
    for _ in range(1000):
        a = _gauss_blur_opencv(rnd[..., :3], 3)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        b = _gauss_blur_pil(rnd[..., :3], 3)
    t2 = time() - t2
    print('gauss blur (no alpha) opencv time: %f' % t1)
    print('gauss blur (no alpha) pil time: %f' % t2)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff: %f' % np.mean(np.abs(a.astype(np.float) - b)))
    # test kernel size = multiple of 2
    t1 = time()
    for _ in range(1000):
        a = _gauss_blur_opencv(rnd[..., :3], 2)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        b = _gauss_blur_pil(rnd[..., :3], 2)
    t2 = time() - t2
    print('gauss blur (2x kernel) opencv time: %f' % t1)
    print('gauss blur (2x kernel) pil time: %f' % t2)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff: %f' % np.mean(np.abs(a.astype(np.float) - b)))
