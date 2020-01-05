from ._backend_determine import backend_determine
import numpy as np
from logging import root

_selected_default_func = None


def _imread_opencv(path: str) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return np.flip(cv2.imread(path), -1)


def _imread_pil(path: str) -> np.ndarray:
    from PIL import Image
    with open(path, 'rb') as f:
        img = np.asarray(Image.open(f), dtype='uint8')
    return img


def _imread_skimage(path: str) -> np.ndarray:
    import skimage.io
    return skimage.io.imread(path)


def imread(path: str) -> np.ndarray:
    global _selected_default_func
    if _selected_default_func is not None:
        return _selected_default_func(path)
    func_list = [_imread_pil, _imread_skimage, _imread_opencv]
    _selected_default_func, img = backend_determine(func_list, (path,))
    root.info('selected %s for image reading (from path)' % str(_selected_default_func))
    return img
