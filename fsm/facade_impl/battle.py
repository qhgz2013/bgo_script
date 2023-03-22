from util import register_handler
from ..facade import FgoFSMFacadeFactory, FgoFSMFacadeBase
from ..fgo_state import FgoState
from bgo_game import ScriptEnv
from ..state_handler import DirectStateForwarder, SingleClickHandler
from ..state_handler_impl import EnterQuestHandler, WaitAttackOrExitQuestHandler, BattleLoopAttackHandler, \
    SelectSupportHandler, SelectQuestHandler, EatAppleHandler, ExitQuestHandler, FriendUIHandler, \
    ContinuousBattleHandler

s = FgoState

__all__ = ['FgoFSMFacadeBattleLoop', 'FgoFSMFacade', 'FgoFSMFacadeSelectSupport']


# Only handles in-battle control, terminated when exiting quest
@register_handler(FgoFSMFacadeFactory, 'battle')
class FgoFSMFacadeBattleLoop(FgoFSMFacadeBase):
    def __init__(self, env: ScriptEnv, forward_state: FgoState = s.STATE_FINISH):
        super().__init__(env, forward_state)
        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(env, s.STATE_ENTER_QUEST))
        self.executor.add_state_handler(s.STATE_ENTER_QUEST,
                                        EnterQuestHandler(env, s.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT))
        self.executor.add_state_handler(s.STATE_BATTLE_LOOP_WAIT_ATK_OR_EXIT,
                                        WaitAttackOrExitQuestHandler(env))
        self.executor.add_state_handler(s.STATE_BATTLE_LOOP_ATK, BattleLoopAttackHandler(env))
        self.executor.add_state_handler(s.STATE_EXIT_QUEST, DirectStateForwarder(env, s.STATE_FINISH))


@register_handler(FgoFSMFacadeFactory, 'full')
class FgoFSMFacade(FgoFSMFacadeBase):
    def __init__(self, env: ScriptEnv, forward_state: FgoState = s.STATE_FINISH):
        super().__init__(env, forward_state)
        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(env, s.STATE_SELECT_QUEST))
        self.executor.add_state_handler(s.STATE_SELECT_QUEST,
                                        SelectQuestHandler(env, s.STATE_AP_CHECK_BEFORE_TEAM_CONFIG))
        self.executor.add_state_handler(s.STATE_AP_CHECK_BEFORE_TEAM_CONFIG,
                                        EatAppleHandler(env, s.STATE_SELECT_SUPPORT))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT, SelectSupportHandler(env, s.STATE_SELECT_TEAM))
        self.executor.add_state_handler(s.STATE_SELECT_TEAM, DirectStateForwarder(env, s.STATE_APPLY_TEAM_CONFIG))
        enter_quest_click = env.click_definitions.enter_quest_button()
        self.executor.add_state_handler(s.STATE_APPLY_TEAM_CONFIG,
                                        SingleClickHandler(env, s.STATE_ENTER_QUEST, enter_quest_click.x,
                                                           enter_quest_click.y, t_before_click=1))
        self.executor.add_state_handler(s.STATE_ENTER_QUEST, FgoFSMFacadeBattleLoop(env, s.STATE_EXIT_QUEST))
        self.executor.add_state_handler(s.STATE_EXIT_QUEST, ExitQuestHandler(env, s.STATE_FRIEND_UI_CHECK))
        self.executor.add_state_handler(s.STATE_FRIEND_UI_CHECK,
                                        FriendUIHandler(env, s.STATE_CONTINUOUS_BATTLE_CONFIRM))
        self.executor.add_state_handler(s.STATE_CONTINUOUS_BATTLE_CONFIRM,
                                        ContinuousBattleHandler(env, s.STATE_AP_CHECK_CONTINUOUS_BATTLE,
                                                                s.STATE_SELECT_QUEST))
        self.executor.add_state_handler(s.STATE_AP_CHECK_CONTINUOUS_BATTLE,
                                        EatAppleHandler(env, s.STATE_SELECT_SUPPORT_CONTINUOUS_BATTLE))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT_CONTINUOUS_BATTLE,
                                        SelectSupportHandler(env, s.STATE_ENTER_QUEST))


@register_handler(FgoFSMFacadeFactory, 'support')
class FgoFSMFacadeSelectSupport(FgoFSMFacadeBase):
    def __init__(self, env: ScriptEnv, forward_state: FgoState = s.STATE_FINISH):
        super().__init__(env, forward_state)
        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(env, s.STATE_SELECT_SUPPORT))
        self.executor.add_state_handler(s.STATE_SELECT_SUPPORT, SelectSupportHandler(env, s.STATE_FINISH))
