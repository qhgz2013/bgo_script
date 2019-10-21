import sqlite3
from typing import *
import os
import numpy as np
import cv2
from PIL import Image
from io import BytesIO

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
        img_arr_resized = cv2.resize(img_arr, (target_size[1], target_size[0]))
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


class CraftEssenceMatcher(AbstractFgoMaterialMatcher):
    def __init__(self, sql_path: str = SQL_PATH):
        super(CraftEssenceMatcher, self).__init__(sql_path)

    # noinspection PyUnresolvedReferences
    def match_support(self, img_arr: np.ndarray) -> int:
        # EXPERIMENTAL
        # 注：礼装的助战缩略图和平常的小图还是有一点偏差的，即会平移一段距离，用一般拍脑袋想象的检测方法可能不合适
        # TODO: 改成SURF进行特征点提取 + 特征点匹配
        # 没用过cv2的SURF和SIFT算法，这里先鸽一下吧，后面补充
        # 注意：这里涉及使用cv2的contrib模块算法，在使用cmake编译时记得include进去，并且勾上python3再编译release
        cursor = self.sqlite_connection.cursor()
        target_size = (144, 132)
        img_arr_resized = cv2.resize(img_arr, (target_size[1], target_size[0]))
        craft_essence_part = img_arr_resized[105:-3, ...]
        h1 = craft_essence_part.shape[0]
        h_slide = target_size[0] - h1
        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.imshow(craft_essence_part)
        # plt.show()
        hsv_craft_essence_part = cv2.cvtColor(craft_essence_part, cv2.COLOR_RGB2HSV)
        if self.cached_icon_meta is None:
            cursor.execute("select * from craft_essence_icon")
            self.cached_icon_meta = cursor.fetchall()
        min_abs_err = 0
        min_craft_essence_id = 0
        min_slide_offset = 0
        min_img_key = None
        for craft_essence_id, image_key in self.cached_icon_meta:
            if image_key not in self.cached_icons:
                cursor.execute("select image_data from image where image_key = ?", (image_key,))
                binary_data = cursor.fetchone()[0]
                pil_image = Image.open(BytesIO(binary_data))
                np_image = np.asarray(pil_image)[3:-15, ...]  # 除去边框
                if np_image.shape[:2] != target_size:
                    np_image = cv2.resize(np_image, (target_size[1], target_size[0]), interpolation=cv2.INTER_CUBIC)
                # if craft_essence_id == 188:
                #     plt.figure()
                #     plt.imshow(np_image[28:28+36, ...])
                #     plt.show()
                hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
                self.cached_icons[image_key] = {'image': hsv_image, 'aligned_y': -1}
            img_data = self.cached_icons[image_key]
            anchor_hsv = img_data['image']
            if img_data['aligned_y'] == -1:
                slide_mean_abs_diff = np.empty((h_slide,))
                for slide_offset in range(h_slide):
                    h_err = np.abs(hsv_craft_essence_part[..., 0] - anchor_hsv[slide_offset:slide_offset + h1, :, 0])
                    h_err = np.minimum(h_err, 255 - h_err)
                    v_err = np.abs(hsv_craft_essence_part[..., 1] - anchor_hsv[slide_offset:slide_offset + h1, :, 1])
                    slide_mean_abs_diff[slide_offset] = np.mean(h_err) + np.mean(v_err)
                slide_offset = np.argmin(slide_mean_abs_diff)
                mean_abs_diff = slide_mean_abs_diff[slide_offset]
            else:
                slide_offset = img_data['aligned_y']
                h_err = np.abs(hsv_craft_essence_part[..., 0] - anchor_hsv[slide_offset:slide_offset + h1, :, 0])
                h_err = np.minimum(h_err, 255 - h_err)
                h_err[24:, 30:110] = 0
                v_err = np.abs(hsv_craft_essence_part[..., 1] - anchor_hsv[slide_offset:slide_offset + h1, :, 1])
                mean_abs_diff = np.mean(h_err) + np.mean(v_err)
            # if craft_essence_id == 188:
            #     plt.figure()
            #     t = hsv_craft_essence_part[..., 0] - anchor_hsv[slide_offset:slide_offset+h1, :, 0]
            #     t = np.minimum(t, 255 - t)
            #     plt.imshow(t)
            #     plt.show()
            if min_craft_essence_id == 0 or mean_abs_diff < min_abs_err:
                min_abs_err = mean_abs_diff
                min_slide_offset = slide_offset
                min_img_key = image_key
                min_craft_essence_id = craft_essence_id
                print(min_craft_essence_id, min_abs_err, min_slide_offset)
        # if self.cached_icons[min_img_key]['aligned_y'] == -1:
        #     self.cached_icons[min_img_key]['aligned_y'] = min_slide_offset
        cursor.close()
        return min_craft_essence_id
