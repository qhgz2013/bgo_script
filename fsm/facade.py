from .executor import FSMExecutor
from .fgo_state import FgoState
from .state_handler import DirectStateForwarder, SingleClickHandler
from .select_quest_handler import SelectQuestHandler
from attacher import AbstractAttacher
from .select_support_handler import SelectSupportHandler
from .eat_apple_handler import EatAppleHandler
from click_positioning import *
from .in_battle_handler import EnterQuestHandler, WaitAttackOrExitQuestHandler, BattleLoopAttackHandler
from .post_quest_handler import ExitQuestHandler, FriendUIHandler, ContinuousBattleHandler
import logging
from _version import VERSION
from battle_control import ScriptConfiguration

logger = logging.getLogger('bgo_script.fsm')
s = FgoState


class FgoFSMFacadeAbstract:
    def __init__(self):
        logger.info('Fate / Grand Order Auto Battle Controller')
        logger.info('* Version: %s' % VERSION)
        logger.info('* This script is for academic research only, commercial usage is strictly prohibited!')
        logger.info('* 本脚本仅用作学术研究，严禁一切商业行为！')
        self.executor = FSMExecutor()

    def run(self):
        self.executor.run()


class FgoFSMFacade(FgoFSMFacadeAbstract):
    def __init__(self, attacher: AbstractAttacher, cfg: ScriptConfiguration):
        super().__init__()
        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(s.STATE_SELECT_QUEST))
        self.executor.add_state_handler(s.STATE_SELECT_QUEST,
                                        SelectQuestHandler(attacher, s.STATE_AP_CHECK_BEFORE_TEAM_CONFIG, cfg))
        self.executor.add_state_handler(s.STATE_AP_CHECK_BEFORE_TEAM_CONFIG,
                                        EatAppleHandler(attacher, s.STATE_SELECT_SUPPORT, cfg))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT,
                                        SelectSupportHandler(attacher, s.STATE_SELECT_TEAM, cfg))
        self.executor.add_state_handler(s.STATE_SELECT_TEAM, DirectStateForwarder(s.STATE_APPLY_TEAM_CONFIG))
        self.executor.add_state_handler(s.STATE_APPLY_TEAM_CONFIG,
                                        SingleClickHandler(attacher, ENTER_QUEST_BUTTON_X, ENTER_QUEST_BUTTON_Y,
                                                           s.STATE_ENTER_QUEST))
        self.executor.add_state_handler(s.STATE_ENTER_QUEST,
                                        EnterQuestHandler(attacher, s.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT, cfg))
        self.executor.add_state_handler(s.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT,
                                        WaitAttackOrExitQuestHandler(attacher, cfg))
        self.executor.add_state_handler(s.STATE_BATTLE_LOOP_ATK, BattleLoopAttackHandler(attacher, cfg))
        # Loop here
        self.executor.add_state_handler(s.STATE_EXIT_QUEST, ExitQuestHandler(attacher, s.STATE_FRIEND_UI_CHECK))
        self.executor.add_state_handler(s.STATE_FRIEND_UI_CHECK,
                                        FriendUIHandler(attacher, s.STATE_CONTINUOUS_BATTLE_CONFIRM))
        self.executor.add_state_handler(s.STATE_CONTINUOUS_BATTLE_CONFIRM,
                                        ContinuousBattleHandler(attacher, s.STATE_AP_CHECK_CONTINUOUS_BATTLE,
                                                                s.STATE_SELECT_QUEST, cfg))
        self.executor.add_state_handler(s.STATE_AP_CHECK_CONTINUOUS_BATTLE,
                                        EatAppleHandler(attacher, s.STATE_SELECT_SUPPORT_CONTINUOUS_BATTLE, cfg))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT_CONTINUOUS_BATTLE,
                                        SelectSupportHandler(attacher, s.STATE_ENTER_QUEST, cfg))


class FgoFSMFacadeSelectSupport(FgoFSMFacadeAbstract):
    def __init__(self, attacher: AbstractAttacher, cfg: ScriptConfiguration):
        super().__init__()
        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(s.STATE_SELECT_SUPPORT))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT, SelectSupportHandler(attacher, s.STATE_FINISH, cfg))
