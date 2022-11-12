from .basic_impl import BasicDetectionDefImpl
from ..resolution_match_rule import Resolution, ExactWidthHeightRatioMatchRule, Rect
from ..factory import DetectionDefFactory
from util import register_handler
from typing import *


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
        return 144, 132  # todo: use new image size

    @staticmethod
    def get_support_detection_servant_split_y() -> int:
        return 107

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
    def get_fp_pool_ui_rect() -> Rect:
        return Rect(700, 480, 950, 620)

    @staticmethod
    def get_fp_active_rect() -> Rect:
        return Rect(700, 30, 840, 55)

    @staticmethod
    def get_fp_pool_gacha_confirm_rect() -> Rect:
        return Rect(175, 80, 1105, 635)

    @staticmethod
    def get_fp_pool_gacha_skip_check_button_rect() -> Rect:
        return Rect(640, 10, 700, 70)
