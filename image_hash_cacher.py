from typing import *
import numpy as np


def mean_gray_diff_err(a: np.ndarray, b: np.ndarray, mean_gray_diff_threshold: float = 20) -> bool:
    if len(a.shape) > 3 or len(b.shape) > 3:
        raise ValueError('unsupported input shape, input image must shapes (h, w, c) or (h, w)')
    if a.shape[:2] != b.shape[:2]:
        raise ValueError('invalid comparison: %s and %s' % (str(a.shape[:2]), str(b.shape[:2])))
    if len(a.shape) == 3:
        a = np.mean(a, -1)
    if len(b.shape) == 3:
        b = np.mean(b, -1)
    gray_diff_err = np.mean(np.abs(a - b))
    # print('[debug] mean gray different error: %f' % gray_diff_err)
    return gray_diff_err < mean_gray_diff_threshold


class ImageHashCacher:
    def __init__(self, hash_func: Callable[[np.ndarray], int],
                 hash_conflict_func: Callable[[np.ndarray, np.ndarray], bool]):
        self.hash_func = hash_func
        self.hash_conflict_func = hash_conflict_func
        self.hash_dict = dict()

    def add_image(self, image: np.ndarray, value: Optional[Any] = None):
        if type(image) != np.ndarray:
            raise TypeError('contains operator can be applied for numpy.ndarray instance')
        hash_value = self.hash_func(image)
        if hash_value in self.hash_dict:
            candidate_conflict_images = self.hash_dict[hash_value]
            for candidate_image, _ in candidate_conflict_images:
                if self.hash_conflict_func(image, candidate_image):
                    return
            self.hash_dict[hash_value].append((image, value))
        else:
            self.hash_dict[hash_value] = [(image, value)]
        # print('[debug] added image hash %x with value %s' % (hash_value, str(value)))

    def contains(self, image: np.ndarray):
        if type(image) != np.ndarray:
            raise TypeError('contains operator can be applied for numpy.ndarray instance')
        hash_value = self.hash_func(image)
        # print('[debug] query image hash: %x' % hash_value)
        if hash_value not in self.hash_dict:
            return False
        for candidate_image, _ in self.hash_dict[hash_value]:
            if self.hash_conflict_func(image, candidate_image):
                return True
        return False

    def get_value(self, image: np.ndarray) -> Optional[Any]:
        if type(image) != np.ndarray:
            raise TypeError('contains operator can be applied for numpy.ndarray instance')
        hash_value = self.hash_func(image)
        # print('[debug] query image hash: %x' % hash_value)
        if hash_value not in self.hash_dict:
            raise KeyError('image not found')
        for candidate_image, value in self.hash_dict[hash_value]:
            if self.hash_conflict_func(image, candidate_image):
                # print('[debug] returned %s' % str(value))
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
