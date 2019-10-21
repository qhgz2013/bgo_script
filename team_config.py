from typing import *


# 配队信息，用于自动选助战和自动配队
class FgoTeamConfiguration:
    def __init__(self, team_servant_id: List[int], team_craft_essence_id: List[int],
                 support_servant_id: int, support_craft_essence_id: int, support_position: int, priority: int = 1):
        self.team_servant_id = team_servant_id
        self.team_craft_essence_id = team_craft_essence_id
        self.support_servant_id = support_servant_id
        self.support_craft_essence_id = support_craft_essence_id
        self.support_position = support_position
        self.priority = priority
