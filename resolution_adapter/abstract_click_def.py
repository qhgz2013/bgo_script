from abc import ABCMeta
from .resolution_match_rule import Resolution, Point
from .plot_util import plot_point
from typing import *

__all__ = ['AbstractClickDef']


class AbstractClickDef(metaclass=ABCMeta):
    __version__ = '2022.11.06'

    @staticmethod
    def get_target_resolution() -> Optional[Resolution]:
        raise NotImplementedError

    # 恰苹果
    @staticmethod
    @plot_point
    def eat_bronze_apple() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_silver_apple() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_gold_apple() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_saint_quartz() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def eat_bronze_sapling() -> Point:
        raise NotImplementedError

    # 确认恰苹果
    @staticmethod
    @plot_point
    def eat_apple_confirm() -> Point:
        raise NotImplementedError

    # 取消恰苹果
    @staticmethod
    @plot_point
    def eat_apple_cancel() -> Point:
        raise NotImplementedError

    # 选第一个本位置
    @staticmethod
    @plot_point
    def enter_first_quest() -> Point:
        raise NotImplementedError

    # 出本结算的点击位置
    @staticmethod
    @plot_point
    def exit_battle_button() -> Point:
        raise NotImplementedError

    # 刷新支援
    @staticmethod
    @plot_point
    def support_refresh() -> Point:
        raise NotImplementedError

    # 确定刷新支援
    @staticmethod
    @plot_point
    def support_refresh_confirm() -> Point:
        raise NotImplementedError

    # 编队界面进本按钮
    @staticmethod
    @plot_point
    def enter_quest_button() -> Point:
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_adb() -> int:
        raise NotImplementedError

    @staticmethod
    def support_scrolldown_y_mumu() -> int:
        raise NotImplementedError

    # 使用技能/点击攻击/选择指令卡/换人的操作的点击坐标
    @staticmethod
    @plot_point
    def skill_buttons() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def np_buttons() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def change_servant() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def command_card() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def clothes_button() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def clothes_skills() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def to_servant() -> List[Point]:
        raise NotImplementedError

    # todo: 6 enemies
    @staticmethod
    @plot_point
    def select_enemy() -> List[Point]:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def attack_button() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def apply_order_change_button() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def attack_back_button() -> Point:
        raise NotImplementedError

    # 助战刷新
    @staticmethod
    @plot_point
    def support_refresh_refused_confirm() -> Point:
        raise NotImplementedError

    # 添加好友：跳过/申请
    @staticmethod
    @plot_point
    def support_request_skip() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def support_request_apply() -> Point:
        raise NotImplementedError

    # 连续出击
    @staticmethod
    @plot_point
    def continuous_battle_confirm() -> Point:
        raise NotImplementedError

    @staticmethod
    @plot_point
    def continuous_battle_cancel() -> Point:
        raise NotImplementedError

    # 技能加速
    @staticmethod
    @plot_point
    def skill_speedup() -> Point:
        raise NotImplementedError

