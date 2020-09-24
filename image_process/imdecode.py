import numpy as np
from ._backend_determine import backend_determine
import logging

_selected_default_func = None
logger = logging.getLogger('bgo_script.image_process')


def _imdecode_opencv(b: bytes) -> np.ndarray:
    import cv2
    b = np.array(bytearray(b), 'uint8')
    # noinspection PyUnresolvedReferences
    return cv2.imdecode(b, cv2.IMREAD_COLOR)


def _imdecode_pil(b: bytes) -> np.ndarray:
    from PIL import Image
    from io import BytesIO
    with BytesIO(b) as f:
        img = Image.open(f)
        return np.asarray(img, 'uint8')


def imdecode(b: bytes) -> np.ndarray:
    global _selected_default_func
    if _selected_default_func is not None:
        return _selected_default_func(b)
    func_list = [_imdecode_pil, _imdecode_opencv]
    _selected_default_func, img = backend_determine(func_list, (b,))
    logger.debug('selected %s for image decode' % str(_selected_default_func))
    return img
