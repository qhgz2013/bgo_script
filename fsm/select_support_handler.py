from .state_handler import StateHandler
from attacher import AbstractAttacher


class SelectSupportHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher):
        self.attacher = attacher

    def run_and_transit_state(self) -> int:
        pass
