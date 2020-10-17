from battle_control import ScriptConfiguration, EatAppleType, BattleController, DispatchedCommandCard, \
    TeamConfiguration, ServantConfiguration, SupportServantConfiguration
from typing import *


class DefaultScriptController(BattleController):
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
        elif battle == 2:
            self.noble_phantasm(216)
            self.attack(0)
            self.attack(1)
        elif battle == 3:
            if turn == 1:
                self.use_clothes_skill(0)
                self.use_skill(62, 0)
                self.noble_phantasm(216)
            else:
                self.attack(2)
            self.attack(0)
            self.attack(1)


DEFAULT_CONFIG = ScriptConfiguration(
    eat_apple_type=EatAppleType.DontEatMyApple,
    battle_controller=DefaultScriptController,
    team_config=TeamConfiguration(servants=[
        ServantConfiguration(svt_id=90, craft_essence_id=1110),
        ServantConfiguration(svt_id=216, craft_essence_id=1110),
        SupportServantConfiguration(svt_id=90, craft_essence_id=1110, craft_essence_max_break=True),
        # SupportServantConfiguration(svt_id=0, craft_essence_id=1108, craft_essence_max_break=True),
        ServantConfiguration(svt_id=62, craft_essence_id=1110),
        ServantConfiguration(svt_id=260, craft_essence_id=1110),
        ServantConfiguration(svt_id=259, craft_essence_id=1110)
    ]),
    max_ap=142,
    detect_command_card=False,
    enable_continuous_battle_feature=True
)
