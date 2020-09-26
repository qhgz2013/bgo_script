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


def _avg(a, b):
    return (a + b) / 2


def _abs_diff(a, b):
    return np.abs(a - b)


_alpha_mode_handle_dict = {
    'min': np.minimum,
    'max': np.maximum,
    'avg': _avg,
}
_v_mode_handle_dict = dict(_alpha_mode_handle_dict)
_v_mode_handle_dict['diff'] = _abs_diff


def mean_gray_diff_err(a: np.ndarray, b: np.ndarray, fast_compute: bool = True, alpha_mode: str = 'min') -> float:
    """
    Compute the absolute difference between two gray-scale images, returns the absolute difference of the two images.

    :param a: image array, shapes (h, w) or (h, w, c)
    :param b: image array, shapes (h, w) or (h, w, c)
    :param fast_compute: Use average over RGB channel if true, or proceed standard RGB to gray conversion
    :param alpha_mode: One of the "min", "max", or "avg", indicating using the minimum / maximum / mean alpha value
        from two images
    :return: whether mean absolute difference between two images are less than specified threshold, or its value
    """
    _check_shape_equality(a, b)
    func = _alpha_mode_handle_dict[alpha_mode.lower()]
    a, alpha_a = split_gray_alpha(a, fast_compute)
    b, alpha_b = split_gray_alpha(b, fast_compute)
    alpha_mask = func(alpha_a.astype(np.float), alpha_b.astype(np.float)) / 255.0
    gray_diff_err = np.abs(a.astype(np.float) - b.astype(np.float)) * alpha_mask
    gray_diff_err = float(np.mean(gray_diff_err))
    return gray_diff_err


def mean_hsv_diff_err(a: np.ndarray, b: np.ndarray, fmt_a: str = 'rgb', fmt_b: str = 'rgb', v_mode: str = 'diff',
                      alpha_mode: str = 'min') -> float:
    """
    Compute the difference between two image using HSV color space with new difference measuring method

    :param a: image array, shapes (h, w, c) or (h, w), NOTE: gray-scale image with shape (h, w) may perform bad here
    :param b: image array, shapes (h, w, c) or (h, w)
    :param fmt_a: input image format for param a, one of "rgb", "hsv"
    :param fmt_b: input image format for param b, one of "rgb", "hsv"
    :param v_mode: the mode for handling value (brightness) of two image, one of "diff" (compute the absolute
        difference), "min" (compute the minimum brightness), "max", or "avg"
    :param alpha_mode: One of the "min", "max", or "avg", indicating using the minimum / maximum / mean alpha value
        from two images
    :return: HSV difference between two images
    """
    _check_shape_equality(a, b)
    fmt_a, fmt_b = fmt_a.lower(), fmt_b.lower()
    assert all([x in ['rgb', 'hsv'] for x in [fmt_a, fmt_b]]), 'Invalid input image format'
    alpha_func = _alpha_mode_handle_dict[alpha_mode.lower()]
    value_func = _v_mode_handle_dict[v_mode.lower()]
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
    alpha_mask = alpha_func(alpha_a.astype(np.float), alpha_b.astype(np.float)) / 255.0
    # ovr_diff = np.abs(hsv_a.astype(np.float) - hsv_b)
    # hue ring difference
    hue_diff = np.abs(hsv_a[..., 0].astype(np.float) - hsv_b[..., 0])
    hue_diff = np.minimum(hue_diff, 255 - hue_diff)
    # value (brightness)
    val_diff = value_func(hsv_a[..., 2].astype(np.float), hsv_b[..., 2]) / 255.0
    err = float(np.mean(hue_diff * val_diff * alpha_mask))
    return err
