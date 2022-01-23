from bgo_game import ScriptConfig, EatAppleType, BattleController, DispatchedCommandCard, TeamConfig, ServantConfig, SupportServantConfig, SupportCraftEssenceConfig, CommandCard
from typing import *


# 2021 Christmas Event - 90+ Battle
class Christmas21Battle90Plus(BattleController):
    def __initialize__(self):
        self._changed = False

    def __call__(self, current_battle: int, max_battle: int, turn: int, dispatched_cards: Optional[Sequence[DispatchedCommandCard]]):
        if current_battle == 1:
            self.use_skill(266, 0)
            self.use_support_skill(0)
            self.use_support_skill(1, 266).use_support_skill(2, 266)
            self.use_clothes_skill(2, [self.SERVANT_ID_SUPPORT, 284])
            self._changed = True
            self.use_skill(284, 1, 266).use_skill(284, 2, 266)
            self.noble_phantasm(266).attack(0).attack(1)
            return
        if not self._changed:
            # for debug only
            self.use_clothes_skill(2, [self.SERVANT_ID_SUPPORT, 284])
            self._changed = True
        if current_battle == 2:
            self.use_skill(141, 1)
            self.use_skill(141, 2)
            self.use_skill(284, 0)
            self.noble_phantasm(141).attack(0).attack(1)
        else:
            self.use_clothes_skill(0)
            self.use_skill(266, 2)
            self.noble_phantasm(266).attack(0).attack(1)


christmas_21_90plus_team = TeamConfig([
    ServantConfig(266),
    ServantConfig(141),
    SupportServantConfig(284, SupportCraftEssenceConfig(1330, True), skill_requirement=[10, 10, 10]),
    ServantConfig(284),
    ServantConfig(1), ServantConfig(2)
])


# Sieg + WCAB for nail harvesting in 1.5.4
class NailWCABController(BattleController):
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(284, 0).use_support_skill(0).use_skill(284, 1, 208)
            self.use_skill(208, 0).use_support_skill(1, 208)
            self.use_skill(284, 2, 208).use_support_skill(2, 208)
            self.noble_phantasm(208).attack(0).attack(1)
        elif battle == 2:
            self.use_skill(208, 1).use_skill(208, 2).noble_phantasm(208).attack(0).attack(1)
        elif battle == 3:
            self.use_clothes_skill(1, 208)
            self.noble_phantasm(208).attack(0).attack(1)


# WCAB + Sieg
nail_grabber_team = TeamConfig([
    ServantConfig(svt_id=284),
    ServantConfig(svt_id=208),
    SupportServantConfig(svt_id=284, craft_essence_cfg=SupportCraftEssenceConfig(910, max_break=True),
                         skill_requirement=[10, 10, 10]),
    ServantConfig(svt_id=16),
    ServantConfig(svt_id=163),
    ServantConfig(svt_id=106)
])

DEFAULT_CONFIG = ScriptConfig(
    eat_apple_type=EatAppleType.DontEatMyApple,
    battle_controller=NailWCABController,
    team_config=nail_grabber_team,
    max_ap=142
)
