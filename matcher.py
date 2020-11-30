import sqlite3
import os
import numpy as np
import cv2
from util import pickle_loads
from cv_positioning import *
import image_process
import logging
# from typing import *
# import matplotlib.pyplot as plt

SQL_PATH = CV_FGO_DATABASE_FILE
logger = logging.getLogger('bgo_script.matcher')


class AbstractFgoMaterialMatcher:
    def __init__(self, sql_path: str = SQL_PATH):
        self.sql_path = sql_path
        assert os.path.isfile(self.sql_path), 'Given sql_path is not a file'
        self.sqlite_connection = sqlite3.connect(self.sql_path, check_same_thread=False)
        self.cached_icon_meta = None
        self.cached_icons = {}

    def match(self, img_arr: np.ndarray) -> int:
        raise NotImplementedError()


class SupportServantMatcher(AbstractFgoMaterialMatcher):
    __warn_size_mismatch = False

    def __init__(self, sql_path: str = SQL_PATH):
        super().__init__(sql_path)

    def match(self, img_arr: np.ndarray) -> int:
        cursor = self.sqlite_connection.cursor()
        img_arr_resized = image_process.resize(img_arr, CV_SUPPORT_SERVANT_IMG_SIZE[1], CV_SUPPORT_SERVANT_IMG_SIZE[0])
        servant_part = img_arr_resized[:CV_SUPPORT_SERVANT_SPLIT_Y, :, :3]
        hsv_servant_part = image_process.rgb_to_hsv(servant_part)
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select id from servant_icon order by id desc limit 1")
            newest_svt_id = cursor.fetchone()[0]
            cursor.execute("select count(1) from servant_icon")
            entries = cursor.fetchone()[0]
            cursor.execute("select id, image_key from servant_icon")
            self.cached_icon_meta = cursor.fetchall()
            logger.info('Finished querying support servant database, %d entries with newest servant id: %d' %
                        (entries, newest_svt_id))
        # querying image data
        min_servant_id = 0
        min_abs_err = 0
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data from image where image_key = ?", (image_key,))
                binary_data = cursor.fetchone()[0]
                # clipping alpha and opacity border
                np_image = image_process.imdecode(binary_data)[3:-3, 3:-3, :]
                if np_image.shape[:2] != CV_SUPPORT_SERVANT_IMG_SIZE:
                    if not self.__warn_size_mismatch:
                        self.__warn_size_mismatch = True
                        logger.warning('The configuration of image size for support servant matching is different from '
                                       'database size, performance will decrease: servant id: %d, key: %s' %
                                       (servant_id, image_key))
                    np_image = image_process.resize(np_image, CV_SUPPORT_SERVANT_IMG_SIZE[1],
                                                    CV_SUPPORT_SERVANT_IMG_SIZE[0])
                np_image, alpha = image_process.split_rgb_alpha(np_image)
                hsv_image = image_process.rgb_to_hsv(np_image)
                self.cached_icons[image_key] = np.concatenate([hsv_image, np.expand_dims(alpha, 2)], axis=2)
            anchor_servant_part = self.cached_icons[image_key][:CV_SUPPORT_SERVANT_SPLIT_Y, ...]
            hsv_err = image_process.mean_hsv_diff_err(anchor_servant_part, hsv_servant_part, 'hsv', 'hsv')
            if min_servant_id == 0 or hsv_err < min_abs_err:
                min_servant_id = servant_id
                min_abs_err = hsv_err
                logger.debug('svt_id = %d, key = %s, hsv_err = %f' % (servant_id, image_key, hsv_err))
        cursor.close()
        return min_servant_id


class ServantCommandCardMatcher(AbstractFgoMaterialMatcher):
    __warn_size_mismatch = False

    def __init__(self, sql_path: str = SQL_PATH):
        super().__init__(sql_path)

    def match(self, img_arr: np.ndarray) -> int:
        blur_radius = 2
        cursor = self.sqlite_connection.cursor()
        target_size = CV_COMMAND_CARD_IMG_SIZE
        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.imshow(img_arr)
        # plt.show()
        img_arr_resized = image_process.resize(img_arr, target_size[1], target_size[0])
        img_arr_resized, img_alpha = image_process.split_rgb_alpha(img_arr_resized)
        # use blur to remove high frequency noise introduced by interpolation, but blurring with alpha channel will
        # produce some weird artifacts on the edge of alpha, same ops to db images
        img_arr_resized = image_process.gauss_blur(img_arr_resized, blur_radius)
        hsv_img = np.concatenate([image_process.rgb_to_hsv(img_arr_resized), np.expand_dims(img_alpha, 2)], 2)
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select id from servant_command_card_icon order by id desc limit 1")
            newest_svt_id = cursor.fetchone()[0]
            cursor.execute("select count(1) from servant_command_card_icon")
            entries = cursor.fetchone()[0]
            cursor.execute("select id, image_key from servant_command_card_icon")
            self.cached_icon_meta = cursor.fetchall()
            logger.info('Finished querying servant command card database, %d entries with newest servant id: %d' %
                        (entries, newest_svt_id))
        # querying image data
        min_servant_id = 0
        min_err = 0
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data, name from image where image_key = ?", (image_key,))
                binary_data, name = cursor.fetchone()
                # All icon are PNG file with extra alpha channel
                np_image = image_process.imdecode(binary_data)
                # split alpha channel
                assert np_image.shape[-1] == 4, 'Servant Icon should be RGBA channel'
                if np_image.shape[:2] != target_size:
                    if not self.__warn_size_mismatch:
                        self.__warn_size_mismatch = True
                        logger.warning('The configuration of image size for command card matching is different from '
                                       'database size, performance will decrease: servant id: %d, key: %s' %
                                       (servant_id, image_key))
                    np_image = image_process.resize(np_image, target_size[1], target_size[0])
                np_image = image_process.gauss_blur(np_image, blur_radius)
                np_image, alpha = image_process.split_rgb_alpha(np_image)
                hsv_image = image_process.rgb_to_hsv(np_image)
                # weighted by alpha channel size
                self.cached_icons[image_key] = np.concatenate([hsv_image, np.expand_dims(alpha, 2)], 2)
            anchor = self.cached_icons[image_key]
            # err_map = image_process.mean_hsv_diff_err_dbg(anchor, hsv_img, 'hsv', 'hsv')
            hsv_err = image_process.mean_hsv_diff_err(anchor, hsv_img, 'hsv', 'hsv')
            if min_servant_id == 0 or hsv_err < min_err:
                min_servant_id = servant_id
                min_err = hsv_err
                logger.debug('svt_id = %d, key = %s, hsv_err = %f' % (servant_id, image_key, hsv_err))
        cursor.close()
        return min_servant_id


def deserialize_cv2_keypoint(serialized_tuple):
    # noinspection PyUnresolvedReferences
    return cv2.KeyPoint(x=serialized_tuple[0][0], y=serialized_tuple[0][1], _size=serialized_tuple[1],
                        _angle=serialized_tuple[2], _response=serialized_tuple[3], _octave=serialized_tuple[4],
                        _class_id=serialized_tuple[5])


class SupportCraftEssenceMatcher(AbstractFgoMaterialMatcher):
    # noinspection PyUnresolvedReferences
    def __init__(self, sql_path: str = SQL_PATH):
        super(SupportCraftEssenceMatcher, self).__init__(sql_path)
        if image_process.sift_class is None:
            raise RuntimeError('SIFT is disabled due to current OpenCV binaries')
        self.sift_detector = image_process.sift_class.create()
        self.matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_FLANNBASED)
        # self.matcher = cv2.BFMatcher()
        self.image_cacher = image_process.ImageHashCacher(image_process.perception_hash,
                                                          image_process.mean_gray_diff_err)

    def match(self, img_arr: np.ndarray) -> int:
        cursor = self.sqlite_connection.cursor()
        ratio_thresh = 0.7
        img_arr_resized = image_process.resize(img_arr, CV_SUPPORT_SERVANT_IMG_SIZE[1], CV_SUPPORT_SERVANT_IMG_SIZE[0])
        craft_essence_part = img_arr_resized[CV_SUPPORT_SERVANT_SPLIT_Y:-3, 2:-2, :]
        # CACHE ACCESS
        cache_key = self.image_cacher.get(craft_essence_part, None)
        if cache_key is not None:
            return cache_key
        if craft_essence_part in self.image_cacher:
            return self.image_cacher[craft_essence_part]
        if self.cached_icon_meta is None:
            cursor.execute("select id from craft_essence_icon order by id desc limit 1")
            newest_craft_essence_id = cursor.fetchone()[0]
            cursor.execute("select count(1) from craft_essence_icon")
            entries = cursor.fetchone()[0]
            cursor.execute("select id, image_key from craft_essence_icon")
            self.cached_icon_meta = cursor.fetchall()
            logger.info('Finished querying craft essence database, %d entries with newest craft essence id: %d' %
                        (entries, newest_craft_essence_id))
        _, target_descriptor = self.sift_detector.detectAndCompute(craft_essence_part, None)
        max_matches = 0
        max_craft_essence_id = 0
        for craft_essence_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select descriptors from image_sift_descriptor where image_key = ?", (image_key,))
                descriptor_blob = cursor.fetchone()[0]
                # keypoint = [deserialize_cv2_keypoint(x) for x in pickle_loads(keypoint_blob)]
                descriptors = pickle_loads(descriptor_blob)
                self.cached_icons[image_key] = descriptors  # {'key_point': keypoint, 'descriptor': descriptors}
            knn_matches = self.matcher.knnMatch(target_descriptor, self.cached_icons[image_key], 2)
            # knn_matches = self.matcher.match(target_descriptor, self.cached_icons[image_key]['descriptor'])
            good_matches = []
            for m, n in knn_matches:
                if m.distance < ratio_thresh * n.distance:
                    good_matches.append(m)
            len_good_matches = len(good_matches)
            if len_good_matches > max_matches:
                max_matches = len_good_matches
                max_craft_essence_id = craft_essence_id
                logger.debug('craft_essence_id = %d, sift_matches = %d' % (craft_essence_id, len_good_matches))
        cursor.close()
        self.image_cacher[craft_essence_part] = max_craft_essence_id
        return max_craft_essence_id
