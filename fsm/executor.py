from .state_handler import StateHandler
from .fgo_state import FgoState
import logging

logger = logging.getLogger('bgo_script.fsm')


class FSMExecutor:
    def __init__(self):
        self.state_dict = {}
        self.state = FgoState.STATE_BEGIN

    def add_state_handler(self, state: int, handler: StateHandler):
        self.state_dict[state] = handler

    def remove_state_handler(self, state: int):
        del self.state_dict[state]

    def run(self):
        while self.state.value >= 0:
            try:
                handler = self.state_dict[self.state]  # type: StateHandler
            except KeyError:
                logger.critical('No handler found for handling state: %s' % self.state.name)
                self.state = FgoState.STATE_ERROR
                break
            next_state = handler.run_and_transit_state()
            if type(next_state) != FgoState:
                logger.critical('Expected state type: FgoState, but got: %s' % str(type(next_state)))
                next_state = FgoState.STATE_ERROR
            logger.info('State transition: %s -> %s' % (self.state.name, next_state.name))
            self.state = next_state
        logger.info('Exited state execution chain due to final state %s' % self.state.name)
