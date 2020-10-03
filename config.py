from battle_control import ScriptConfiguration, EatAppleType, BattleController, DispatchedCommandCard, \
    TeamConfiguration, ServantConfiguration, SupportServantConfiguration
from typing import *


class DefaultScriptController(BattleController):
    # battle_action is changed to here
    def __call__(self, battle: int, max_battle: int, turn: int, cards: Optional[Sequence[DispatchedCommandCard]]):
        if battle == 1:
            self.use_skill(90, 0, 29)
            self.use_skill(90, 1, 29)
            self.use_clothes_skill(2, [90, self.SERVANT_ID_SUPPORT])
            self.use_support_skill(0, 29)
            self.use_skill(215, 0, 29)
            self.noble_phantasm(29)
            self.attack(0)
            self.attack(1)
        elif battle == 2:
            self.use_support_skill(2, 29)
            self.noble_phantasm(29)
            self.attack(0)
            self.attack(1)
        elif battle == 3:
            self.use_skill(215, 2, 29)
            self.use_support_skill(1)
            self.use_skill(215, 1)
            self.use_clothes_skill(0)
            self.noble_phantasm(29)
            self.attack(0)
            self.attack(1)


DEFAULT_CONFIG = ScriptConfiguration(
    eat_apple_type=EatAppleType.GoldApple,
    battle_controller=DefaultScriptController,
    team_config=TeamConfiguration(servants=[
        ServantConfiguration(svt_id=215, craft_essence_id=1110),
        ServantConfiguration(svt_id=29, craft_essence_id=34),
        ServantConfiguration(svt_id=90, craft_essence_id=1110),
        SupportServantConfiguration(svt_id=215, craft_essence_id=1110, craft_essence_max_break=True),
        ServantConfiguration(svt_id=260, craft_essence_id=1110),
        ServantConfiguration(svt_id=259, craft_essence_id=1110)
    ]),
    max_ap=142,
    detect_command_card=False,
    enable_continuous_battle_feature=True
)
