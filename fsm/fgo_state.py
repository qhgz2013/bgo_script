from enum import IntEnum


class FgoState(IntEnum):
    STATE_BEGIN = 0
    STATE_FINISH = -1
    STATE_ERROR = -2

    STATE_SELECT_QUEST = 1
    STATE_AP_CHECK_BEFORE_TEAM_CONFIG = 2
    STATE_SELECT_SUPPORT = 3
    STATE_SELECT_TEAM = 4
    STATE_APPLY_TEAM_CONFIG = 5
    STATE_ENTER_QUEST = 6
    STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT = 7
    STATE_BATTLE_LOOP_ATK = 8
    STATE_EXIT_QUEST = 9
    STATE_FRIEND_UI_CHECK = 10
    STATE_CONTINUOUS_BATTLE_CONFIRM = 11
    STATE_AP_CHECK_CONTINUOUS_BATTLE = 12
    STATE_SELECT_SUPPORT_CONTINUOUS_BATTLE = 13
