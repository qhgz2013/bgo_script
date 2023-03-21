from util import register_handler
from ..facade import FgoFSMFacadeFactory, FgoFSMFacadeBase
from bgo_game import ScriptEnv
from ..fgo_state import FgoState
from ..state_handler import DirectStateForwarder
from ..state_handler_impl import *

__all__ = ['FgoFSMFacadeFriendPointGacha']

s = FgoState


@register_handler(FgoFSMFacadeFactory, 'friend_point')
class FgoFSMFacadeFriendPointGacha(FgoFSMFacadeBase):
    def __init__(self, env: ScriptEnv, forward_state: FgoState = FgoState.STATE_FINISH):
        super(FgoFSMFacadeFriendPointGacha, self).__init__(env, forward_state)

        self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(env, s.STATE_CHECK_FP_GACHA_UI))
        # self.executor.add_state_handler(s.STATE_BEGIN, DirectStateForwarder(env, s.STATE_FP_GACHA_ITEM_OVERFLOW_CE))
        self.executor.add_state_handler(s.STATE_CHECK_FP_GACHA_UI,
                                        CheckFriendPointGachaUIHandler(env, s.STATE_FP_GACHA_CONFIRM))
        self.executor.add_state_handler(s.STATE_FP_GACHA_CONFIRM,
                                        FriendPointGachaConfirmHandler(env, s.STATE_FP_GACHA_SKIP))
        self.executor.add_state_handler(s.STATE_FP_GACHA_SKIP,
                                        FriendPointGachaSkipHandler(env, s.STATE_FP_GACHA_CONFIRM))
        self.executor.add_state_handler(s.STATE_FP_GACHA_ITEM_OVERFLOW,
                                        FriendPointGachaItemOverflowHandler(env, s.STATE_ERROR))
        self.executor.add_state_handler(s.STATE_FP_GACHA_ITEM_OVERFLOW_SVT,
                                        DirectStateForwarder(env, s.STATE_FINISH))
        self.executor.add_state_handler(s.STATE_FP_GACHA_ITEM_OVERFLOW_CE,
                                        CraftEssenceSynthesisHandler(env, s.STATE_FINISH))
