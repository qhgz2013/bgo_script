from .basic_impl import BasicDetectionDefImpl
from ..resolution_match_rule import Resolution, ExactWidthHeightRatioMatchRule, Rect
from ..factory import DetectionDefFactory
from util import register_handler
from typing import *

__all__ = ['Exact16x9RatioDetectionDefImpl']


@register_handler(DetectionDefFactory, ExactWidthHeightRatioMatchRule(16 / 9))
class Exact16x9RatioDetectionDefImpl(BasicDetectionDefImpl):
    @staticmethod
    def get_target_resolution() -> Optional[Resolution]:
        return Resolution(720, 1280)

    @staticmethod
    def get_ap_bar_rect() -> Rect:
        return Rect(190, 690, 320, 695)

    @staticmethod
    def get_fufu_rect() -> Rect:
        return Rect(0, 625, 900, 700)

    @staticmethod
    def get_attack_button_rect() -> Rect:
        return Rect(1042, 515, 1227, 700)

    @staticmethod
    def get_support_scrollbar_rect() -> Rect:
        return Rect(1245, 180, 1265, 700)

    @staticmethod
    def get_support_detection_x() -> Tuple[int, int]:
        return 300, 1000

    @staticmethod
    def get_support_detection_y_len_threshold_range() -> Tuple[int, int]:
        return 176, 181

    @staticmethod
    def get_support_detection_servant_x() -> Tuple[int, int]:
        return 48, 212

    @staticmethod
    def get_support_detection_servant_img_size() -> Tuple[int, int]:
        return 128, 128

    @staticmethod
    def get_support_detection_craft_essence_img_size() -> Tuple[int, int]:
        return 68, 150  # the original size is 68x150, but cropped to 40x150 in support selection stage

    @staticmethod
    def get_support_detection_craft_essence_crop_height() -> int:
        return 40

    @staticmethod
    def get_support_detection_servant_split_y() -> int:
        return 102

    @staticmethod
    def get_support_craft_essence_max_break_rect() -> Rect:
        return Rect(134, -24, 154, -4)

    @staticmethod
    def get_support_friend_detect_rect() -> Rect:
        return Rect(360, 130, 600, 155)

    @staticmethod
    def get_support_friend_ratio_threshold() -> float:
        return 5 / 255

    @staticmethod
    def get_support_skill_box_rect() -> List[Rect]:
        # 助战技能框位置，已更新至被动技能layout
        # 35px, 10px margin
        return [Rect(837, 135, 872, 170), Rect(882, 135, 917, 170), Rect(927, 135, 962, 170)]

    @staticmethod
    def get_exit_quest_rect() -> Rect:
        return Rect(55, 155, 1225, 545)

    @staticmethod
    def get_battle_digit_rect() -> Rect:
        return Rect(860, 10, 940, 40)

    @staticmethod
    def get_support_refresh_refused_detection_rect() -> Rect:
        return Rect(550, 540, 750, 580)

    @staticmethod
    def get_eat_apple_ui_rect() -> Rect:
        return Rect(150, 40, 1130, 650)

    @staticmethod
    def get_continuous_battle_ui_rect() -> Rect:
        return Rect(190, 90, 1090, 630)

    @staticmethod
    def get_fp_pool_ui_rect() -> Rect:
        return Rect(695, 480, 955, 580)

    @staticmethod
    def get_fp_pool_ui_rect_daily() -> Rect:
        return Rect(510, 480, 770, 580)

    @staticmethod
    def get_fp_active_rect() -> Rect:
        return Rect(820, 30, 960, 55)

    @staticmethod
    def get_fp_pool_gacha_confirm_rect() -> Rect:
        return Rect(175, 80, 1105, 635)

    @staticmethod
    def get_fp_pool_gacha_skip_check_button_rect() -> Rect:
        return Rect(754, 10, 814, 70)

    @staticmethod
    def get_fp_item_overflow_rect() -> Rect:
        # same as gacha_confirm_rect?
        return Rect(175, 80, 1105, 635)

    @staticmethod
    def get_craft_essence_synthesis_ui_rect() -> Rect:
        return Rect(400, 565, 500, 595)

    @staticmethod
    def get_craft_essence_material_size() -> Tuple[int, int]:
        return 128, 117

    @staticmethod
    def get_craft_essence_material_margin_y() -> int:
        return 14

    @staticmethod
    def get_craft_essence_material_ui_size_rect() -> Rect:
        return Rect(0, 640, 60, 710)

    @staticmethod
    def get_craft_essence_order_ascending_rect() -> Rect:
        return Rect(1235, 120, 1260, 140)

    @staticmethod
    def get_craft_essence_order_by_rarity_rect() -> Rect:
        return Rect(330, 290, 520, 358)

    @staticmethod
    def get_craft_essence_smart_filter_rect() -> Rect:
        return Rect(550, 440, 610, 500)

    @staticmethod
    def get_craft_essence_selective_filter_rect() -> Rect:
        return Rect(990, 440, 1050, 500)

    @staticmethod
    def get_craft_essence_material_x_range() -> Tuple[int, int]:
        # margin: 16, width: 117
        return 74, 989  # 75, 990 <- offset 1 px left

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
        return Rect(22, 103, 370, 700)
