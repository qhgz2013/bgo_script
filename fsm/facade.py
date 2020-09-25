from .executor import FSMExecutor
from .fgo_state import *
from .direct_state_forwarder import DirectStateForwarder
from .select_quest_handler import SelectQuestHandler
from attacher import AbstractAttacher
from .select_support_handler import SelectSupportHandler
from config import *
from .single_click_and_wait_fufu_handler import SingleClickAndWaitFufuHandler
from click_positioning import *
from .battle_loop_handler import BattleLoopHandler
from cv_positioning import *
from .exit_quest_handler import ExitQuestHandler
import logging
from _version import VERSION

logger = logging.getLogger('bgo_script.fsm')


class FgoFSMFacade:
    def __init__(self, attacher: AbstractAttacher):
        team_preset = DEFAULT_TEAM_CONFIGURATION
        logger.info('Fate / Grand Order Auto Battle Controller')
        logger.info('* Version: %s' % VERSION)
        logger.info('* This script is free and forbid commercial usage')
        self.executor = FSMExecutor()
        self.executor.add_state_handler(STATE_BEGIN, DirectStateForwarder(STATE_SELECT_SUPPORT))
        self.executor.add_state_handler(STATE_SELECT_QUEST, SelectQuestHandler(attacher, STATE_SELECT_SUPPORT, MAX_AP))
        self.executor.add_state_handler(STATE_SELECT_SUPPORT,
                                        SelectSupportHandler(attacher, STATE_APPLY_TEAM_CONFIG,
                                                             team_preset.support_servant_id,
                                                             team_preset.support_craft_essence_id,
                                                             team_preset.support_craft_essence_max_break,
                                                             team_preset.support_skill_requirement))
        # todo: check team configuration
        self.executor.add_state_handler(STATE_APPLY_TEAM_CONFIG, DirectStateForwarder(STATE_ENTER_QUEST))
        self.executor.add_state_handler(STATE_ENTER_QUEST,
                                        SingleClickAndWaitFufuHandler(attacher, ENTER_QUEST_BUTTON_X,
                                                                      ENTER_QUEST_BUTTON_Y, STATE_BATTLE_LOOP))
        self.executor.add_state_handler(STATE_BATTLE_LOOP, BattleLoopHandler(attacher, STATE_EXIT_QUEST, team_preset,
                                                                             apply_action, CV_BATTLE_DIGIT_DIRECTORY))
        # Loop here
        self.executor.add_state_handler(STATE_EXIT_QUEST, ExitQuestHandler(attacher, STATE_SELECT_QUEST))
        # NOT USED STATE: STATE_SELECT_TEAM

    def run(self):
        self.executor.run()
