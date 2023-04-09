from ..abstract_click_def import AbstractClickDef
from ..resolution_match_rule import ExactWidthHeightRatioMatchRule
from ..factory import ClickDefFactory
from typing import *
from util import register_handler
from basic_class import *

__all__ = ['Exact20x9RatioClickDefImpl']


@register_handler(ClickDefFactory, ExactWidthHeightRatioMatchRule(20 / 9))
class Exact20x9RatioClickDefImpl(AbstractClickDef):
    # 恰苹果
    @staticmethod
    def eat_bronze_apple() -> PointF:
        # todo: this is replaced by eat_bronze_sapling
        raise NotImplementedError

    @staticmethod
    def eat_silver_apple() -> PointF:
        # return PointF(0.469, 0.648)
        raise NotImplementedError

    @staticmethod
    def eat_gold_apple() -> PointF:
        # return PointF(0.469, 0.486)
        raise NotImplementedError

    @staticmethod
    def eat_saint_quartz() -> PointF:
        # return PointF(0.469, 0.278)
        raise NotImplementedError

    @staticmethod
    def eat_bronze_sapling() -> PointF:
        # return PointF(0.469, 0.769)
        raise NotImplementedError

    # 确认恰苹果
    @staticmethod
    def eat_apple_confirm() -> PointF:
        # return PointF(0.625, 0.778)
        raise NotImplementedError

    # 取消恰苹果
    @staticmethod
    def eat_apple_cancel() -> PointF:
        # return PointF(0.5, 0.85)
        raise NotImplementedError

    # 选第一个本位置
    @staticmethod
    def enter_first_quest() -> PointF:
        # return PointF(0.75, 0.264)
        raise NotImplementedError

    # 出本结算的点击位置
    @staticmethod
    def exit_battle_button() -> PointF:
        # return PointF(0.859, 0.944)
        raise NotImplementedError

    # 刷新支援
    @staticmethod
    def support_refresh() -> PointF:
        # return PointF(0.724, 0.181)
        raise NotImplementedError

    # 确定刷新支援
    @staticmethod
    def support_refresh_confirm() -> PointF:
        # return PointF(0.656, 0.778)
        raise NotImplementedError

    # 编队界面进本按钮
    @staticmethod
    def enter_quest_button() -> PointF:
        # return PointF(0.938, 0.931)
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_adb() -> float:
        # return 0.455
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_mumu() -> float:
        # return 0.51
        raise NotImplementedError

    # 使用技能/点击攻击/选择指令卡/换人的操作的点击坐标
    @staticmethod
    def skill_buttons() -> List[PointF]:
        # return [PointF(0.055, 0.792), PointF(0.125, 0.792), PointF(0.203, 0.792),
        #         PointF(0.3, 0.792), PointF(0.375, 0.792), PointF(0.453, 0.792),
        #         PointF(0.55, 0.792), PointF(0.625, 0.792), PointF(0.7, 0.792)]
        raise NotImplementedError

    @staticmethod
    def np_buttons() -> List[PointF]:
        # return [PointF(0.3, 0.28), PointF(0.5, 0.28), PointF(0.7, 0.28)]
        raise NotImplementedError

    @staticmethod
    def change_servant() -> List[PointF]:
        # return [PointF(0.109, 0.486), PointF(0.266, 0.486), PointF(0.422, 0.486),
        #         PointF(0.578, 0.486), PointF(0.734, 0.486), PointF(0.891, 0.486)]
        raise NotImplementedError

    @staticmethod
    def command_card() -> List[PointF]:
        # return [PointF(0.1, 0.69), PointF(0.23, 0.69), PointF(0.5, 0.69), PointF(0.7, 0.69), PointF(0.9, 0.69)]
        raise NotImplementedError

    @staticmethod
    def clothes_button() -> PointF:
        # return PointF(0.934, 0.43)
        raise NotImplementedError

    @staticmethod
    def clothes_skills() -> List[PointF]:
        # return [PointF(0.707, 0.43), PointF(0.777, 0.43), PointF(0.844, 0.43)]
        raise NotImplementedError

    @staticmethod
    def to_servant() -> List[PointF]:
        # return [PointF(0.258, 0.625), PointF(0.508, 0.625), PointF(0.75, 0.625)]
        raise NotImplementedError

    # todo: 6 enemies
    @staticmethod
    def select_enemy() -> List[PointF]:
        # return [PointF(0.035, 0.056), PointF(0.223, 0.056), PointF(0.41, 0.056)]
        raise NotImplementedError

    @staticmethod
    def attack_button() -> PointF:
        # return PointF(0.89, 0.84)
        raise NotImplementedError

    @staticmethod
    def apply_order_change_button() -> PointF:
        # return PointF(0.5, 0.868)
        raise NotImplementedError

    @staticmethod
    def attack_back_button() -> PointF:
        # return PointF(0.9375, 0.9444)
        raise NotImplementedError

    # 助战刷新
    @staticmethod
    def support_refresh_refused_confirm() -> PointF:
        # return PointF(0.5078, 0.7639)
        raise NotImplementedError

    # 添加好友：跳过/申请
    @staticmethod
    def support_request_skip() -> PointF:
        # return PointF(0.2578, 0.8542)
        raise NotImplementedError

    @staticmethod
    def support_request_apply() -> PointF:
        # return PointF(0.7422, 0.8542)
        raise NotImplementedError

    # 连续出击
    @staticmethod
    def continuous_battle_confirm() -> PointF:
        # return PointF(0.6511, 0.7871)
        raise NotImplementedError

    @staticmethod
    def continuous_battle_cancel() -> PointF:
        # return PointF(0.3386, 0.7871)
        raise NotImplementedError

    # 技能加速
    @staticmethod
    def skill_speedup() -> PointF:
        # return PointF(0.75, 0.5)
        raise NotImplementedError

    # 友情池
    @staticmethod
    def fp_pool_gacha() -> PointF:
        # return PointF(0.6485, 0.7639)
        return PointF(0.6156, 0.7222)

    @staticmethod
    def fp_pool_gacha_confirm() -> PointF:
        # return PointF(0.6563, 0.7778)
        return PointF(0.625, 0.7847)

    @staticmethod
    def fp_pool_gacha_skip_click() -> PointF:
        return PointF(0.9375, 0.1389)

    @staticmethod
    def fp_pool_continuous_gacha() -> PointF:
        # return PointF(0.5938, 0.9306)
        return PointF(0.575, 0.9097)

    @staticmethod
    def fp_overflow_synthesis() -> PointF:
        return PointF(0.5, 0.6598)

    @staticmethod
    def craft_essence_synthesis_target_select() -> PointF:
        return PointF(0.2225, 0.5556)

    @staticmethod
    def craft_essence_synthesis_material_select() -> PointF:
        return PointF(0.375, 0.2986)

    @staticmethod
    def craft_essence_change_ui_size() -> PointF:
        # return PointF(0.0235, 0.9375)
        return PointF(0.0769, 0.9375)

    @staticmethod
    def craft_essence_synthesis_filter() -> PointF:
        return PointF(0.85, 0.1806)

    @staticmethod
    def craft_essence_order_by_rarity() -> PointF:
        return PointF(0.3656, 0.45)

    @staticmethod
    def craft_essence_toggle_order() -> PointF:
        return PointF(0.9203, 0.1806)

    @staticmethod
    def craft_essence_filter_cancel() -> PointF:
        return PointF(0.3625, 0.889)

    @staticmethod
    def craft_essence_filter_apply() -> PointF:
        return PointF(0.6875, 0.889)

    @staticmethod
    def craft_essence_toggle_smart_filter() -> PointF:
        return PointF(0.4625, 0.6528)

    @staticmethod
    def craft_essence_toggle_selective_filter() -> PointF:
        return PointF(0.7375, 0.6528)

    @staticmethod
    def craft_essence_toggle_lock() -> PointF:
        return PointF(0.0769, 0.5)

    @staticmethod
    def craft_essence_toggle_ce_selection() -> PointF:
        return PointF(0.0769, 0.3333)

    @staticmethod
    def craft_essence_confirm() -> PointF:
        return PointF(0.875, 0.8889)

    @staticmethod
    def craft_essence_double_confirm_yes() -> PointF:
        return PointF(0.625, 0.8194)

    @staticmethod
    def craft_essence_double_confirm_no() -> PointF:
        return PointF(0.375, 0.8194)

    @staticmethod
    def synthesis_cancel() -> PointF:
        return PointF(0.1188, 0.0556)

    @staticmethod
    def menu() -> PointF:
        return PointF(0.8875, 0.9028)

    @staticmethod
    def summon() -> PointF:
        return PointF(0.5, 0.8334)

    @staticmethod
    def switch_friend_point() -> PointF:
        return PointF(0.0813, 0.5)