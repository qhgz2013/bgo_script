import numpy as np
from typing import *
import logging
from util import LazyValue
from .resize import resize
from .imread import imread
import os

logger = logging.getLogger('bgo_script.image_process')
try:
    # noinspection PyUnresolvedReferences
    import numba
    jit_no_python = numba.njit
    logger.info('Package "numba" found, using @njit to accelerate computation')
except ImportError:
    def jit_no_python(fn):
        # default decorator
        return fn
    logger.info('Package "numba" not found, it is an optional package which can improve image processing speed')


class ImageSegment:
    def __init__(self, original_image: np.ndarray, min_x: int, min_y: int, max_x: int, max_y: int,
                 associated_pixels: np.ndarray, boundary_pixels: np.ndarray):
        self.original_image = original_image
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.associated_pixels = associated_pixels
        self.boundary_pixels = boundary_pixels
        self._image_segment = LazyValue(self._get_image_segment_internal)

    __slots__ = ['_image_segment', 'min_x', 'min_y', 'max_x', 'max_y', 'original_image', 'associated_pixels',
                 'boundary_pixels']

    def get_image_segment(self) -> np.ndarray:
        return self._image_segment()

    def _get_image_segment_internal(self):
        # generated from associated pixels
        img = np.zeros([self.max_y - self.min_y, self.max_x - self.min_x], dtype=np.uint8)
        img[(self.associated_pixels[:, 0] - self.min_y, self.associated_pixels[:, 1] - self.min_x)] = 255
        return img

    def __repr__(self):
        return f'<ImageSegment x={self.min_x}-{self.max_x}, y={self.min_y}-{self.max_y}, associated pixels=' \
               f'{self.associated_pixels.shape[0]}, boundary pixels={self.boundary_pixels.shape[0]}>'


# UPDATED: newer version (supports numba jit decorator) implemented in BDCI'20 flood fill algorithm
@jit_no_python
def _dfs_visit_internal(img, visited, x, y, cls, assoc_loc, bnd_loc):
    pos_queue = [(x, y)]
    assoc_ofs = 0
    bnd_ofs = 0
    while len(pos_queue) > 0:
        x, y = pos_queue.pop()
        if (visited[y, x] & 1) != 0:
            continue
        if cls != img[y, x]:
            if (visited[y, x] & 2) == 0:
                bnd_loc[bnd_ofs] = (y, x)
                visited[y, x] |= 2
                bnd_ofs += 1
            continue
        visited[y, x] |= 1
        assoc_loc[assoc_ofs, :] = (y, x)
        assoc_ofs += 1
        # left
        if x > 0:
            pos_queue.append((x-1, y))
        # right
        if x + 1 < img.shape[1]:
            pos_queue.append((x+1, y))
        # up
        if y > 0:
            pos_queue.append((x, y-1))
        # down
        if y + 1 < img.shape[0]:
            pos_queue.append((x, y+1))
    return assoc_ofs, bnd_ofs


def _dfs_visit(img):
    visited = np.zeros_like(img, dtype=np.uint8)
    ret_list = []
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if img[y, x] != 0 and visited[y, x] == 0:
                assoc_loc = np.empty([img.shape[0]*img.shape[1], 2], dtype=np.int32)
                bnd_loc = np.empty_like(assoc_loc, dtype=np.int32)
                v_tmp = np.zeros_like(visited, dtype=np.uint8)
                cnt, bnd_cnt = _dfs_visit_internal(img, v_tmp, x, y, img[y, x], assoc_loc, bnd_loc)
                visited |= (v_tmp & 1)
                assoc_loc = assoc_loc[:cnt, :]
                bnd_loc = bnd_loc[:bnd_cnt, :]
                result = ImageSegment(img, int(np.min(assoc_loc[:, 1])), int(np.min(assoc_loc[:, 0])),
                                      int(np.max(assoc_loc[:, 1]))+1, int(np.max(assoc_loc[:, 0]))+1,
                                      assoc_loc, bnd_loc)
                ret_list.append(result)
    return ret_list


def split_image(img: np.ndarray) -> List[ImageSegment]:
    """
    Split an image into multiple connected segments using DFS

    :param img: The binarized image with shape (h, w) (equivalent class: positive (!= 0) and negative (= 0))
    :return: A list containing (y_min, x_min, y_max, x_max, available_pixels)
    """
    assert len(img.shape) == 2, 'Incompatible image shape, 2D image only'
    return _dfs_visit(img)


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


def normalize_image(img: np.ndarray, target_size: Sequence[int]) -> np.ndarray:
    """
    Normalize the image size, with extra 1 px blank padding added at each side

    :param img: Image to be normalized
    :param target_size: output image size, shape (h, w)
    :return: normalized (resized and padded) image shapes (target_size[0], target_size[1])
    """
    assert len(target_size) == 2, 'Invalid target size, should be (h, w) shape'
    resized_img = resize(img, target_size[1]-2, target_size[0]-2)
    extended_img = np.zeros(target_size, dtype=img.dtype)
    extended_img[1:-1, 1:-1] = resized_img
    return extended_img


def read_digit_label_dir(digit_dir: str):
    files = os.listdir(digit_dir)
    digit_dict = {}
    for file in files:
        file_no_ext, _ = os.path.splitext(file)
        img = imread(os.path.join(digit_dir, file))
        if len(img.shape) == 3:
            img = np.round(np.mean(img, -1)).astype(np.uint8)
        digit_dict[int(file_no_ext)] = img
    return digit_dict
