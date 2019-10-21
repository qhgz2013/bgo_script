import sqlite3
from typing import *
import os
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import pickle
from phash import perception_hash


SQL_PATH = 'cv_data/fgo.db'


class AbstractFgoMaterialMatcher:
    def __init__(self, sql_path: str = SQL_PATH):
        self.sql_path = sql_path
        assert os.path.isfile(self.sql_path), 'Given sql_path is not a file'
        self.sqlite_connection = sqlite3.connect(self.sql_path)
        self.cached_icon_meta = None
        self.cached_icons = {}

    def match_support(self, img_arr: np.ndarray) -> int:
        raise NotImplementedError()


class ServantMatcher(AbstractFgoMaterialMatcher):
    def __init__(self, sql_path: str = SQL_PATH):
        super(ServantMatcher, self).__init__(sql_path)

    # noinspection PyUnresolvedReferences
    def match_support(self, img_arr: np.ndarray) -> int:
        # 支援从者匹配（注意：这里忽略了匹配的礼装）
        # 从数据库中匹配给定的截图，返回对应的从者ID（目前可以很客气地说应该是可以识别某个从者的所有卡面的，包括灵衣）
        # 数据库记录目前更新至2019年2月的日服进度
        cursor = self.sqlite_connection.cursor()
        target_size = (150, 138)
        img_arr_resized = cv2.resize(img_arr, (target_size[1], target_size[0]), interpolation=cv2.INTER_CUBIC)
        servant_part = img_arr_resized[:109, ...]
        hsv_servant_part = cv2.cvtColor(servant_part, cv2.COLOR_RGB2HSV)
        # querying servant icon database
        if self.cached_icon_meta is None:
            cursor.execute("select id, image_key from servant_icon")
            self.cached_icon_meta = cursor.fetchall()
        # querying image data
        min_servant_id = 0
        min_abs_err = 0
        for servant_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data from image where image_key = ?", (image_key,))
                binary_data = cursor.fetchone()[0]
                pil_image = Image.open(BytesIO(binary_data))
                np_image = np.asarray(pil_image)[3:-3, 3:-3, :3]  # clipping alpha and opacity border
                if np_image.shape[:2] != target_size:
                    np_image = cv2.resize(np_image, (target_size[1], target_size[0]), interpolation=cv2.INTER_CUBIC)
                hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
                self.cached_icons[image_key] = hsv_image
            anchor_servant_part = self.cached_icons[image_key][:109, ...]
            abs_h_err = np.abs(anchor_servant_part[..., 0] - hsv_servant_part[..., 0])
            # 因为hsv色域中的色相hue是一个环，所以应该从线性修正如下
            abs_h_err = np.minimum(abs_h_err, 255 - abs_h_err)
            mean_abs_h_err = np.mean(abs_h_err)
            if min_servant_id == 0 or mean_abs_h_err < min_abs_err:
                min_servant_id = servant_id
                min_abs_err = mean_abs_h_err
                # print(min_servant_id, min_abs_err)
        cursor.close()
        return min_servant_id

    def get_servant_name(self, servant_id: int) -> str:
        cursor = self.sqlite_connection.cursor()
        cursor.execute("select name_cn from servant_base where id = ?", (servant_id,))
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return ''
        return result[0]


def deserialize_cv2_keypoint(serialized_tuple):
    return cv2.KeyPoint(x=serialized_tuple[0][0], y=serialized_tuple[0][1], _size=serialized_tuple[1],
                        _angle=serialized_tuple[2], _response=serialized_tuple[3], _octave=serialized_tuple[4],
                        _class_id=serialized_tuple[5])


class CraftEssenceMatcher(AbstractFgoMaterialMatcher):
    def __init__(self, sql_path: str = SQL_PATH):
        super(CraftEssenceMatcher, self).__init__(sql_path)
        self.sift_detector = cv2.xfeatures2d_SIFT.create()
        self.flann_matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_FLANNBASED)
        self.phash = {}

    # noinspection PyUnresolvedReferences
    def match_support(self, img_arr: np.ndarray) -> int:
        # EXPERIMENTAL
        # 数据库记录目前更新至2019年10月的日服进度
        # 注：礼装的助战缩略图和平常的小图还是有挺大偏差的，旋转裁剪缩放这种事情都能干出来，极其心不甘情不愿上SIFT算法
        # （毕竟匹配开销太大了）
        # 注意：这里使用cv2的contrib模块算法，在使用cmake编译时把contrib module记得include进去，
        # 并且勾上python3和enable_nonfree再编译release
        # todo: 添加一层基于Perception Hash的cache，避免重复计算
        cursor = self.sqlite_connection.cursor()
        target_size = (144, 132)
        ratio_thresh = 0.7
        img_arr_resized = cv2.resize(img_arr, (target_size[1], target_size[0]), interpolation=cv2.INTER_CUBIC)
        craft_essence_part = img_arr_resized[105:-3, ...]
        # CACHE ACCESS
        phash = perception_hash(craft_essence_part, 8)
        # if phash in self.phash:
        #     return self.phash[phash]
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
        if phash in self.phash:
            print('cached id:', self.phash[phash], 'current id:', max_craft_essence_id)
        self.phash[phash] = max_craft_essence_id
        return max_craft_essence_id
