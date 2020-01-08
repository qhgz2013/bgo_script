from .state_handler import StateHandler
from .fgo_state import *
from warnings import warn


class FSMExecutor:
    def __init__(self):
        self.state_dict = {}
        self.state = STATE_BEGIN

    def add_state_handler(self, state: int, handler: StateHandler):
        self.state_dict[state] = handler

    def remove_state_handler(self, state: int):
        del self.state_dict[state]

    def run(self):
        while self.state != STATE_ERROR and self.state != STATE_FINISH:
            try:
                handler = self.state_dict[self.state]  # type: StateHandler
            except KeyError:
                warn('No handler found for handling state: %d' % self.state)
                self.state = STATE_ERROR
                break
            next_state = handler.run_and_transit_state()
            if type(next_state) != int:
                warn('Expected state type: int, but got: %s' % str(type(next_state)), RuntimeWarning)
                next_state = STATE_ERROR
            self.state = next_state
