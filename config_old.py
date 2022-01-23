from bgo_game import ScriptConfig, EatAppleType, BattleController, DispatchedCommandCard, TeamConfig, ServantConfig, \
    SupportServantConfig, SupportCraftEssenceConfig, CommandCardType
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
            self.use_skill(215, 1).use_support_skill(1).use_support_skill(2, 14).use_clothes_skill(0, 14)
            self.use_skill(14, 0).noble_phantasm(14).attack(0).attack(1)


# class NailGrabberController(BattleController):
#     def __initialize__(self):
#         self._stella = False

#     # noinspection DuplicatedCode
#     def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
#         if battle == 1:
#             self.use_skill(16, 2).noble_phantasm(16).attack(0).attack(1)
#             self.remove_servant(16)
#             self._stella = True
#             return
#         if not self._stella:
#             self.remove_servant(16)
#             self._stella = True
#         if battle == 2:
#             self.use_support_skill(1).use_support_skill(2).use_skill(120, 0)
#             self.noble_phantasm(120).attack(0).attack(1)
#         elif battle == 3:
#             self.use_skill(120, 1).use_skill(219, 1).use_skill(219, 2).use_support_skill(0, 219)
#             self.use_clothes_skill(0, 219).noble_phantasm(120).noble_phantasm(219).attack(0)


class FireworkGrabberController(BattleController):
    def __initialize__(self):
        self._stella = False

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(16, 2).noble_phantasm(16)
            self.attack(0).attack(1)
        if not self._stella:
            self.remove_servant(16)
            self._stella = True
        if battle == 2:
            self.use_support_skill(2).use_support_skill(1).use_skill(120, 0)
            self.noble_phantasm(120).attack(0).attack(1)
        elif battle == 3:
            self.use_skill(120, 1).use_skill(219, 1).use_skill(219, 2)  # .use_clothes_skill(1, 219)
            self.use_support_skill(0, 219)
            self.noble_phantasm(120).noble_phantasm(219).attack(0)


class JeanneArcherWCABController(BattleController):
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(284, 0).use_support_skill(0).use_skill(284, 1, 216).use_support_skill(1, 216)
            self.use_skill(284, 2, 216).use_support_skill(2, 216)
            self.use_skill(216, 0).use_skill(216, 1).use_skill(216, 2)
        elif battle == 3:
            self.use_clothes_skill(1, 216)
        self.noble_phantasm(216).attack(0).attack(1)


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


class DustGrabberController(BattleController):
    def __initialize__(self):
        self._stella = False

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(16, 2).noble_phantasm(16).attack(0).attack(1)
        if not self._stella:
            self.remove_servant(16)
            self._stella = True
        if battle == 2:
            self.use_support_skill(2).use_support_skill(1).use_skill(91, 0).use_skill(91, 1).use_support_skill(0, 91)
            self.noble_phantasm(91).attack(0).attack(1)
        elif battle == 3:
            self.use_skill(76, 0).use_skill(76, 2).use_clothes_skill(0, 76)
            self.noble_phantasm(76).attack(0).attack(1)


class BBAFesStage1Controller(BattleController):
    def __initialize__(self):
        self._changed = False

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(2, 0).use_skill(171, 0).use_skill(171, 1).use_skill(171, 2).use_support_skill(0)
            self.noble_phantasm(2).attack(0).attack(1)
            return
        if battle == 2:
            self.use_support_skill(1, 2).use_support_skill(2, 2)
        if not self._changed:
            self.use_clothes_skill(2, [self.SERVANT_ID_SUPPORT, 284])
            self._changed = True
        if battle == 2:
            self.use_skill(284, 0).use_skill(284, 1, 171)
            self.noble_phantasm(171).attack(0).attack(1)
        elif battle == 3:
            self.use_skill(2, 1).use_skill(2, 2).use_clothes_skill(0).use_skill(284, 2, 2)
            self.noble_phantasm(2).attack(0).attack(1)


# 呆毛+杀生院 6加成（需要呆毛蓝卡，不稳定3T，稳定4T）
class BBAFesStage1Controller2(BattleController):
    def __initialize__(self):
        self._np_enough = False

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            # check saber card
            saber_arts_cards = len([x for x in cards if x.svt_id == 2 and x.card_type == CommandCardType.Arts])
            if turn == 1 and saber_arts_cards == 0:
                # no saber cards in the first turn, preserve skill and wait until next turn
                self.attack(0).attack(1).attack(2)
                return
            self.use_support_skill(0).use_support_skill(1, 167).use_support_skill(2, 167)
            self.use_clothes_skill(2, [self.SERVANT_ID_SUPPORT, 284])
            self.use_skill(284, 0).use_skill(284, 1, 167).use_skill(284, 2, 167)
            self.use_skill(167, 2).use_skill(2, 0)
            self.refresh_command_card_list()
            if saber_arts_cards > 0:
                self.select_command_card(2, CommandCardType.Arts, 1)
                self._np_enough = True
            self.noble_phantasm(167)
            self.select_remain_command_card()
        elif battle == 2:
            self.use_skill(167, 0)
            if not self._np_enough:
                self.select_command_card(2, CommandCardType.Arts, 1)
                self.noble_phantasm(167)
                self.select_remain_command_card()
                self._np_enough = True
            else:
                self.noble_phantasm(167).attack(0).attack(1)
        else:
            if turn == 1:
                self.use_skill(2, 1).use_skill(2, 2).use_clothes_skill(0).use_skill(167, 1)
                self.noble_phantasm(2).attack(0).attack(1)
            else:
                self.attack(0).attack(1).attack(2)

    def __require_battle_card_detection__(self, current_battle: int, max_battle: int, turn: int) -> bool:
        return not self._np_enough


class BBAFesStage2Controller(BattleController):
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_support_skill(0).use_support_skill(1, 258).use_support_skill(2, 258)
            self.use_clothes_skill(2, [self.SERVANT_ID_SUPPORT, 284])
            self.use_skill(284, 0).use_skill(284, 1, 258).use_skill(284, 2, 258)
            self.use_skill(258, 1)
            self.use_skill(16, 2)
            self.use_skill(258, 2, 16)
            self.use_clothes_skill(0)
            self.noble_phantasm(16)
            # select non-arash card first
            remain_cards = 2
            for svt in [284, 258, 16]:
                for card_type in [CommandCardType.Buster, CommandCardType.Arts, CommandCardType.Quick]:
                    remain_cards -= self.select_command_card(svt, card_type, remain_cards)
        elif battle == 2:
            self.noble_phantasm(258).attack(0).attack(1)
            self.remove_servant(16)
        else:
            self.use_skill(241, 0).use_skill(241, 1, 258).use_skill(241, 2, 258)
            self.noble_phantasm(258).attack(0).attack(1)

    # def __require_battle_card_detection__(self, current_battle: int, max_battle: int, turn: int) -> bool:
    #     return current_battle == 1


shell_grabber_team = TeamConfig([
    ServantConfig(svt_id=215),
    ServantConfig(svt_id=16),
    SupportServantConfig(svt_id=215, craft_essence_cfg=SupportCraftEssenceConfig(910, max_break=True)),
    ServantConfig(svt_id=14),
    ServantConfig(svt_id=106),
    ServantConfig(svt_id=59)
])

# WCAB + 弓贞
shell_grabber_team_wcab = TeamConfig([
    ServantConfig(svt_id=284),
    ServantConfig(svt_id=216),
    SupportServantConfig(svt_id=284, craft_essence_cfg=SupportCraftEssenceConfig(910, max_break=True),
                         skill_requirement=[10, 10, 10]),
    ServantConfig(svt_id=14),
    ServantConfig(svt_id=106),
    ServantConfig(svt_id=59)
])

# WCAB + 齐格
nail_grabber_team = TeamConfig([
    ServantConfig(svt_id=284),
    ServantConfig(svt_id=208),
    SupportServantConfig(svt_id=284, craft_essence_cfg=SupportCraftEssenceConfig(910, max_break=True),
                         skill_requirement=[10, 10, 10]),
    ServantConfig(svt_id=16),
    ServantConfig(svt_id=163),
    ServantConfig(svt_id=106)
])

firework_grabber_team = TeamConfig([
    ServantConfig(16),
    SupportServantConfig(37, craft_essence_cfg=SupportCraftEssenceConfig(910, True)),
    ServantConfig(120), ServantConfig(219), ServantConfig(106), ServantConfig(59)
])

tmp = TeamConfig([
    ServantConfig(svt_id=215),
    ServantConfig(svt_id=29),
    SupportServantConfig(svt_id=215, craft_essence_cfg=SupportCraftEssenceConfig(1123, max_break=False),
                         skill_requirement=[10, 10, 10]),
    ServantConfig(svt_id=14),
    ServantConfig(svt_id=106),
    ServantConfig(svt_id=59)
])

dust_grabber_team = TeamConfig([
    ServantConfig(76), ServantConfig(16),
    SupportServantConfig(37, SupportCraftEssenceConfig(910, True), skill_requirement=[10, 10, 10]),
    ServantConfig(91), ServantConfig(219), ServantConfig(141)
])

# wcba + 孔明 + 狂兰，6加成
christmas_team_2 = TeamConfig([
    ServantConfig(215), ServantConfig(48),
    SupportServantConfig(215, SupportCraftEssenceConfig(1126, True), skill_requirement=[10, 10, 10]),
    ServantConfig(37), ServantConfig(1), ServantConfig(2)
])


bba_fes_team1 = TeamConfig([
    ServantConfig(2), ServantConfig(167),
    SupportServantConfig(284, SupportCraftEssenceConfig(1298, True), skill_requirement=[10, 10, 10]),
    ServantConfig(284), ServantConfig(1), ServantConfig(2)
])

bba_fes_team2 = TeamConfig([
    ServantConfig(16), ServantConfig(258),
    SupportServantConfig(284, SupportCraftEssenceConfig(1298, True), skill_requirement=[10, 10, 10]),
    ServantConfig(241), ServantConfig(284), ServantConfig(158)
])


class ChristmasTeam2Controller(BattleController):
    def __initialize__(self):
        self.order_changed = False

    def _select_card(self):
        for t in [CommandCardType.Quick, CommandCardType.Buster, CommandCardType.Arts]:
            self.select_command_card(48, t)
        for t in [CommandCardType.Buster, CommandCardType.Arts, CommandCardType.Quick]:
            for svt_id in [215, 37]:
                self.select_command_card(svt_id, t)

    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(215, 0, 48).use_support_skill(2, 48).use_support_skill(0, 48)
            self.noble_phantasm(48)  # .attack(0).attack(1)
            self.select_remain_command_card()
            # expected 39 np
        elif battle == 2:
            self.use_support_skill(1).use_clothes_skill(2, (self.SERVANT_ID_SUPPORT, 37))
            self.order_changed = True
            self.use_skill(37, 2).use_skill(215, 2, 48)
            self.use_skill(48, 2).use_skill(48, 0)
            self.noble_phantasm(48)
            self._select_card()
        else:
            if not self.order_changed:
                self.order_change(self.SERVANT_ID_SUPPORT, 37)
                self.order_changed = True
            if turn == 1:
                self.use_skill(37, 0, 48).use_clothes_skill(0)
                self.use_skill(37, 1)
                self.noble_phantasm(48)
            self._select_card()


DEFAULT_CONFIG = ScriptConfig(
    eat_apple_type=EatAppleType.DontEatMyApple,
    battle_controller=NailWCABController,
    team_config=nail_grabber_team,
    max_ap=142,
    enable_continuous_battle_feature=True
)
