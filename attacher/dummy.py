from .abstract import AbstractAttacher
import numpy as np
from typing import *
import logging

logger = logging.getLogger('bgo_script.attacher.dummy')


# Do nothing, except log the callings
class DummyAttacher(AbstractAttacher):
    def get_screenshot(self, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        logger.info('Method called: get_screenshot(%s, %s)' % (str(width), str(height)))
        return np.zeros([height, width, 3], dtype='uint8')

    def send_slide(self, p_from: Tuple[float, float], p_to: Tuple[float, float], stay_time_before_move: float = 0.1,
                   stay_time_move: float = 0.8, stay_time_after_move: float = 0.1):
        logger.info('Method called: send_slice(%s, %s, %s, %s, %s)' %
                    (str(p_from), str(p_to), stay_time_before_move, stay_time_move, stay_time_after_move))

    def send_click(self, x: float, y: float, stay_time: float = 0.1):
        logger.info('Method called: send_click(%s, %s, %s)' % (str(x), str(y), str(stay_time)))
