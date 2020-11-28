import numpy as np
from ._backend_determine import *


@backend_support('resize', 1)
def _resize_opencv(img: np.ndarray, width: int, height: int) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)


@backend_support('resize', 0)
def _resize_skimage(img: np.ndarray, width: int, height: int) -> np.ndarray:
    import skimage.transform
    return np.round(skimage.transform.resize(img, (height, width)) * 255).astype('uint8')


@backend_support('resize', 2)
def _resize_pil(img: np.ndarray, width: int, height: int) -> np.ndarray:
    from PIL import Image
    img_obj = Image.fromarray(img)
    return np.asarray(img_obj.resize((width, height), Image.ANTIALIAS), dtype='uint8')


def resize(img: np.ndarray, width: int, height: int) -> np.ndarray:
    return backend_call('resize', img=img, width=width, height=height)


def benchmark():
    a = np.round(np.random.uniform(0, 255, [128, 128, 4])).astype('uint8')
    from time import time
    t1 = time()
    for _ in range(1000):
        b = _resize_opencv(a, 96, 96)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        c = _resize_pil(a, 96, 96)
    t2 = time() - t2
    t3 = time()
    for _ in range(1000):
        d = _resize_skimage(a, 96, 96)
    t3 = time() - t3
    print('resize opencv (png with alpha) time: %f' % t1)
    print('resize pil (png with alpha) time: %f' % t2)
    print('resize skimage (png with alpha) time: %f' % t3)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff (opencv, pil): %f' % np.mean(np.abs(b.astype(np.float) - c)))
    # noinspection PyUnboundLocalVariable
    print('mean abs diff (pil, skimage): %f' % np.mean(np.abs(c.astype(np.float) - d)))
    print('mean abs diff (opencv, skimage): %f' % np.mean(np.abs(b.astype(np.float) - d)))
