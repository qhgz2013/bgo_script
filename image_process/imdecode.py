import numpy as np
from ._backend_determine import *


@backend_support('imdecode', 0)
def _imdecode_opencv(b: bytes) -> np.ndarray:
    import cv2
    b = np.array(bytearray(b), 'uint8')
    # noinspection PyUnresolvedReferences
    value = cv2.imdecode(b, cv2.IMREAD_UNCHANGED)
    if len(value.shape) == 3:
        # reverse BGRA to RGBA
        value[..., :3] = value[..., 2::-1]
    return value


@backend_support('imdecode', 1)
def _imdecode_pil(b: bytes) -> np.ndarray:
    from PIL import Image
    from io import BytesIO
    with BytesIO(b) as f:
        img = Image.open(f)
        return np.asarray(img, 'uint8')


def imdecode(b: bytes) -> np.ndarray:
    return backend_call('imdecode', b=b)


# noinspection DuplicatedCode
def benchmark():
    from PIL import Image
    from io import BytesIO
    from time import time
    a = np.round(np.random.uniform(0, 255, [512, 512, 4])).astype('uint8')
    with BytesIO() as f1:
        Image.fromarray(a).save(f1, 'PNG')
        f1.seek(0)
        blob = f1.read()
    t1 = time()
    for _ in range(1000):
        bb = _imdecode_pil(blob)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        c = _imdecode_opencv(blob)
    t2 = time() - t2
    print('imdecode opencv (png with alpha) time: %f' % t2)
    print('imdecode pil (png with alpha) time: %f' % t1)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff: %f' % np.mean(np.abs(bb.astype(np.float) - c)))
    with BytesIO() as f1:
        Image.fromarray(a[..., :3]).save(f1, 'PNG')
        f1.seek(0)
        blob = f1.read()
    t1 = time()
    for _ in range(1000):
        bb = _imdecode_pil(blob)
    t1 = time() - t1
    t2 = time()
    for _ in range(1000):
        c = _imdecode_opencv(blob)
    t2 = time() - t2
    print('imdecode opencv (png without alpha) time: %f' % t2)
    print('imdecode pil (png without alpha) time: %f' % t1)
    # noinspection PyUnboundLocalVariable
    print('mean abs diff: %f' % np.mean(np.abs(bb.astype(np.float) - c)))
