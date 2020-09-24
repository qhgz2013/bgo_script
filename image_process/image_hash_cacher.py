# Author: Zhou Xuebin
# Version: 1.1
# Changelog:
# v1.1: changed cacher hash algorithm from bucket to BK tree

from typing import *
import numpy as np
from .bk_tree import BKTree


T = TypeVar('T')


class ImageHashCacher:
    """
    A class for caching image-value pair, using low computation cost and image-oriented hash
    """
    def __init__(self, hash_func: Callable[[np.ndarray], int],
                 hash_conflict_func: Callable[[np.ndarray, np.ndarray], bool], tol: int = 2):
        """
        Default constructor of this cacher
        :param hash_func: A callable functions that maps image to hash code
        :param hash_conflict_func: A callable function indicating two images are same, used for hash conflict detection
        :param tol: The maximum tolerant distance in hamming space to perform a rough similarity query
        """
        self.hash_func = hash_func
        self.hash_conflict_func = hash_conflict_func
        self.hash_tree = BKTree()
        self.tol = tol

    def add_image(self, image: np.ndarray, value: Optional[T] = None):
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
        for candidate_image_list, _ in candidate_conflict_images:
            for candidate_image, value in candidate_image_list:
                if self.hash_conflict_func(image, candidate_image):
                    return
        self.hash_tree.add_node(hash_value, (image, value))

    def contains(self, image: np.ndarray) -> bool:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
        for candidate_image_list, _ in candidate_conflict_images:
            for candidate_image, _ in candidate_image_list:
                if self.hash_conflict_func(image, candidate_image):
                    return True
        return False

    def get_value(self, image: np.ndarray) -> Optional[T]:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
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
