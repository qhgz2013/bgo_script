from ._backend_determine import *
import numpy as np
import logging

logger = logging.getLogger('bgo_script.image_process')
_warn_non_ascii_path_opencv = False


@backend_support('imread', 0)
def _imread_opencv(path: str) -> np.ndarray:
    global _warn_non_ascii_path_opencv
    if not _warn_non_ascii_path_opencv:
        _warn_non_ascii_path_opencv = True
        logger.warning('Known issue: imread from package OpenCV does not support non-ascii path')
    import cv2
    # noinspection PyUnresolvedReferences
    value = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if len(value.shape) == 3:
        # reverse BGRA to RGBA
        value[..., :3] = value[..., 2::-1]
    return value


@backend_support('imread', 2)
def _imread_pil(path: str) -> np.ndarray:
    from PIL import Image
    with open(path, 'rb') as f:
        img = np.asarray(Image.open(f), dtype='uint8')
    return img


@backend_support('imread', 1)
def _imread_skimage(path: str) -> np.ndarray:
    import skimage.io
    return skimage.io.imread(path)


def imread(path: str) -> np.ndarray:
    return backend_call('imread', path=path)


def benchmark():
    from time import time
    name = '%d.png' % int(time())
    a = np.round(np.random.uniform(0, 255, [512, 512, 4])).astype('uint8')
    from PIL import Image
    with open(name, 'wb') as f1:
        Image.fromarray(a).save(f1, 'PNG')
    t1 = time()
    try:
        for _ in range(1000):
            b = _imread_opencv(name)
    except Exception as ex:
        print(ex)
        b = None
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        c = _imread_pil(name)
    t2 = time() - t2
    t3 = time()
    for _ in range(1000):
        d = _imread_skimage(name)
    t3 = time() - t3
    print('imread opencv time: %f' % t1)
    print('imread pil time: %f' % t2)
    print('imread skimage time: %f' % t3)
    # noinspection PyUnboundLocalVariable
    if b is None:
        print('imread for opencv failed')
    else:
        # noinspection PyUnboundLocalVariable
        print('mean abs diff opencv: %f' % np.mean(np.abs(a.astype(np.float) - b)))
    # noinspection PyUnboundLocalVariable
    print('mean abs diff pil: %f' % np.mean(np.abs(a.astype(np.float) - c)))
    # noinspection PyUnboundLocalVariable
    print('mean abs diff skimage: %f' % np.mean(np.abs(a.astype(np.float) - d)))
    import os
    os.remove(name)
