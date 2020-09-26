# Author: Zhou Xuebin
# Version: 1.1
# Changelog:
# v1.1: changed cacher hash algorithm from bucket to BK tree

from typing import *
import numpy as np
from .bk_tree import BKTree
import logging


T = TypeVar('T')
logger = logging.getLogger('bgo_script.image_process')


class ImageHashCacher:
    """
    A class for caching image-value pair, using low computation cost and image-oriented hash
    """
    def __init__(self, hash_func: Callable[[np.ndarray], int],
                 hash_conflict_func: Callable[[np.ndarray, np.ndarray], float], hash_code_tol: int = 2,
                 conflict_tol: float = 10):
        """
        Default constructor of this cacher
        :param hash_func: A callable functions that maps image to hash code
        :param hash_conflict_func: A callable function indicating two images are same, used for hash conflict detection
        :param hash_code_tol: The maximum tolerant distance in hamming space to perform a rough similarity query
        :param conflict_tol: The tolerance of hash conflict function, if the hash_conflict_func returned the value less
            than this tolerance, it will regard two input images as the same image
        """
        self.hash_func = hash_func
        self.hash_conflict_func = hash_conflict_func
        self.hash_tree = BKTree()
        self.tol = hash_code_tol
        self.conflict_tol = conflict_tol

    def add_image(self, image: np.ndarray, value: Optional[T] = None) -> bool:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
        for candidate_image_list, _, _ in candidate_conflict_images:
            for candidate_image, _ in candidate_image_list:
                v = self.hash_conflict_func(image, candidate_image)
                if (isinstance(v, bool) and v) or (isinstance(v, float) and v < self.conflict_tol):
                    return False
        logger.debug('Added value "%s" in node %d' % (str(value), hash_value))
        self.hash_tree.add_node(hash_value, (image, value))
        return True

    def contains(self, image: np.ndarray) -> bool:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
        for candidate_image_list, key, dis in candidate_conflict_images:
            for candidate_image, val in candidate_image_list:
                v = self.hash_conflict_func(image, candidate_image)
                logger.debug('Candidate from node %d (distance: %d) with value %s: conflict func returned %s' %
                             (key, dis, str(val), str(v)))
                if (isinstance(v, bool) and v) or (isinstance(v, float) and v < self.conflict_tol):
                    return True
        return False

    def get_value(self, image: np.ndarray) -> Optional[T]:
        if type(image) != np.ndarray:
            raise TypeError('image must be numpy.ndarray instance')
        hash_value = self.hash_func(image)
        candidate_conflict_images = self.hash_tree.approximate_query(hash_value, tol=self.tol)
        for candidate_image_list, key, dis in candidate_conflict_images:
            for candidate_image, value in candidate_image_list:
                v = self.hash_conflict_func(image, candidate_image)
                logger.debug('Candidate from node %d (distance: %d) with value %s: conflict func returned %s' %
                             (key, dis, str(value), str(v)))
                if (isinstance(v, bool) and v) or (isinstance(v, float) and v < self.conflict_tol):
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
