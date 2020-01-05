from .executor import FSMExecutor
from .fgo_state import *
from .direct_state_forwarder import DirectStateForwarder
from .select_quest_handler import SelectQuestHandler
from attacher import AbstractAttacher
from click_positioning import *
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
        self.executor.add_state_handler(STATE_SELECT_SUPPORT, SelectSupportHandler(attacher))

    def run(self):
        self.executor.run()
