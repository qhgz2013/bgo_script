from util import register_handler
from ..facade import FgoFSMFacadeFactory, FgoFSMFacadeBase
from bgo_game import ScriptEnv
from ..fgo_state import FgoState

__all__ = ['FgoFSMFacadeFriendPointGacha']


@register_handler(FgoFSMFacadeFactory, 'friend_point')
class FgoFSMFacadeFriendPointGacha(FgoFSMFacadeBase):
    def __init__(self, env: ScriptEnv, forward_state: FgoState = FgoState.STATE_FINISH):
        super(FgoFSMFacadeFriendPointGacha, self).__init__(env, forward_state)
