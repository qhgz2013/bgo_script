import scipy.fftpack
import numpy as np
import cv2


def perception_hash(img: np.ndarray, hash_size: int = 4, high_freq_factor: int = 4) -> int:
    """
    Perception Hash (pHash) for fast image matching
    :param img: input image, with shape (h, w, c) or (h, w)
    :param hash_size: the dimension of hash, the returned hash will have bit length of hash_size ^ 2
    :param high_freq_factor: the coefficient used for capturing image high frequent features
    :return: the hash code, code address ranges [0, 2^(hash_size^2))
    """
    if len(img.shape) == 3:
        img = np.mean(img, -1)
    image_size = hash_size * high_freq_factor
    # noinspection PyUnresolvedReferences
    img = cv2.resize(img, (image_size, image_size), interpolation=cv2.INTER_CUBIC)
    dct = scipy.fftpack.dct(img)
    dct_low_freq = dct[:hash_size, 1:hash_size+1]
    avg_dct = np.mean(dct_low_freq)
    diff = dct_low_freq > avg_dct
    hash_bit = np.reshape(diff, -1)
    code = 0
    for bit in hash_bit:
        code = (code << 1) | int(bit)
    return code
