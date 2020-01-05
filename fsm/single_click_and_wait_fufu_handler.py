from .state_handler import StateHandler
from attacher import AbstractAttacher
from time import sleep
from .wait_fufu_handler import WaitFufuStateHandler


class SingleClickAndWaitFufuHandler(StateHandler):
    def __init__(self, attacher: AbstractAttacher, x: float, y: float, next_state: int):
        self.attacher = attacher
        self.x = x
        self.y = y
        self.wait_fufu_handler = WaitFufuStateHandler(attacher, next_state)

    def run_and_transit_state(self) -> int:
        self.attacher.send_click(self.x, self.y)
        sleep(1)
        return self.wait_fufu_handler.run_and_transit_state()
