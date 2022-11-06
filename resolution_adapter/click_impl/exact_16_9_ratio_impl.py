from ..abstract_click_def import AbstractClickDef
from ..resolution_match_rule import Resolution, Point, ExactWidthHeightRatioMatchRule
from ..factory import ClickDefFactory
from typing import *
from util import register_handler


@register_handler(ClickDefFactory, ExactWidthHeightRatioMatchRule(16 / 9))
class Exact16x9RatioClickDefImpl(AbstractClickDef):
    @staticmethod
    def get_target_resolution() -> Optional[Resolution]:
        return Resolution(1280, 720)

    # 恰苹果
    @staticmethod
    def eat_bronze_apple() -> Point:
        # todo: this is replaced by eat_bronze_sapling
        raise NotImplementedError

    @staticmethod
    def eat_silver_apple() -> Point:
        return Point(600, 465)

    @staticmethod
    def eat_gold_apple() -> Point:
        return Point(600, 350)

    @staticmethod
    def eat_saint_quartz() -> Point:
        return Point(600, 200)

    @staticmethod
    def eat_bronze_sapling() -> Point:
        return Point(600, 555)

    # 确认恰苹果
    @staticmethod
    def eat_apple_confirm() -> Point:
        return Point(800, 560)

    # 取消恰苹果
    @staticmethod
    def eat_apple_cancel() -> Point:
        return Point(640, 612)

    # 选第一个本位置
    @staticmethod
    def enter_first_quest() -> Point:
        return Point(960, 190)

    # 出本结算的点击位置
    @staticmethod
    def exit_battle_button() -> Point:
        return Point(1100, 680)

    # 刷新支援
    @staticmethod
    def support_refresh() -> Point:
        return Point(925, 130)

    # 确定刷新支援
    @staticmethod
    def support_refresh_confirm() -> Point:
        return Point(840, 560)

    # 编队界面进本按钮
    @staticmethod
    def enter_quest_button() -> Point:
        return Point(1200, 670)

    @staticmethod
    def support_scrolldown_y_adb() -> int:
        return 327

    @staticmethod
    def support_scrolldown_y_mumu() -> int:
        return 367

    # 使用技能/点击攻击/选择指令卡/换人的操作的点击坐标
    @staticmethod
    def skill_buttons() -> List[Point]:
        return [Point(70, 570), Point(160, 570), Point(260, 570),
                Point(385, 570), Point(480, 570), Point(580, 570),
                Point(705, 570), Point(800, 570), Point(895, 570)]

    @staticmethod
    def np_buttons() -> List[Point]:
        return [Point(384, 201), Point(640, 201), Point(896, 201)]

    @staticmethod
    def change_servant() -> List[Point]:
        return [Point(140, 350), Point(340, 350), Point(540, 350), Point(740, 350), Point(940, 350), Point(1140, 350)]

    @staticmethod
    def command_card() -> List[Point]:
        return [Point(128, 497), Point(384, 497), Point(640, 497), Point(896, 497), Point(1152, 497)]

    @staticmethod
    def clothes_button() -> Point:
        return Point(1195, 310)

    @staticmethod
    def clothes_skills() -> List[Point]:
        return [Point(905, 310), Point(995, 310), Point(1080, 310)]

    @staticmethod
    def to_servant() -> List[Point]:
        return [Point(330, 450), Point(650, 450), Point(970, 450)]

    # todo: 6 enemies
    @staticmethod
    def select_enemy() -> List[Point]:
        return [Point(45, 40), Point(285, 40), Point(525, 40)]

    @staticmethod
    def attack_button() -> Point:
        return Point(1140, 605)

    @staticmethod
    def apply_order_change_button() -> Point:
        return Point(640, 625)

    @staticmethod
    def attack_back_button() -> Point:
        return Point(1200, 680)

    # 助战刷新
    @staticmethod
    def support_refresh_refused_confirm() -> Point:
        return Point(650, 550)

    # 添加好友：跳过/申请
    @staticmethod
    def support_request_skip() -> Point:
        return Point(330, 615)

    @staticmethod
    def support_request_apply() -> Point:
        return Point(950, 615)

    # 连续出击
    @staticmethod
    def continuous_battle_confirm() -> Point:
        return Point(833, 566)

    @staticmethod
    def continuous_battle_cancel() -> Point:
        return Point(433, 566)

    # 技能加速
    @staticmethod
    def skill_speedup() -> Point:
        return Point(960, 360)
