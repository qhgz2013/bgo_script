from .state_handler import StateHandler
from attacher import AbstractAttacher
from click_positioning import *
from .wait_fufu_handler import WaitFufuStateHandler
from time import sleep


class ExitQuestHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, forward_state: int):
        self.attacher = attacher
        self.forward_state = forward_state

    def run_and_transit_state(self) -> int:
        for _ in range(6):
            self.attacher.send_click(BATTLE_EXIT_BUTTON_X, BATTLE_EXIT_BUTTON_Y)
            sleep(0.5)
        WaitFufuStateHandler(self.attacher, 0).run_and_transit_state()
        return self.forward_state
