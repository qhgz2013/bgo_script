from ._class_def import EatAppleType, TeamConfiguration, BattleController
from typing import *


# 定义脚本的全局变量，传入facade中用作初始化所有状态以及状态转移所执行的动作
class ScriptConfiguration:
    def __init__(self, eat_apple_type: EatAppleType, battle_controller: Type[BattleController],
                 team_config: TeamConfiguration, max_ap: Optional[int] = None,
                 detect_command_card: bool = True, enable_continuous_battle_feature: bool = True):
        self.eat_apple_type = eat_apple_type
        self.battle_controller = battle_controller
        self.team_config = team_config
        self.max_ap = max_ap
        self.detect_command_card = detect_command_card
        self.DO_NOT_MODIFY_BATTLE_VARS = {}  # type: Dict[str, Any]
        self.enable_continuous_battle = enable_continuous_battle_feature
