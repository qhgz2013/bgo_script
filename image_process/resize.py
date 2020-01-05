import numpy as np
from ._backend_determine import backend_determine
from logging import root

_selected_default_func = None


def _resize_opencv(img: np.ndarray, width: int, height: int) -> np.ndarray:
    import cv2
    # noinspection PyUnresolvedReferences
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)


def _resize_skimage(img: np.ndarray, width: int, height: int) -> np.ndarray:
    import skimage.transform
    return np.round(skimage.transform.resize(img, (height, width)) * 255).astype('uint8')


def _resize_pil(img: np.ndarray, width: int, height: int) -> np.ndarray:
    from PIL import Image
    img_obj = Image.fromarray(img)
    return np.asarray(img_obj.resize((width, height), Image.ANTIALIAS), dtype='uint8')


def resize(img: np.ndarray, width: int, height: int) -> np.ndarray:
    global _selected_default_func
    if _selected_default_func is not None:
        return _selected_default_func(img, width, height)
    func_list = [_resize_pil, _resize_skimage, _resize_opencv]
    _selected_default_func, resized_img = backend_determine(func_list, (img, width, height))
    root.info('selected %s for image resizing' % str(_selected_default_func))
    return resized_img
