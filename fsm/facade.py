from .executor import FSMExecutor
from .fgo_state import *
from .direct_state_forwarder import DirectStateForwarder
from .select_quest_handler import SelectQuestHandler
from attacher import AbstractAttacher
from .select_support_handler import SelectSupportHandler
from .ap_check_handler import ApCheckHandler
from config import *


class FgoFSMFacade:
    def __init__(self, attacher: AbstractAttacher):
        self.executor = FSMExecutor()
        self.executor.add_state_handler(STATE_BEGIN, DirectStateForwarder(STATE_CHECK_AP))
        self.executor.add_state_handler(STATE_CHECK_AP, ApCheckHandler(attacher, MAX_AP, EAT_APPLE_AP_THRESHOLD,
                                                                       STATE_SELECT_QUEST))
        self.executor.add_state_handler(STATE_SELECT_QUEST, SelectQuestHandler(attacher, STATE_SELECT_SUPPORT))
        self.executor.add_state_handler(STATE_SELECT_SUPPORT, SelectSupportHandler(attacher, STATE_APPLY_TEAM_CONFIG,
                                                                                   215, 390))
        # todo: check team configuration
        self.executor.add_state_handler(STATE_APPLY_TEAM_CONFIG, DirectStateForwarder(STATE_ENTER_QUEST))
        self.executor.add_state_handler(STATE_ENTER_QUEST, DirectStateForwarder(STATE_BATTLE_LOOP))
        self.executor.add_state_handler(STATE_BATTLE_LOOP, DirectStateForwarder(STATE_EXIT_QUEST))
        # Loop here
        self.executor.add_state_handler(STATE_EXIT_QUEST, DirectStateForwarder(STATE_CHECK_AP))
        # NOT USED STATE: STATE_SELECT_TEAM

    def run(self):
        self.executor.run()
