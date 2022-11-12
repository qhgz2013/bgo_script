from .executor import FSMExecutor
from .fgo_state import FgoState
from .state_handler import StateHandler
# from .select_support_handler import SelectSupportHandler
# from fsm.state_handler_impl.eat_apple_handler import EatAppleHandler
# from archives.click_positioning import *
# from .in_battle_handler import EnterQuestHandler, WaitAttackOrExitQuestHandler, BattleLoopAttackHandler
import logging
from _version import VERSION
from bgo_game import ScriptEnv
from util import HandlerRegistry

__all__ = ['FgoFSMFacadeBase', 'FgoFSMFacadeFactory']

logger = logging.getLogger('bgo_script.fsm')


# keep this class?
class FgoFSMFacadeBase(StateHandler):
    _logged_msg = False

    def __init__(self, env: ScriptEnv, forward_state: FgoState = FgoState.STATE_FINISH):
        super(FgoFSMFacadeBase, self).__init__(env, forward_state)
        if not FgoFSMFacadeBase._logged_msg:
            logger.info('Fate / Grand Order Auto Battle Controller')
            logger.info('* Version: %s' % VERSION)
            logger.info('* This script is for academic research only, commercial usage is strictly prohibited!')
            logger.info('* 本脚本仅用作学术研究，严禁一切商业行为！')
            FgoFSMFacadeBase._logged_msg = True
        self.executor = FSMExecutor()

    def run_and_transit_state(self) -> FgoState:
        if self.executor.state == FgoState.STATE_ERROR:
            return FgoState.STATE_ERROR
        # reset state
        self.executor.state = FgoState.STATE_BEGIN
        self.executor.run()
        return self.forward_state


class FgoFSMFacadeFactory(HandlerRegistry[str, StateHandler]):
    pass
