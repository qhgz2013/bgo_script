# Author: Zhou Xuebin
# Version: 1.1
# Changelog:
# v1.1: changed cacher hash algorithm from bucket to BK tree

from typing import *
import numpy as np
from .bk_tree import BKTree


def _compute_gray_alpha(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if len(img.shape) == 3:
        if img.shape[-1] == 4:
            alpha = img[..., -1]
        else:
            alpha = np.full([img.shape[0], img.shape[1]], 255, 'uint8')
        gray = np.mean(img[..., :3], -1)
        return gray, alpha
    else:
        alpha = np.full([img.shape[0], img.shape[1]], 255, 'uint8')
        return img, alpha


def mean_gray_diff_err(a: np.ndarray, b: np.ndarray, mean_gray_diff_threshold: Optional[float] = 20) -> \
        Union[bool, float]:
    """
    A common used hash conflict function, compute the absolute difference between two images, returns whether the mean
    value is less than the threshold, indicating that there are the same images.
    :param a: image array, shapes (h, w) or (h, w, c), if c > 1,
    the image will be reshape to (h, w) by computing the mean value for each channel
    :param b: image array, shapes (h, w) or (h, w, c)
    :param mean_gray_diff_threshold: the threshold for comparing two images, if none, returns the difference
    :return: whether mean absolute difference between two images are less than specified threshold, or its value
    """
    if len(a.shape) > 3 or len(b.shape) > 3:
        raise ValueError('unsupported input shape, input image must shapes (h, w, c) or (h, w)')
    if a.shape[:2] != b.shape[:2]:
        raise ValueError('invalid comparison: %s and %s' % (str(a.shape[:2]), str(b.shape[:2])))
    a, alpha_a = _compute_gray_alpha(a)
    b, alpha_b = _compute_gray_alpha(b)
    gray_diff_err = np.abs(a - b) * (np.minimum(alpha_a, alpha_b) / 255.0)
    gray_diff_err = np.mean(gray_diff_err)
    return gray_diff_err if mean_gray_diff_threshold is None else gray_diff_err < mean_gray_diff_threshold


T = TypeVar('T')


class ImageHashCacher:
    """
    A class for caching image-value pair, using low computation cost and image-oriented hash
    """
    def __init__(self, hash_func: Callable[[np.ndarray], int],
                 hash_conflict_func: Callable[[np.ndarray, np.ndarray], bool]):
        """
        Default constructor of this cacher
        :param hash_func: A callable functions that maps image to hash code
        :param hash_conflict_func: A callable function indicating two images are same, used for hash conflict detection
        """
        self.hash_func = hash_func
        self.hash_conflict_func = hash_conflict_func
        self.hash_tree = BKTree()

    def add_image(self, image: np.ndarray, value: Optional[T] = None):
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=2)
        for candidate_image_list, _ in candidate_conflict_images:
            for candidate_image, value in candidate_image_list:
                if self.hash_conflict_func(image, candidate_image):
                    return
        self.hash_tree.add_node(hash_value, (image, value))

    def contains(self, image: np.ndarray) -> bool:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=2)
        for candidate_image_list, _ in candidate_conflict_images:
            for candidate_image, _ in candidate_image_list:
                if self.hash_conflict_func(image, candidate_image):
                    return True
        return False

    def get_value(self, image: np.ndarray) -> Optional[T]:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=2)
        for candidate_image_list, _ in candidate_conflict_images:
            for candidate_image, value in candidate_image_list:
                if self.hash_conflict_func(image, candidate_image):
                    return value
        raise KeyError('image not found')

    def __contains__(self, item):
        return self.contains(item)

    def __getitem__(self, item):
        return self.get_value(item)

    def __setitem__(self, key, value):
        self.add_image(key, value)

    def get(self, image: np.ndarray, default_value: Optional[Any] = None) -> Optional[Any]:
        try:
            return self.get_value(image)
        except KeyError:
            return default_value
