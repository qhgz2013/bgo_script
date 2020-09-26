# B-K Tree, original implemented in project image-hash
# Author: Zhou Xuebin
# Version: 1.0
# Changelog:
#

import numpy as np
from typing import *

# quick hamming distance lookup
_nbits = np.array(
      [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, 1, 2, 2, 3, 2, 3, 3,
       4, 2, 3, 3, 4, 3, 4, 4, 5, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4,
       4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 1, 2, 2, 3, 2,
       3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5,
       4, 5, 5, 6, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4,
       5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3,
       3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 2,
       3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4, 5, 4, 5, 5, 6,
       4, 5, 5, 6, 5, 6, 6, 7, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5,
       6, 3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 3, 4, 4, 5, 4, 5,
       5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6,
       7, 7, 8], dtype=np.uint8)


def hamming_distance_i64(x: int, y: int) -> int:
    xor_result = x ^ y
    return _nbits[xor_result & 0xff] + _nbits[(xor_result >> 8) & 0xff] + _nbits[(xor_result >> 16) & 0xff] + \
        _nbits[(xor_result >> 24) & 0xff] + _nbits[(xor_result >> 32) & 0xff] + _nbits[(xor_result >> 40) & 0xff] + \
        _nbits[(xor_result >> 48) & 0xff] + _nbits[(xor_result >> 56) & 0xff]


def hamming_distance_i128(x: int, y: int) -> int:
    return hamming_distance_i64(x >> 64, y >> 64) + hamming_distance_i64(x & 0xffffffff, y & 0xffffffff)


class KeyValuePairTreeNode:
    def __init__(self, key: Any, value: Any, children: Optional[Dict[Any, 'KeyValuePairTreeNode']] = None):
        self.key = key
        self.value = value
        self.children = children or dict()

    def __repr__(self):
        return '<Node %s: %s (+%d)>' % (str(self.key), str(self.value), len(self.children))

    __slots__ = ['key', 'value', 'children', '__weakref__']


# Fast hamming lookup tree structure, supports range query with tolerant value
class BKTree:
    def __init__(self):
        self.root = None

    def add_node(self, key: int, value: Any):
        """
        adding a key-value into BK-Tree
        :param key: key of current node, all keys will be compared in hamming distance, int64
        :param value: value of current node
        :return: none
        """
        if self.root is None:
            self.root = KeyValuePairTreeNode(key, [value])
        else:
            node = self.root
            while True:
                distance = hamming_distance_i64(key, node.key)
                if distance == 0:
                    node.value.append(value)
                    break
                elif distance in node.children:
                    node = node.children[distance]
                else:
                    new_node = KeyValuePairTreeNode(key, [value])
                    node.children[distance] = new_node
                    break

    def approximate_query(self, query: int, tol: int) -> List[Tuple[Any, int, int]]:
        """
        querying all values with a distance tolerance (tol) specified to the query point, returns a list of
        tuples (values, key, distance)
        :param query: query point
        :param tol: tolerance
        :return: all candidate values within the tolerance distance
        """
        if self.root is None:
            return []
        nodes = [self.root]
        ret_list = []
        while len(nodes) > 0:
            node = nodes.pop(0)
            distance = hamming_distance_i64(node.key, query)
            if distance <= tol:
                ret_list.append((node.value, int(node.key), int(distance)))
            min_range = distance - tol
            max_range = distance + tol
            for child_distance in node.children:
                if min_range <= child_distance <= max_range:
                    nodes.append(node.children[child_distance])
        return ret_list
