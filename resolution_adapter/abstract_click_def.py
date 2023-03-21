from abc import ABCMeta
from basic_class import PointF
from .plot_util import plot_point
from typing import *

__all__ = ['AbstractClickDef']


class AbstractClickDef(metaclass=ABCMeta):
    __version__ = '2022.11.06'

    # 恰苹果
    @staticmethod
    @plot_point
    def eat_bronze_apple() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_silver_apple() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_gold_apple() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_saint_quartz() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_bronze_sapling() -> PointF:
        raise NotImplementedError

    # 确认恰苹果
    @staticmethod
    @plot_point
    def eat_apple_confirm() -> PointF:
        raise NotImplementedError

    # 取消恰苹果
    @staticmethod
    @plot_point
    def eat_apple_cancel() -> PointF:
        raise NotImplementedError

    # 选第一个本位置
    @staticmethod
    @plot_point
    def enter_first_quest() -> PointF:
        raise NotImplementedError

    # 出本结算的点击位置
    @staticmethod
    @plot_point
    def exit_battle_button() -> PointF:
        raise NotImplementedError

    # 刷新支援
    @staticmethod
    @plot_point
    def support_refresh() -> PointF:
        raise NotImplementedError

    # 确定刷新支援
    @staticmethod
    @plot_point
    def support_refresh_confirm() -> PointF:
        raise NotImplementedError

    # 编队界面进本按钮
    @staticmethod
    @plot_point
    def enter_quest_button() -> PointF:
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_adb() -> float:
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_mumu() -> float:
        raise NotImplementedError

    # 使用技能/点击攻击/选择指令卡/换人的操作的点击坐标
    @staticmethod
    @plot_point
    def skill_buttons() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def np_buttons() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def change_servant() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def command_card() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def clothes_button() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def clothes_skills() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def to_servant() -> List[PointF]:
        raise NotImplementedError

    # todo: 6 enemies
    @staticmethod
    @plot_point
    def select_enemy() -> List[PointF]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def attack_button() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def apply_order_change_button() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def attack_back_button() -> PointF:
        raise NotImplementedError

    # 助战刷新
    @staticmethod
    @plot_point
    def support_refresh_refused_confirm() -> PointF:
        raise NotImplementedError

    # 添加好友：跳过/申请
    @staticmethod
    @plot_point
    def support_request_skip() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def support_request_apply() -> PointF:
        raise NotImplementedError

    # 连续出击
    @staticmethod
    @plot_point
    def continuous_battle_confirm() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def continuous_battle_cancel() -> PointF:
        raise NotImplementedError

    # 技能加速
    @staticmethod
    @plot_point
    def skill_speedup() -> PointF:
        raise NotImplementedError

    # 友情池
    @staticmethod
    @plot_point
    def fp_pool_gacha() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def fp_pool_gacha_confirm() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def fp_pool_gacha_skip_click() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def fp_pool_continuous_gacha() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def fp_overflow_synthesis() -> PointF:
        raise NotImplementedError

    # 礼装强化
    # <===== Craft Essence Synthesis Begin =====
    @staticmethod
    @plot_point
    def craft_essence_synthesis_target_select() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_synthesis_material_select() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_change_ui_size() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_synthesis_filter() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_order_by_rarity() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_toggle_order() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_filter_cancel() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_filter_apply() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_toggle_smart_filter() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_toggle_selective_filter() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_toggle_lock() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_toggle_ce_selection() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_confirm() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_cancel() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_double_confirm_yes() -> PointF:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def craft_essence_double_confirm_no() -> PointF:
        raise NotImplementedError

    # <===== Craft Essence Synthesis End =====
