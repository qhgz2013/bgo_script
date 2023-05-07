from .basic_impl import BasicDetectionDefImpl
from ..resolution_match_rule import Resolution, ExactWidthHeightRatioMatchRule, Rect
from ..factory import DetectionDefFactory
from util import register_handler
from typing import *


@register_handler(DetectionDefFactory, ExactWidthHeightRatioMatchRule(20 / 9))
class Exact20x9RatioDetectionDefImpl(BasicDetectionDefImpl):
    @staticmethod
    def get_target_resolution() -> Optional[Resolution]:
        # candidate resolution: 2400x1080, 3200x1440
        return Resolution(720, 1600)

    @staticmethod
    def get_ap_bar_rect() -> Rect:
        # return Rect(190, 690, 320, 695)
        raise NotImplementedError

    @staticmethod
    def get_fufu_rect() -> Rect:
        return Rect(0, 600, 1000, 675)

    @staticmethod
    def get_attack_button_rect() -> Rect:
        # return Rect(1042, 515, 1227, 700)
        raise NotImplementedError

    @staticmethod
    def get_support_scrollbar_rect() -> Rect:
        # return Rect(1245, 180, 1265, 700)
        raise NotImplementedError

    @staticmethod
    def get_support_detection_x() -> Tuple[int, int]:
        # return 300, 1000
        raise NotImplementedError

    @staticmethod
    def get_support_detection_y_len_threshold_range() -> Tuple[int, int]:
        # return 176, 181
        raise NotImplementedError

    @staticmethod
    def get_support_detection_servant_x() -> Tuple[int, int]:
        # return 48, 212
        raise NotImplementedError

    @staticmethod
    def get_support_detection_servant_img_size() -> Tuple[int, int]:
        # return 128, 128
        raise NotImplementedError

    @staticmethod
    def get_support_detection_craft_essence_img_size() -> Tuple[int, int]:
        # return 68, 150  # the original size is 68x150, but cropped to 40x150 in support selection stage
        raise NotImplementedError

    @staticmethod
    def get_support_detection_craft_essence_crop_height() -> int:
        # return 40
        raise NotImplementedError

    @staticmethod
    def get_support_detection_servant_split_y() -> int:
        # return 102
        raise NotImplementedError

    @staticmethod
    def get_support_craft_essence_max_break_rect() -> Rect:
        # return Rect(134, -24, 154, -4)
        raise NotImplementedError

    @staticmethod
    def get_support_friend_detect_rect() -> Rect:
        # return Rect(360, 130, 600, 155)
        raise NotImplementedError

    @staticmethod
    def get_support_friend_ratio_threshold() -> float:
        # return 5 / 255
        raise NotImplementedError

    @staticmethod
    def get_support_skill_box_rect() -> List[Rect]:
        # 助战技能框位置，已更新至被动技能layout
        # 35px, 10px margin
        # return [Rect(837, 135, 872, 170), Rect(882, 135, 917, 170), Rect(927, 135, 962, 170)]
        raise NotImplementedError

    @staticmethod
    def get_exit_quest_rect() -> Rect:
        # return Rect(55, 155, 1225, 545)
        raise NotImplementedError

    @staticmethod
    def get_battle_digit_rect() -> Rect:
        # return Rect(860, 10, 940, 40)
        raise NotImplementedError

    @staticmethod
    def get_support_refresh_refused_detection_rect() -> Rect:
        # return Rect(550, 540, 750, 580)
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_ui_rect() -> Rect:
        return Rect(855, 470, 1115, 570)  # for JP server

    @staticmethod
    def get_fp_pool_ui_rect_daily() -> Rect:
        # return Rect(510, 480, 770, 580)
        return Rect(670, 470, 930, 570)

    @staticmethod
    def get_fp_active_rect() -> Rect:
        return Rect(970, 30, 1110, 55)  # for JP server

    @staticmethod
    def get_fp_pool_gacha_confirm_rect() -> Rect:
        return Rect(335, 80, 1265, 635)

    @staticmethod
    def get_fp_pool_gacha_skip_check_button_rect() -> Rect:
        return Rect(915, 10, 975, 70)  # for JP server

    @staticmethod
    def get_fp_item_overflow_rect() -> Rect:
        # same as gacha_confirm_rect?
        return Rect(335, 80, 1265, 635)

    @staticmethod
    def get_craft_essence_synthesis_ui_rect() -> Rect:
        return Rect(560, 545, 660, 575)

    @staticmethod
    def get_craft_essence_material_size() -> Tuple[int, int]:
        return 128, 117

    @staticmethod
    def get_craft_essence_material_margin_y() -> int:
        return 14

    @staticmethod
    def get_craft_essence_material_ui_size_rect() -> Rect:
        return Rect(93, 599, 153, 669)

    @staticmethod
    def get_craft_essence_order_ascending_rect() -> Rect:
        return Rect(1470, 120, 1495, 140)

    @staticmethod
    def get_craft_essence_order_by_rarity_rect() -> Rect:
        return Rect(490, 290, 680, 358)

    @staticmethod
    def get_craft_essence_smart_filter_rect() -> Rect:
        return Rect(710, 440, 770, 500)

    @staticmethod
    def get_craft_essence_selective_filter_rect() -> Rect:
        return Rect(1150, 440, 1210, 500)

    @staticmethod
    def get_craft_essence_material_x_range() -> Tuple[int, int]:
        # margin: 16, width: 117
        return 241, 1156  # move --> +1px

    @staticmethod
    def get_craft_essence_material_margin_x() -> int:
        return 16

    @staticmethod
    def get_craft_essence_material_y_start() -> int:
        return 170

    @staticmethod
    def get_craft_essence_material_inner_image_rect() -> Rect:
        # 113 x 113
        return Rect(2, 4, 115, 117)

    @staticmethod
    def get_craft_essence_lock_detection_y_range() -> Tuple[int, int]:
        return 40, 70  # x: <= x1 of get_craft_essence_material_inner_image_rect

    @staticmethod
    def get_craft_essence_grid_detection_area_min_pixels() -> int:
        return 7

    @staticmethod
    def get_craft_essence_target_rect() -> Rect:
        return Rect(182, 103, 530, 700)
