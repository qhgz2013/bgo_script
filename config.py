from battle_control import ScriptConfiguration, EatAppleType, BattleController, DispatchedCommandCard, \
    TeamConfiguration, ServantConfiguration, SupportServantConfiguration
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


shell_grabber_team = TeamConfiguration([
    ServantConfiguration(svt_id=215, craft_essence_id=0),
    ServantConfiguration(svt_id=16, craft_essence_id=0),
    SupportServantConfiguration(svt_id=215, craft_essence_id=910, craft_essence_max_break=True),
    ServantConfiguration(svt_id=14, craft_essence_id=0),
    ServantConfiguration(svt_id=106, craft_essence_id=0),
    ServantConfiguration(svt_id=59, craft_essence_id=0)
])

nail_grabber_team = TeamConfiguration([
    ServantConfiguration(svt_id=219, craft_essence_id=0),
    ServantConfiguration(svt_id=120, craft_essence_id=0),
    ServantConfiguration(svt_id=16, craft_essence_id=0),
    SupportServantConfiguration(svt_id=37, craft_essence_id=910, craft_essence_max_break=True),
    ServantConfiguration(svt_id=163, craft_essence_id=0),
    ServantConfiguration(svt_id=106, craft_essence_id=0)
])

tmp = TeamConfiguration([
    ServantConfiguration(svt_id=215, craft_essence_id=0),
    ServantConfiguration(svt_id=16, craft_essence_id=0),
    SupportServantConfiguration(svt_id=215, craft_essence_id=1112, craft_essence_max_break=True),
    ServantConfiguration(svt_id=14, craft_essence_id=0),
    ServantConfiguration(svt_id=106, craft_essence_id=0),
    ServantConfiguration(svt_id=59, craft_essence_id=0)
])

DEFAULT_CONFIG = ScriptConfiguration(
    eat_apple_type=EatAppleType.DontEatMyApple,
    battle_controller=ShellGrabberController,
    team_config=shell_grabber_team,
    max_ap=142,
    detect_command_card=False,
    enable_continuous_battle_feature=True
)
