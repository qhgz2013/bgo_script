from abc import ABCMeta
from .resolution_match_rule import Resolution, Rect
from .plot_util import plot_rect
from typing import *

__all__ = ['AbstractDetectionDef']


try:
    final
except NameError:
    # python 3.6
    def final(f):
        return f


class AbstractDetectionDef(metaclass=ABCMeta):
    __version__ = '2022.11.06'

    @classmethod
    @final
    def _x1_x2_to_rect(cls, x1: int, x2: int) -> Rect:
        h = cls.get_target_resolution().height
        return Rect(x1, 1, x2, h - 1)

    # 所有截图都会缩放到下面的分辨率
    @staticmethod
    def get_target_resolution() -> Optional[Resolution]:
        raise NotImplementedError

    # AP检测
    @staticmethod
    @plot_rect
    def get_ap_bar_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_ap_green_threshold() -> int:
        raise NotImplementedError

    # 跑芙芙的检测
    @staticmethod
    @plot_rect
    def get_fufu_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_fufu_blank_binarization_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_fufu_blank_ratio_threshold() -> float:
        raise NotImplementedError

    # Attack按钮
    @staticmethod
    @plot_rect
    def get_attack_button_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_attack_button_diff_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_attack_button_anchor_file() -> str:
        raise NotImplementedError

    # 助战的scrollbar
    @staticmethod
    @plot_rect
    def get_support_scrollbar_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_support_scrollbar_gray_threshold() -> int:
        raise NotImplementedError

    # 助战界面的垂直位置检测
    @staticmethod
    def get_support_detection_x() -> Tuple[int, int]:
        raise NotImplementedError

    @classmethod
    @final
    @plot_rect
    def _get_support_detection_rect(cls) -> Rect:
        # internal use
        return cls._x1_x2_to_rect(*cls.get_support_detection_x())

    @staticmethod
    def get_support_detection_diff_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_detection_gray_grad_offset_pixel() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_detection_y_len_threshold_range() -> Tuple[int, int]:
        raise NotImplementedError

    # 助战从者框的水平位置（垂直位置通过上面的参数给出）
    @staticmethod
    def get_support_detection_servant_x() -> Tuple[int, int]:
        raise NotImplementedError

    @classmethod
    @final
    @plot_rect
    def _get_support_detection_rect(cls) -> Rect:
        # internal use
        return cls._x1_x2_to_rect(*cls.get_support_detection_servant_x())

    @staticmethod
    def get_support_detection_servant_img_size() -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def get_support_detection_craft_essence_img_size() -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def get_support_detection_craft_essence_crop_height() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_detection_servant_split_y() -> int:
        raise NotImplementedError

    # 助战识别
    @staticmethod
    def get_database_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_support_empty_file() -> str:
        raise NotImplementedError

    # 助战礼装识别
    @staticmethod
    def get_support_empty_craft_essence_files() -> List[str]:
        raise NotImplementedError

    @staticmethod
    def get_max_break_icon_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_support_craft_essence_max_break_err_threshold() -> float:
        raise NotImplementedError

    # 助战礼装满破图标位置
    @staticmethod
    def get_support_craft_essence_max_break_rect() -> Rect:
        raise NotImplementedError

    # 助战好友识别
    @staticmethod
    def get_support_friend_detect_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_support_friend_binarization_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_friend_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_support_skill_box_rect() -> List[Rect]:
        raise NotImplementedError

    # 助战技能等级识别
    @staticmethod
    def get_support_skill_v_diff_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_skill_v_diff_step_size() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_skill_v_diff_edge_size() -> int:
        raise NotImplementedError

    @staticmethod
    def get_support_skill_binarization_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_support_skill_digit_dir() -> str:
        raise NotImplementedError

    # 出本识别
    @staticmethod
    @plot_rect
    def get_exit_quest_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_exit_quest_diff_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_in_battle_blank_screen_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_in_battle_blank_screen_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_exit_quest_ui_file() -> str:
        raise NotImplementedError

    # 战斗场次识别
    @staticmethod
    @plot_rect
    def get_battle_digit_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_battle_digit_dir() -> str:
        raise NotImplementedError

    @staticmethod
    def get_battle_filter_pixel_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_battle_digit_threshold() -> int:
        raise NotImplementedError

    # TODO: 指令卡识别

    # 刷新助战失败界面
    @staticmethod
    @plot_rect
    def get_support_refresh_refused_detection_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_support_refresh_refused_detection_s_threshold() -> int:
        raise NotImplementedError

    # 加好友界面识别
    @staticmethod
    def get_request_support_ui_file() -> str:
        raise NotImplementedError

    # 吃苹果界面识别
    @staticmethod
    def get_eat_apple_ui_file() -> str:
        raise NotImplementedError

    # 连续出击界面识别
    @staticmethod
    def get_continuous_battle_ui_file() -> str:
        raise NotImplementedError

    # 友情池的十连按钮（非每日首次）识别
    @staticmethod
    @plot_rect
    def get_fp_pool_ui_rect() -> Rect:
        raise NotImplementedError

    # 首次的位置
    @staticmethod
    @plot_rect
    def get_fp_pool_ui_rect_daily() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_ui_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_ui_diff_threshold() -> float:
        raise NotImplementedError

    # double check: 用的是友情点不是石头（必须手动狗头）
    @staticmethod
    @plot_rect
    def get_fp_active_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_fp_active_gray_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_fp_active_gray_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_fp_pool_gacha_confirm_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_gacha_confirm_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_gacha_confirm_diff_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_fp_pool_gacha_skip_check_button_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_gacha_skip_diff_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_fp_pool_gacha_skip_diff_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_fp_item_overflow_file() -> str:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_fp_item_overflow_rect() -> Rect:
        raise NotImplementedError

    # 礼装强化界面识别
    # <===== Craft Essence Synthesis Begin =====
    @staticmethod
    @plot_rect
    def get_craft_essence_synthesis_ui_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_synthesis_ui_gray_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_synthesis_ui_gray_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_size() -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_margin_y() -> int:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_material_ui_size_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_ui_size_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_ui_size_diff_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_order_ascending_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_order_by_rarity_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_order_by_rarity_r_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_order_by_rarity_r_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_smart_filter_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_selective_filter_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_extra_filter_b_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_extra_filter_b_ratio_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_x_range() -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_margin_x() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_n_materials_per_row() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_material_y_start() -> int:
        raise NotImplementedError

    # 礼装框内部的图片
    @staticmethod
    def get_craft_essence_material_inner_image_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_frame_detection_ratio() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_unavailable_v_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_unavailable_v_rescale_ratio() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_empty_slot_h_diff_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_synthesis_result_ui_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_lock_detection_y_range() -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_lock_std_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_wait_synthesis_complete_diff_threshold() -> float:
        raise NotImplementedError

    # grid detection params
    @staticmethod
    def get_craft_essence_grid_detection_tol_pixels() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_grid_detection_hsv_threshold() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_grid_detection_area_min_pixels() -> int:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_grid_detection_conf_threshold() -> float:
        raise NotImplementedError

    @staticmethod
    @plot_rect
    def get_craft_essence_target_rect() -> Rect:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_target_empty_file() -> str:
        raise NotImplementedError

    @staticmethod
    def get_craft_essence_target_empty_diff_threshold() -> float:
        raise NotImplementedError

    # <===== Craft Essence Synthesis End =====
