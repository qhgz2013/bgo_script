from .executor import FSMExecutor
from .fgo_state import *
from .direct_state_forwarder import DirectStateForwarder


class FgoStateFacade:
    def __init__(self):
        self.executor = FSMExecutor()
        self.executor.add_state_handler(STATE_BEGIN, DirectStateForwarder(STATE_SELECT_QUEST))
        # todo: implement quest select
        self.executor.add_state_handler(STATE_SELECT_QUEST, DirectStateForwarder(STATE_SELECT_SUPPORT))

    def run(self):
        self.executor.run()
