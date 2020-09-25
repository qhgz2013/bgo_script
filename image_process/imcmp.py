__all__ = ['split_gray_alpha', 'split_rgb_alpha', 'mean_gray_diff_err', 'mean_hsv_diff_err']

import numpy as np
from typing import *
from .rgb_hsv import rgb_to_hsv


def split_rgb_alpha(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Split an image with shape (h, w) or (h, w, 3) in RGB format, or (h, w, 4) in RGBA format into RGB value shapes
     (h, w, 3) and alpha mask shapes (h, w)

    :param img: Input image with shape (h, w), (h, w, 3) or (h, w, 4)
    :return: The tuple of RGB value and the alpha mask
    """
    if len(img.shape) == 3:
        if img.shape[-1] == 4:
            alpha = img[..., -1]
        elif img.shape[-1] == 3:
            alpha = np.full([img.shape[0], img.shape[1]], 255, 'uint8')
        else:
            raise ValueError('Incompatible input image shape: %s' % str(img.shape))
        return img[..., :3], alpha
    elif len(img.shape) == 2:
        alpha = np.full([img.shape[0], img.shape[1]], 255, 'uint8')
        img = np.dstack([img] * 3)
        return img, alpha
    else:
        raise ValueError('Incompatible input image shape: %s' % str(img.shape))


def split_gray_alpha(img: np.ndarray, fast_compute: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Split an image with shape (h, w) or (h, w, 3) in RGB format, or (h, w, 4) in RGBA format into gray scale value
    shapes (h, w) and alpha mask shapes (h, w)

    :param img: Input image with shape (h, w), (h, w, 3) or (h, w, 4)
    :param fast_compute: Use average over RGB channel if true, or proceed standard RGB to gray conversion
    :return: The tuple of gray scale value and the alpha mask
    """
    img, alpha = split_rgb_alpha(img)
    if fast_compute:
        gray = np.mean(img[..., :3], -1)
    else:
        w = np.array([[0.2126], [0.7152], [0.0722]])
        gray = np.squeeze(np.round(np.dot(img.astype(np.float), w)).astype('uint8'))
    return gray, alpha


def _check_shape_equality(a: np.ndarray, b: np.ndarray):
    if len(a.shape) > 3 or len(b.shape) > 3 or len(a.shape) < 2 or len(b.shape) < 2:
        raise ValueError('Unsupported input shape, input image must shapes (h, w, c) or (h, w)')
    if a.shape[:2] != b.shape[:2]:
        raise ValueError('Invalid comparison: %s and %s' % (str(a.shape[:2]), str(b.shape[:2])))


def mean_gray_diff_err(a: np.ndarray, b: np.ndarray, diff_threshold: Optional[float] = 10,
                       fast_compute: bool = True) -> Union[bool, float]:
    """
    Compute the absolute difference between two gray-scale images, returns whether the mean value is less than the
    threshold, indicating that there are the same images (if mean_gray_diff_threshold is given), or the absolute
    difference of the two images.

    :param a: image array, shapes (h, w) or (h, w, c)
    :param b: image array, shapes (h, w) or (h, w, c)
    :param diff_threshold: the threshold for comparing two images, if none, returns the difference
    :param fast_compute: Use average over RGB channel if true, or proceed standard RGB to gray conversion
    :return: whether mean absolute difference between two images are less than specified threshold, or its value
    """
    _check_shape_equality(a, b)
    a, alpha_a = split_gray_alpha(a, fast_compute)
    b, alpha_b = split_gray_alpha(b, fast_compute)
    gray_diff_err = np.abs(a - b) * (np.minimum(alpha_a, alpha_b) / 255.0)
    gray_diff_err = np.mean(gray_diff_err)
    return gray_diff_err if diff_threshold is None else gray_diff_err < diff_threshold


def mean_hsv_diff_err(a: np.ndarray, b: np.ndarray, fmt_a: str = 'rgb', fmt_b: str = 'rgb',
                      diff_threshold: Optional[float] = 5) -> Union[bool, float]:
    """
    Compute the difference between two image using HSV color space with new difference measuring method

    :param a: image array, shapes (h, w, c) or (h, w), NOTE: gray-scale image with shape (h, w) may perform bad here
    :param b: image array, shapes (h, w, c) or (h, w)
    :param fmt_a: input image format for param a, one of "rgb", "hsv"
    :param fmt_b: input image format for param b, one of "rgb", "hsv"
    :param diff_threshold: the threshold for comparing two images, if none, returns the difference
    :return: whether HSV difference between two images are less than specified threshold, or its value if the threshold
        leaves empty
    """
    _check_shape_equality(a, b)
    fmt_a, fmt_b = fmt_a.lower(), fmt_b.lower()
    assert all([x in ['rgb', 'hsv'] for x in [fmt_a, fmt_b]]), 'Invalid input image format'
    if fmt_a == 'rgb':
        rgb_a, alpha_a = split_rgb_alpha(a)
        hsv_a = rgb_to_hsv(rgb_a)
    else:
        hsv_a, alpha_a = split_rgb_alpha(a)
    if fmt_b == 'rgb':
        rgb_b, alpha_b = split_rgb_alpha(b)
        hsv_b = rgb_to_hsv(rgb_b)
    else:
        hsv_b, alpha_b = split_rgb_alpha(b)
    ovr_diff = np.abs(hsv_a.astype(np.float) - hsv_b)
    # hue ring difference
    hue_diff = ovr_diff[..., 0]
    hue_diff = np.minimum(hue_diff, 255 - hue_diff)
    # value (brightness) coefficient
    val_diff = ovr_diff[..., 2] / 255.0
    err = np.mean(hue_diff * val_diff)
    return err if diff_threshold is None else err < diff_threshold
