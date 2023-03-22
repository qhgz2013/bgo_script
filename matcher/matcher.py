import sqlite3
import os
import numpy as np
from util import pickle_loads, pickle_load, pickle_dump, RWLock
import image_process
import logging
from typing import *
import threading
from time import time, sleep
from bgo_game import ScriptEnv
import matplotlib.pyplot as plt

logger = logging.getLogger('bgo_script.matcher')


class AbstractFgoMaterialMatcher:
    def __init__(self, sql_path: str, env: ScriptEnv):
        self.sql_path = sql_path
        self.env = env
        assert os.path.isfile(self.sql_path), 'Given sql_path is not a file'
        self.sqlite_connection = sqlite3.connect(self.sql_path, check_same_thread=False)
        self.cached_icon_meta = None
        self.cached_icons = {}

    def match(self, img_arr: np.ndarray) -> int:
        raise NotImplementedError()


class SupportServantMatcher(AbstractFgoMaterialMatcher):
    __warn_size_mismatch = False

    def match(self, img_arr: np.ndarray) -> int:
        img_arr = img_arr[5:163, 3:-3, :]  # TODO: remove this hardcoded crop area
        cursor = self.sqlite_connection.cursor()
        h, w = self.env.detection_definitions.get_support_detection_servant_img_size()
        img_arr_resized = image_process.resize(img_arr, w, h)
        split_y = self.env.detection_definitions.get_support_detection_servant_split_y()
        servant_part = img_arr_resized[:split_y, :, :3]

        # plt.figure()
        # plt.imshow(servant_part)
        # plt.show()

        hsv_servant_part = image_process.rgb_to_hsv(servant_part)
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select servant_id, image_key from servant_faces")
            self.cached_icon_meta = cursor.fetchall()
            logger.info(f'Finished querying support servant database, {len(self.cached_icon_meta)} entries with newest '
                        f'servant id: {max(map(lambda x: x[0], self.cached_icon_meta))}')
        # querying image data
        min_servant_id = 0
        min_abs_err = 0
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data from image where image_key = ?", (image_key,))
                binary_data = cursor.fetchone()[0]
                # clipping alpha and opacity border
                np_image = image_process.imdecode(binary_data)
                if np_image.shape[:2] != (h, w):
                    if not self.__warn_size_mismatch:
                        self.__warn_size_mismatch = True
                        logger.warning('The configuration of image size for support servant matching is different from '
                                       'database size, performance will decrease: servant id: %d, key: %s' %
                                       (servant_id, image_key))
                    np_image = image_process.resize(np_image, w, h)
                np_image, alpha = image_process.split_rgb_alpha(np_image)
                hsv_image = image_process.rgb_to_hsv(np_image)
                self.cached_icons[image_key] = np.concatenate([hsv_image, np.expand_dims(alpha, 2)], axis=2)
            anchor_servant_part = self.cached_icons[image_key][:split_y, ...]
            hsv_err = image_process.mean_hsv_diff_err(anchor_servant_part, hsv_servant_part, 'hsv', 'hsv')
            if min_servant_id == 0 or hsv_err < min_abs_err:
                min_servant_id = servant_id
                min_abs_err = hsv_err
                logger.debug('svt_id = %d, key = %s, hsv_err = %f' % (servant_id, image_key, hsv_err))
        cursor.close()
        return min_servant_id


class ServantCommandCardMatcher(AbstractFgoMaterialMatcher):
    __warn_size_mismatch = False

    def match(self, img_arr: np.ndarray, candidate_servant_list: Optional[List[int]] = None) -> int:
        raise NotImplementedError
        # blur_radius = 2
        # cursor = self.sqlite_connection.cursor()
        # target_size = CV_COMMAND_CARD_IMG_SIZE
        # # import matplotlib.pyplot as plt
        # # plt.figure()
        # # plt.imshow(img_arr)
        # # plt.show()
        # img_arr_resized = image_process.resize(img_arr, target_size[1], target_size[0])
        # img_arr_resized, img_alpha = image_process.split_rgb_alpha(img_arr_resized)
        # # use blur to remove high frequency noise introduced by interpolation, but blurring with alpha channel will
        # # produce some weird artifacts on the edge of alpha, same ops to db images
        # img_arr_resized = image_process.gauss_blur(img_arr_resized, blur_radius)
        # hsv_img = np.concatenate([image_process.rgb_to_hsv(img_arr_resized), np.expand_dims(img_alpha, 2)], 2)
        # # querying servant icon database
        # if self.cached_icon_meta is None:
        #     cursor.execute("select id from servant_command_card_icon order by id desc limit 1")
        #     newest_svt_id = cursor.fetchone()[0]
        #     cursor.execute("select count(1) from servant_command_card_icon")
        #     entries = cursor.fetchone()[0]
        #     cursor.execute("select id, image_key from servant_command_card_icon")
        #     result = cursor.fetchall()
        #     svt_id_img_key_list = dict()  # type: Dict[int, List[str]]
        #     for id_, image_key in result:
        #         if id_ not in svt_id_img_key_list:
        #             svt_id_img_key_list[id_] = []
        #         svt_id_img_key_list[id_].append(image_key)
        #     self.cached_icon_meta = svt_id_img_key_list
        #     logger.info('Finished querying servant command card database, %d entries with newest servant id: %d' %
        #                 (entries, newest_svt_id))
        # # querying image data
        # query_target = set(candidate_servant_list) or self.cached_icon_meta.keys()
        # min_servant_id = 0
        # min_err = 0
        # for servant_id in query_target:
        #     image_keys = self.cached_icon_meta[servant_id]
        #     for image_key in image_keys:
        #         if image_key not in self.cached_icons:
        #             cursor.execute("select image_data, name from image where image_key = ?", (image_key,))
        #             binary_data, name = cursor.fetchone()
        #             # All icon are PNG file with extra alpha channel
        #             np_image = image_process.imdecode(binary_data)
        #             # split alpha channel
        #             assert np_image.shape[-1] == 4, 'Servant Icon should be RGBA channel'
        #             if np_image.shape[:2] != target_size:
        #                 if not self.__warn_size_mismatch:
        #                     self.__warn_size_mismatch = True
        #                     logger.warning('The configuration of image size for command card matching is different from'
        #                                    ' database size, performance will decrease: servant id: %d, key: %s' %
        #                                    (servant_id, image_key))
        #                 np_image = image_process.resize(np_image, target_size[1], target_size[0])
        #             np_image = image_process.gauss_blur(np_image, blur_radius)
        #             np_image, alpha = image_process.split_rgb_alpha(np_image)
        #             hsv_image = image_process.rgb_to_hsv(np_image)
        #             # weighted by alpha channel size
        #             self.cached_icons[image_key] = np.concatenate([hsv_image, np.expand_dims(alpha, 2)], 2)
        #         anchor = self.cached_icons[image_key]
        #         # err_map = image_process.mean_hsv_diff_err_dbg(anchor, hsv_img, 'hsv', 'hsv')
        #         hsv_err = image_process.mean_hsv_diff_err(anchor, hsv_img, 'hsv', 'hsv')
        #         if min_servant_id == 0 or hsv_err < min_err:
        #             min_servant_id = servant_id
        #             min_err = hsv_err
        #             logger.debug('svt_id = %d, key = %s, hsv_err = %f' % (servant_id, image_key, hsv_err))
        # cursor.close()
        # return min_servant_id


def deserialize_cv2_keypoint(serialized_tuple):
    # noinspection PyUnresolvedReferences
    return cv2.KeyPoint(x=serialized_tuple[0][0], y=serialized_tuple[0][1], _size=serialized_tuple[1],
                        _angle=serialized_tuple[2], _response=serialized_tuple[3], _octave=serialized_tuple[4],
                        _class_id=serialized_tuple[5])


# todo [PRIOR: high]: Multi-process support
class SupportCraftEssenceMatcher(AbstractFgoMaterialMatcher):
    __warn_size_mismatch = False

    def __init__(self, sql_path: str, env: ScriptEnv):
        super(SupportCraftEssenceMatcher, self).__init__(sql_path, env)
        self.image_cacher = image_process.ImageHashCacher(image_process.perception_hash,
                                                          image_process.mean_gray_diff_err)

    def match(self, img_arr: np.ndarray) -> int:
        img_arr = img_arr[5:-2, 3:-3, :]
        cursor = self.sqlite_connection.cursor()
        svt_h, svt_w = self.env.detection_definitions.get_support_detection_servant_img_size()  # 128x128
        img_arr_resized = image_process.resize(img_arr, svt_w, svt_h)
        h, w = self.env.detection_definitions.get_support_detection_craft_essence_img_size()  # 68x150
        crop_height = self.env.detection_definitions.get_support_detection_craft_essence_crop_height()  # 40
        split_h = int(round(crop_height * (svt_w / w)))
        split_y = svt_h - split_h
        craft_essence_part = image_process.resize(img_arr_resized[split_y:, ...], w, crop_height)

        # plt.figure()
        # plt.imshow(craft_essence_part)
        # plt.show()

        # CACHE ACCESS
        cache_key = self.image_cacher.get(craft_essence_part, None)
        if cache_key is not None:
            return cache_key
        if self.cached_icon_meta is None:
            cursor.execute("select ce_id, image_key from craft_essence_equip_face")
            self.cached_icon_meta = cursor.fetchall()
            logger.info(f'Finished querying craft essence database, {len(self.cached_icon_meta)} entries with newest '
                        f'craft essence id: {max(map(lambda x: x[0], self.cached_icon_meta))}')

        # querying image data
        min_ce_id = 0
        min_abs_err = 0
        for ce_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data from image where image_key = ?", (image_key,))
                binary_data = cursor.fetchone()[0]
                # clipping alpha and opacity border
                np_image = image_process.imdecode(binary_data)  # 68x150
                if np_image.shape[:2] != (h, w):
                    if not self.__warn_size_mismatch:
                        self.__warn_size_mismatch = True
                        logger.warning('The configuration of image size for support CE matching is different from '
                                       'database size, performance will decrease: ce id: %d, key: %s' %
                                       (ce_id, image_key))
                if crop_height != h:
                    # craft essence equip face in support selection stage is cropped
                    padding = int(round((h - crop_height) / 2))
                    np_image = np_image[padding:padding+crop_height, ...]
                self.cached_icons[image_key] = np_image
            err = image_process.mean_gray_diff_err(craft_essence_part, self.cached_icons[image_key])
            if min_ce_id == 0 or err < min_abs_err:
                min_ce_id = ce_id
                min_abs_err = err
                logger.debug('ce_id = %d, key = %s, err = %f' % (ce_id, image_key, err))
        cursor.close()
        return min_ce_id
