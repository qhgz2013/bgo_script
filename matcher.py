import sqlite3
import os
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import pickle
from util.phash import perception_hash
from cv_positioning import CV_FGO_DATABASE_FILE
from util.image_hash_cacher import ImageHashCacher, mean_gray_diff_err
import image_process
from typing import *

SQL_PATH = CV_FGO_DATABASE_FILE


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

    # noinspection PyUnresolvedReferences
    def match(self, img_arr: np.ndarray) -> int:
        # 支援从者匹配（注意：这里忽略了匹配的礼装）
        # 从数据库中匹配给定的截图，返回对应的从者ID（目前可以很客气地说应该是可以识别某个从者的所有卡面的，包括灵衣）
        # 数据库记录目前更新至2020年1月的日服进度：最新从者：Foreigner 杨贵妃
        cursor = self.sqlite_connection.cursor()
        target_size = (150, 138)
        img_arr_resized = image_process.resize(img_arr, target_size[1], target_size[0])
        servant_part = img_arr_resized[:109, ...]
        hsv_servant_part = image_process.rgb_to_hsv(servant_part)
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select id, image_key from servant_icon")
            self.cached_icon_meta = cursor.fetchall()
        # querying image data
        min_servant_id = 0
        min_abs_err = 0
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data, name from image where image_key = ?", (image_key,))
                binary_data, name = cursor.fetchone()
                # In the newest database, the icon contains servant portrait, which is useless here.
                if 'portrait' in name.lower() or 'without frame' in name.lower():
                    continue
                pil_image = Image.open(BytesIO(binary_data))
                np_image = np.asarray(pil_image)[3:-3, 3:-3, :3]  # clipping alpha and opacity border
                if np_image.shape[:2] != target_size:
                    np_image = image_process.resize(np_image, target_size[1], target_size[0])
                hsv_image = image_process.rgb_to_hsv(np_image)
                self.cached_icons[image_key] = hsv_image
            anchor_servant_part = self.cached_icons[image_key][:109, ...]
            abs_h_err = np.abs(anchor_servant_part[..., 0].astype(np.float) - hsv_servant_part[..., 0])
            # 因为hsv色域中的色相hue是一个环，所以应该从线性修正如下
            abs_h_err = np.minimum(abs_h_err, 255 - abs_h_err)
            abs_v_err = np.abs(anchor_servant_part[..., 2].astype(np.float) - hsv_servant_part[..., 2]) / 255.0
            mean_abs_h_err = np.mean(abs_h_err * abs_v_err)
            if min_servant_id == 0 or mean_abs_h_err < min_abs_err:
                min_servant_id = servant_id
                min_abs_err = mean_abs_h_err
                # print(min_servant_id, min_abs_err)
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
    return cv2.KeyPoint(x=serialized_tuple[0][0], y=serialized_tuple[0][1], _size=serialized_tuple[1],
                        _angle=serialized_tuple[2], _response=serialized_tuple[3], _octave=serialized_tuple[4],
                        _class_id=serialized_tuple[5])


class SupportCraftEssenceMatcher(AbstractFgoMaterialMatcher):
    def __init__(self, sql_path: str = SQL_PATH):
        super(SupportCraftEssenceMatcher, self).__init__(sql_path)
        self.sift_detector = cv2.xfeatures2d_SIFT.create()
        self.flann_matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_FLANNBASED)
        self.image_cacher = ImageHashCacher(perception_hash, mean_gray_diff_err)

    # noinspection PyUnresolvedReferences
    def match(self, img_arr: np.ndarray) -> int:
        # EXPERIMENTAL
        # 数据库记录目前更新至2020年1月的日服进度
        # 注：礼装的助战缩略图和平常的小图还是有挺大偏差的，旋转裁剪缩放这种事情都能干出来，极其心不甘情不愿上SIFT算法
        # （毕竟匹配开销太大了）
        # 注意：这里使用cv2的contrib模块算法，在使用cmake编译时把contrib module记得include进去，
        # 并且勾上python3和enable_nonfree再编译release
        cursor = self.sqlite_connection.cursor()
        target_size = (144, 132)
        ratio_thresh = 0.7
        img_arr_resized = image_process.resize(img_arr, target_size[1], target_size[0])
        craft_essence_part = img_arr_resized[105:-3, ...]
        # CACHE ACCESS
        if craft_essence_part in self.image_cacher:
            return self.image_cacher[craft_essence_part]
        if self.cached_icon_meta is None:
            cursor.execute("select * from craft_essence_icon")
            self.cached_icon_meta = cursor.fetchall()
        target_keypoint, target_descriptor = self.sift_detector.detectAndCompute(craft_essence_part, None)
        max_matches = 0
        max_craft_essence_id = 0
        for craft_essence_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select key_points, descriptors from image_sift_descriptor where image_key = ?",
                               (image_key,))
                keypoint_blob, descriptor_blob = cursor.fetchone()
                keypoint = [deserialize_cv2_keypoint(x) for x in pickle.loads(keypoint_blob)]
                descriptors = pickle.loads(descriptor_blob)
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
        cursor.close()
        self.image_cacher[craft_essence_part] = max_craft_essence_id
        return max_craft_essence_id
