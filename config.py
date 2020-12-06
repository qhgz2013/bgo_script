from battle_control import ScriptConfiguration, EatAppleType, BattleController, DispatchedCommandCard, \
    TeamConfiguration, ServantConfiguration, SupportServantConfiguration, SupportCraftEssenceConfiguration, \
    CommandCardType
from typing import *


class JeanneArcherWBrideTeam(BattleController):
    def __initialize__(self):
        self._order_changed = False

    # battle_action is changed to here
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(90, 0, 216)
            self.use_skill(90, 1, 216)
            self.use_support_skill(0, 216)
            self.use_support_skill(1, 216)
            self.use_clothes_skill(2, [62, self.SERVANT_ID_SUPPORT])
            self.use_skill(62, 2, 216)
            self.use_skill(216, 0)
            self.use_skill(216, 1)
            self.use_skill(216, 2)
            self.noble_phantasm(216)
            self.attack(0)
            self.attack(1)
            self._order_changed = True
            return
        # For debug scene (process terminated before exit quest), order change must be called explicitly
        if not self._order_changed:
            self.order_change(62, self.SERVANT_ID_SUPPORT)
            self._order_changed = True
        if battle == 2:
            self.use_skill(62, 0)
            self.noble_phantasm(216)
            self.attack(0)
            self.attack(1)
        elif battle == 3:
            if turn == 1:
                self.use_clothes_skill(0)
                self.noble_phantasm(216)
            else:
                self.attack(2)
            self.attack(0)
            self.attack(1)


class ShellGrabberController(BattleController):
    def __initialize__(self):
        self._stella = False

    # noinspection DuplicatedCode
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(16, 2).noble_phantasm(16).attack(0).attack(1)
            self.remove_servant(16)
            self._stella = True
            return
        if not self._stella:
            self.remove_servant(16)
            self._stella = True
        if battle == 2:
            self.use_skill(215, 0, 14).use_support_skill(0, 14).use_skill(215, 2, 14).use_skill(14, 2)
            self.noble_phantasm(14).attack(0).attack(1)
        elif battle == 3:
            self.use_skill(215, 1).use_support_skill(1).use_support_skill(2, 14).use_clothes_skill(1, 14)
            self.use_skill(14, 0).noble_phantasm(14).attack(0).attack(1)


class NailGrabberController(BattleController):
    def __initialize__(self):
        self._stella = False

    # noinspection DuplicatedCode
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(16, 2).noble_phantasm(16).attack(0).attack(1)
            self.remove_servant(16)
            self._stella = True
            return
        if not self._stella:
            self.remove_servant(16)
            self._stella = True
        if battle == 2:
            self.use_support_skill(1).use_support_skill(2).use_skill(120, 0)
            self.noble_phantasm(120).attack(0).attack(1)
        elif battle == 3:
            self.use_skill(120, 1).use_skill(219, 1).use_skill(219, 2).use_support_skill(0, 219)
            self.use_clothes_skill(0, 219).noble_phantasm(120).noble_phantasm(219).attack(0)


class TmpController(BattleController):
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(215, 0, 29).use_support_skill(0, 29).use_clothes_skill(1, 29)
            self.noble_phantasm(29).attack(0).attack(1)
        elif battle == 2:
            self.use_skill(215, 2, 29)
            self.noble_phantasm(29).attack(0).attack(1)
        elif battle == 3:
            self.use_support_skill(2, 29).use_support_skill(1).use_skill(215, 1)
            self.noble_phantasm(29).attack(0).attack(1)


shell_grabber_team = TeamConfiguration([
    ServantConfiguration(svt_id=215),
    ServantConfiguration(svt_id=16),
    SupportServantConfiguration(svt_id=215, craft_essence_cfg=SupportCraftEssenceConfiguration(910, max_break=True)),
    ServantConfiguration(svt_id=14),
    ServantConfiguration(svt_id=106),
    ServantConfiguration(svt_id=59)
])

nail_grabber_team = TeamConfiguration([
    ServantConfiguration(svt_id=219),
    ServantConfiguration(svt_id=120),
    ServantConfiguration(svt_id=16),
    SupportServantConfiguration(svt_id=37, craft_essence_cfg=SupportCraftEssenceConfiguration(910, max_break=True)),
    ServantConfiguration(svt_id=163),
    ServantConfiguration(svt_id=106)
])

tmp = TeamConfiguration([
    ServantConfiguration(svt_id=215),
    ServantConfiguration(svt_id=29),
    SupportServantConfiguration(svt_id=215, craft_essence_cfg=SupportCraftEssenceConfiguration(1123, max_break=False),
                                skill_requirement=[10, 10, 10]),
    ServantConfiguration(svt_id=14),
    ServantConfiguration(svt_id=106),
    ServantConfiguration(svt_id=59)
])

# wcba + 孔明 + 宝石狂兰，5加成
christmas_team_1 = TeamConfiguration([
    ServantConfiguration(215), ServantConfiguration(48), ServantConfiguration(37),
    SupportServantConfiguration(215, SupportCraftEssenceConfiguration(1126, True), skill_requirement=[10, 10, 10]),
    ServantConfiguration(1), ServantConfiguration(2)
])


class ChristmasTeam1Controller(BattleController):
    def __initialize__(self):
        self.order_changed = False
        self.use_cba_skill_in_battle2 = False

    # def __require_battle_card_detection__(self, current_battle: int, max_battle: int, turn: int) -> bool:
    #     return current_battle > 1

    def _select_card(self, battle):
        v = 0
        for t in [CommandCardType.Quick, CommandCardType.Buster, CommandCardType.Arts]:
            v += self.select_command_card(48, t)
        if v == 0 and battle == 2:
            # 没有狂兰卡，2面交降防
            self.use_cba_skill_in_battle2 = True
            self.use_skill(215, 1)
        for t in [CommandCardType.Buster, CommandCardType.Arts, CommandCardType.Quick]:
            for svt_id in [215, self.SERVANT_ID_SUPPORT]:
                self.select_command_card(svt_id, t)

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(37, 1).use_skill(37, 2).use_skill(215, 0, 48)
            self.noble_phantasm(48).attack(0).attack(1)
        elif battle == 2:
            if not self.order_changed:
                self.use_skill(37, 0, 48)
                self.use_clothes_skill(2, (37, self.SERVANT_ID_SUPPORT))
                self.refresh_command_card_list()
            else:
                self.order_change(37, self.SERVANT_ID_SUPPORT)
            self.order_changed = True
            self.use_support_skill(0, 48).use_skill(215, 2, 48).use_skill(48, 2).use_skill(48, 0)
            self.noble_phantasm(48)
            self._select_card(battle)
        elif battle == 3:
            if not self.order_changed:
                self.order_change(37, self.SERVANT_ID_SUPPORT)
                self.order_changed = True
            if turn == 1:
                self.use_support_skill(2, 48).use_support_skill(1).use_clothes_skill(0)
                if not self.use_cba_skill_in_battle2:
                    self.use_skill(215, 1)
                self.noble_phantasm(48)
            self._select_card(battle)


DEFAULT_CONFIG = ScriptConfiguration(
    eat_apple_type=EatAppleType.GoldApple,
    battle_controller=ChristmasTeam1Controller,
    team_config=christmas_team_1,
    max_ap=142,
    enable_continuous_battle_feature=True
)
