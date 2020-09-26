import sqlite3
import os
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from util import pickle_loads
from cv_positioning import *
import image_process
import logging
# from typing import *
import matplotlib.pyplot as plt

SQL_PATH = CV_FGO_DATABASE_FILE
logger = logging.getLogger('bgo_script.matcher')


# TODO: 重构该部分代码
class AbstractFgoMaterialMatcher:
    def __init__(self, sql_path: str = SQL_PATH):
        self.sql_path = sql_path
        assert os.path.isfile(self.sql_path), 'Given sql_path is not a file'
        self.sqlite_connection = sqlite3.connect(self.sql_path)
        self.cached_icon_meta = None
        self.cached_icons = {}

    def match(self, img_arr: np.ndarray) -> int:
        raise NotImplementedError()


class SupportServantMatcher(AbstractFgoMaterialMatcher):
    def __init__(self, sql_path: str = SQL_PATH):
        super(SupportServantMatcher, self).__init__(sql_path)

    def match(self, img_arr: np.ndarray) -> int:
        cursor = self.sqlite_connection.cursor()
        img_arr_resized = image_process.resize(img_arr, CV_SUPPORT_SERVANT_IMG_SIZE[1], CV_SUPPORT_SERVANT_IMG_SIZE[0])
        servant_part = img_arr_resized[:CV_SUPPORT_SERVANT_SPLIT_Y, ...]
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
                cursor.execute("select image_data, name from image where image_key = ?", (image_key,))
                binary_data, name = cursor.fetchone()
                # In the newest database, the icon contains servant portrait, which is useless here.
                # if 'portrait' in name.lower() or 'without frame' in name.lower():
                #     continue
                pil_image = Image.open(BytesIO(binary_data))
                # clipping alpha and opacity border
                np_image, alpha = image_process.split_rgb_alpha(np.asarray(pil_image)[3:-3, 3:-3, :])
                if np_image.shape[:2] != CV_SUPPORT_SERVANT_IMG_SIZE:
                    np_image = image_process.resize(np_image, CV_SUPPORT_SERVANT_IMG_SIZE[1],
                                                    CV_SUPPORT_SERVANT_IMG_SIZE[0])
                    alpha = image_process.resize(alpha, CV_SUPPORT_SERVANT_IMG_SIZE[1], CV_SUPPORT_SERVANT_IMG_SIZE[0])
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
    def __init__(self, sql_path: str = SQL_PATH):
        super(ServantCommandCardMatcher, self).__init__(sql_path)

    def _match_gray_diff(self, img_arr: np.ndarray) -> int:  # Tuple[int, int]:
        # import matplotlib.pyplot as plt
        cursor = self.sqlite_connection.cursor()
        target_size = (160, 160)
        img_arr_resized = image_process.resize(img_arr, target_size[1], target_size[0])
        servant_part = img_arr_resized[:int(0.6*target_size[0]), ...]
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select id, image_key from servant_command_card_icon")
            self.cached_icon_meta = cursor.fetchall()
        # querying image data
        min_servant_id = 0
        min_abs_err = 0
        # card_color = -1
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data, name from image where image_key = ?", (image_key,))
                binary_data, name = cursor.fetchone()
                # All icon are PNG file with extra alpha channel
                pil_image = Image.open(BytesIO(binary_data))
                np_image = np.asarray(pil_image)
                # split alpha channel
                assert np_image.shape[-1] == 4, 'Servant Icon should be RGBA channel'
                alpha = np_image[..., -1:]
                np_image = np_image[..., :3]
                if np_image.shape[:2] != target_size:
                    np_image = image_process.resize(np_image, target_size[1], target_size[0])
                self.cached_icons[image_key] = np_image, alpha
            anchor_servant_part = self.cached_icons[image_key][0][:int(0.6*target_size[0]), ...]
            abs_err = np.abs(anchor_servant_part.astype(np.float) - servant_part)
            abs_err = abs_err * (self.cached_icons[image_key][1][:int(0.6*target_size[0]), ...] / 255)
            mean_abs_err = np.mean(abs_err)
            if min_servant_id == 0 or mean_abs_err < min_abs_err:
                min_servant_id = servant_id
                min_abs_err = mean_abs_err
                # computing card color, reverse alpha channel to choose background
                # card_bg = (1.0 - self.cached_icons[image_key][1] / 255) * img_arr_resized
                # card_bg = card_bg[15:150, 27:133, :].astype('uint8')
                # card_color = np.argmax(np.mean(card_bg, (0, 1)))
            # if servant_id == 29:
            #     plt.figure()
            #     plt.imshow(servant_part)
            #     plt.show()
            #     plt.figure()
            #     plt.imshow(anchor_servant_part)
            #     plt.show()
            #     plt.figure()
            #     plt.imshow(abs_err.astype('uint8'))
            #     plt.show()
        cursor.close()
        return min_servant_id  # , card_color

    def match(self, img_arr: np.ndarray) -> int:
        return self._match_gray_diff(img_arr)


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
        self.flann_matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_FLANNBASED)
        self.image_cacher = image_process.ImageHashCacher(image_process.perception_hash,
                                                          image_process.mean_gray_diff_err)

    def match(self, img_arr: np.ndarray) -> int:
        cursor = self.sqlite_connection.cursor()
        ratio_thresh = 0.7
        img_arr_resized = image_process.resize(img_arr, CV_SUPPORT_SERVANT_IMG_SIZE[1], CV_SUPPORT_SERVANT_IMG_SIZE[0])
        craft_essence_part = img_arr_resized[CV_SUPPORT_SERVANT_SPLIT_Y:-3, ...]
        # CACHE ACCESS
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
        target_keypoint, target_descriptor = self.sift_detector.detectAndCompute(craft_essence_part, None)
        max_matches = 0
        max_craft_essence_id = 0
        for craft_essence_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select key_points, descriptors from image_sift_descriptor where image_key = ?",
                               (image_key,))
                keypoint_blob, descriptor_blob = cursor.fetchone()
                keypoint = [deserialize_cv2_keypoint(x) for x in pickle_loads(keypoint_blob)]
                descriptors = pickle_loads(descriptor_blob)
                self.cached_icons[image_key] = {'key_point': keypoint, 'descriptor': descriptors}
            knn_matches = self.flann_matcher.knnMatch(target_descriptor, self.cached_icons[image_key]['descriptor'], 2)
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
