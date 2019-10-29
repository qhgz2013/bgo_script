from .state_handler import StateHandler


class DirectStateForwarder(StateHandler):
    def __init__(self, forward_state: int):
        self.forward_state = forward_state

    def run_and_transit_state(self) -> int:
        return self.forward_state
