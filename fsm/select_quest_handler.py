from .state_handler import StateHandler
from attacher import AbstractAttacher
from click_positioning import *


class SelectQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int):
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> int:
        # todo: implement quest select
        from .single_click_and_wait_fufu_handler import SingleClickAndWaitFufuHandler
        return SingleClickAndWaitFufuHandler(self.attacher, FIRST_QUEST_X, FIRST_QUEST_Y, self.forward_state).\
            run_and_transit_state()
