import numpy as np
from typing import *


# DFS segmentation, original implemented in file fgo_detection.ipynb
def _dfs_image(img_binary: np.ndarray, x: int, y: int, visited: np.ndarray, rect: List[int], group_idx: int = 1):
    assert group_idx != 0
    if img_binary[y, x] < 128 or visited[y, x] != 0:
        return False
    # rect: in (y1, x1, y2, x2) formatted
    if y < rect[0]:
        rect[0] = y
    if y+1 > rect[2]:
        rect[2] = y+1
    if x < rect[1]:
        rect[1] = x
    if x+1 > rect[3]:
        rect[3] = x+1

    visited[y, x] = group_idx
    rect[4] = rect[4] + 1

    if y > 0 and visited[y-1, x] == 0:
        # up
        _dfs_image(img_binary, x, y-1, visited, rect, group_idx)
    if y < img_binary.shape[0] - 1 and visited[y+1, x] == 0:
        # down
        _dfs_image(img_binary, x, y+1, visited, rect, group_idx)
    if x > 0 and visited[y, x-1] == 0:
        # left
        _dfs_image(img_binary, x-1, y, visited, rect, group_idx)
    if x < img_binary.shape[1] - 1 and visited[y, x+1] == 0:
        # right
        _dfs_image(img_binary, x+1, y, visited, rect, group_idx)


def split_image(img: np.ndarray, threshold: Any = 127) -> List[List[int]]:
    """
    Split an image into multiple connected segments using DFS
    :param img: The image with shape (h, w)
    :param threshold: The threshold value for bianry indication function I(pixel value > threshold)
    :return: A list containing (y_min, x_min, y_max, x_max, available_pixels)
    """
    assert img.dtype == np.uint8, 'Invalid image dtype, expected uint8'
    assert len(img.shape) == 2, 'Incompatible image shape, 2D image only'
    cnt = 1
    rects = []
    v = np.zeros_like(img, dtype='uint8')
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if img[y, x] > threshold and v[y, x] == 0:
                rect = [y, x, y + 1, x + 1, 1]
                _dfs_image(img, x, y, v, rect, cnt)
                rects.append(rect)
                cnt += 1
    return rects


def extend_alpha_1px(alpha: np.ndarray) -> np.ndarray:
    """
    Extend the edge of alpha mask by 1 pixel
    :param alpha: original alpha mask, shape (h, w) with uint8 type
    :return: extended alpha mask
    """
    if len(alpha.shape) == 3 and alpha.shape[-1] == 1:
        alpha = np.squeeze(alpha, -1)
    elif len(alpha.shape) != 2:
        raise ValueError('Invalid alpha shape')
    v = np.zeros_like(alpha, dtype='uint8')
    for y in range(alpha.shape[0]):
        for x in range(alpha.shape[1]):
            if alpha[y, x] > 127:
                # broadcast
                if y > 0:
                    v[y-1, x] |= 1
                if y < alpha.shape[0] - 1:
                    v[y+1, x] |= 2
                if x > 0:
                    v[y, x-1] |= 4
                if x < alpha.shape[1] - 1:
                    v[y, x+1] |= 8
    alpha_new = np.empty_like(alpha, dtype=np.float)
    for y in range(alpha.shape[0]):
        for x in range(alpha.shape[1]):
            c = 0
            t = 0
            if v[y, x] & 1:
                c += 1
                t += alpha[y+1, x]
            if v[y, x] & 2:
                c += 1
                t += alpha[y-1, x]
            if v[y, x] & 4:
                c += 1
                t += alpha[y, x+1]
            if v[y, x] & 8:
                c += 1
                t += alpha[y, x-1]
            if c > 0:
                alpha_new[y, x] = t / c
            else:
                alpha_new[y, x] = 0
    return np.round(np.maximum(alpha_new, alpha)).astype('uint8')
