from ..abstract_detection_def import AbstractDetectionDef
from abc import ABCMeta
from typing import *

__all__ = ['BasicDetectionDefImpl']


# original value defined in cv_positioning.py
class BasicDetectionDefImpl(AbstractDetectionDef, metaclass=ABCMeta):
    @staticmethod
    def get_ap_green_threshold() -> int:
        return 100

    @staticmethod
    def get_fufu_blank_binarization_threshold() -> int:
        return 210  # previous: 195

    @staticmethod
    def get_fufu_blank_ratio_threshold() -> float:
        return 0.98  # previous: 0.995

    @staticmethod
    def get_attack_button_anchor_file() -> str:
        return 'cv_data/attack_button.png'

    @staticmethod
    def get_attack_button_diff_threshold() -> int:
        return 10

    @staticmethod
    def get_support_scrollbar_gray_threshold() -> int:
        return 200

    @staticmethod
    def get_support_detection_diff_threshold() -> int:
        return 80

    @staticmethod
    def get_support_detection_gray_grad_offset_pixel() -> int:
        return 2

    @staticmethod
    def get_database_file() -> str:
        return 'cv_data/fgo_v2.db'

    @staticmethod
    def get_support_empty_file() -> str:
        return 'cv_data/support_empty.png'

    @staticmethod
    def get_support_empty_craft_essence_files() -> List[str]:
        return ['cv_data/support_craft_essence_empty.png', 'cv_data/support_craft_essence_empty2.png']

    @staticmethod
    def get_max_break_icon_file() -> str:
        return 'cv_data/max_break.png'

    @staticmethod
    def get_support_craft_essence_max_break_err_threshold() -> float:
        return 1.8

    @staticmethod
    def get_support_friend_binarization_threshold() -> int:
        return 200

    @staticmethod
    def get_support_skill_v_diff_threshold() -> int:
        return 30

    @staticmethod
    def get_support_skill_v_diff_step_size() -> int:
        return 2

    @staticmethod
    def get_support_skill_v_diff_edge_size() -> int:
        return 3

    @staticmethod
    def get_support_skill_binarization_threshold() -> float:
        return 85 / 255

    @staticmethod
    def get_support_skill_digit_dir() -> str:
        return 'cv_data/support_skill_digit'

    @staticmethod
    def get_exit_quest_diff_threshold() -> int:
        return 7  # previous value: 3

    @staticmethod
    def get_in_battle_blank_screen_threshold() -> int:
        return 30

    @staticmethod
    def get_in_battle_blank_screen_ratio_threshold() -> float:
        return 0.75

    @staticmethod
    def get_exit_quest_ui_file() -> str:
        return 'cv_data/exit_quest_ui.png'

    @staticmethod
    def get_battle_digit_dir() -> str:
        return 'cv_data/battle_digit'

    @staticmethod
    def get_battle_filter_pixel_threshold() -> int:
        return 40

    @staticmethod
    def get_battle_digit_threshold() -> int:
        return 140

    @staticmethod
    def get_support_refresh_refused_detection_s_threshold() -> int:
        return 5

    @staticmethod
    def get_request_support_ui_file() -> str:
        return 'cv_data/request_support_ui.png'

    @staticmethod
    def get_eat_apple_ui_file() -> str:
        return 'cv_data/eat_apple_ui.png'

    @staticmethod
    def get_continuous_battle_ui_file() -> str:
        return 'cv_data/continuous_battle.png'

    @staticmethod
    def get_fp_pool_ui_file() -> str:
        return 'cv_data/fp_gacha_button.png'

    @staticmethod
    def get_fp_pool_ui_diff_threshold() -> float:
        return 20  # > 14

    @staticmethod
    def get_fp_active_gray_threshold() -> int:
        return 150

    @staticmethod
    def get_fp_active_gray_ratio_threshold() -> float:
        return 0.01

    @staticmethod
    def get_fp_pool_gacha_confirm_file() -> str:
        return 'cv_data/fp_gacha_confirm.png'

    @staticmethod
    def get_fp_pool_gacha_confirm_diff_threshold() -> float:
        return 15  # previous: 20, found min: 17.4

    @staticmethod
    def get_fp_pool_gacha_skip_diff_threshold() -> float:
        return 40  # previous: 20

    @staticmethod
    def get_fp_pool_gacha_skip_diff_file() -> str:
        return 'cv_data/fp_anchor.png'

    @staticmethod
    def get_fp_item_overflow_file() -> str:
        return 'cv_data/fp_item_overflow.png'

    @staticmethod
    def get_craft_essence_synthesis_ui_gray_threshold() -> float:
        return 90

    @staticmethod
    def get_craft_essence_synthesis_ui_gray_ratio_threshold() -> float:
        return 0.98

    @staticmethod
    def get_craft_essence_material_ui_size_file() -> str:
        return 'cv_data/synthesis_ui_size.png'

    @staticmethod
    def get_craft_essence_ui_size_diff_threshold() -> float:
        return 20  # correct: < 20, others are: 31.3, 50.8

    @staticmethod
    def get_craft_essence_order_by_rarity_r_threshold() -> float:
        return 120

    @staticmethod
    def get_craft_essence_order_by_rarity_r_ratio_threshold() -> float:
        return 0.7

    @staticmethod
    def get_craft_essence_extra_filter_b_threshold() -> float:
        return 150

    @staticmethod
    def get_craft_essence_extra_filter_b_ratio_threshold() -> float:
        return 0.6  # 0.16 if disable, 0.7 if enabled

    @staticmethod
    def get_craft_essence_n_materials_per_row() -> int:
        return 7

    @staticmethod
    def get_craft_essence_frame_detection_ratio() -> float:
        return 0.23

    @staticmethod
    def get_craft_essence_unavailable_v_threshold() -> float:
        return 0.5  # should be less than 1 - get_craft_essence_unavailable_v_rescale_ratio()

    @staticmethod
    def get_craft_essence_unavailable_v_rescale_ratio() -> float:
        return 0.4

    @staticmethod
    def get_craft_essence_empty_slot_h_diff_threshold() -> int:
        return 20  # <= 75

    @staticmethod
    def get_craft_essence_synthesis_result_ui_file() -> str:
        return 'cv_data/ce_synthesis_result.png'

    @staticmethod
    def get_craft_essence_lock_std_threshold() -> float:
        return 50  # locked >= 70, unlock <= 28

    @staticmethod
    def get_craft_essence_wait_synthesis_complete_diff_threshold() -> float:
        return 5  # <= 5 ok, previous: 3

    @staticmethod
    def get_craft_essence_grid_detection_tol_pixels() -> int:
        return 3

    @staticmethod
    def get_craft_essence_grid_detection_hsv_threshold() -> int:
        return 30

    @staticmethod
    def get_craft_essence_grid_detection_conf_threshold() -> float:
        return 0.8

    @staticmethod
    def get_craft_essence_target_empty_file() -> str:
        return 'cv_data/craft_essence_target_empty.png'

    @staticmethod
    def get_craft_essence_target_empty_diff_threshold() -> float:
        return 10  # <= 3
