# This class is split from fsm.BattleLoopHandler
import numpy as np
from ._class_def import DispatchedCommandCard, CommandCardType
from typing import *
from cv_positioning import *
import image_process
import logging
from time import time
from matcher import ServantCommandCardMatcher

logger = logging.getLogger('bgo_script.battle_control')


def _proc_cmd_card_alpha():
    ret = []
    for file in CV_COMMAND_CARD_MASK:
        img = image_process.imread(file)
        _, alpha = image_process.split_rgb_alpha(img)
        ret.append(255 - alpha)
    return ret


class CommandCardDetector:
    _command_card_type_anchor = [image_process.imread(x) for x in CV_COMMAND_CARD_TYPE_FILES]
    _command_card_rev_alpha = _proc_cmd_card_alpha()
    _servant_matcher = ServantCommandCardMatcher()

    @staticmethod
    def detect_command_cards(img: np.ndarray) -> List[DispatchedCommandCard]:
        """
        Detect in-battle command card for current turn (attack button must be pressed before calling this method!)

        :param img: In-game screenshot, with shape (h, w, 3) in RGB format or (h, w, 4) in RGBA format (A channel will
         be ignored)
        :return: A list containing command card info
        """
        assert len(img.shape) == 3, 'Invalid image shape, expected RGB format'
        if img.shape[-1] == 4:
            img = img.shape[..., :3]
        ret_list = []

        # 从者头像与指令卡的padding: Top 25px, Left 40px, Right 40px, Bottom 14px
        # 缩放比到时候根据指令卡边框大小算就ok
        # import matplotlib.pyplot as plt
        t = time()
        for card_idx, (x1, x2) in enumerate(zip(CV_COMMAND_CARD_X1S, CV_COMMAND_CARD_X2S)):
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y*CV_COMMAND_CARD_Y):,
                               int(CV_SCREENSHOT_RESOLUTION_X*x1):int(CV_SCREENSHOT_RESOLUTION_X*x2), :3]
            card_type = 0
            target_err = float('inf')
            y_offset_norm = 0
            # y_offset = 0
            for idx, (command_card_type, offset) in enumerate(zip(CommandCardDetector._command_card_type_anchor,
                                                                  CV_COMMAND_CARD_TYPE_OFFSET)):
                score = np.empty(30, np.float)
                h = command_card_type.shape[0]
                for i in range(30):
                    score[i] = image_process.mean_gray_diff_err(command_card[75+i:75+i+h, ...], command_card_type)
                min_score = np.min(score)
                if min_score < target_err:
                    card_type = idx
                    target_err = min_score
                    y_offset = np.argmin(score) + 75
                    y_offset_norm = y_offset / CV_SCREENSHOT_RESOLUTION_Y - offset + CV_COMMAND_CARD_Y
            # logger.debug('Detected command card type: %s with y offset: %d' %
            #              (_card_type_mapper[card_type+1], y_offset))
            # Extend pixels
            command_card = img[int(CV_SCREENSHOT_RESOLUTION_Y * (y_offset_norm - CV_COMMAND_CARD_EXTEND_TOP)):
                               int(CV_SCREENSHOT_RESOLUTION_Y * (y_offset_norm + CV_COMMAND_CARD_EXTEND_BOTTOM +
                                                                 CV_COMMAND_CARD_HEIGHT)),
                               int(CV_SCREENSHOT_RESOLUTION_X * (x1 - CV_COMMAND_CARD_EXTEND_LEFT)):
                               int(CV_SCREENSHOT_RESOLUTION_X * (x2 + CV_COMMAND_CARD_EXTEND_RIGHT)), :]
            # mask command card: concat RGB with extra alpha channel
            alpha = CommandCardDetector._command_card_rev_alpha[card_type]
            if command_card.shape[:2] != alpha.shape[:2]:
                logger.warning('Width or height of command card rect does not match the alpha mask, alpha mask must be'
                               ' updated to obtain best matching accuracy')
                command_card = image_process.resize(command_card, alpha.shape[1], alpha.shape[0])
            command_card = np.concatenate([command_card, np.expand_dims(alpha, 2)], 2)
            servant_id = CommandCardDetector._servant_matcher.match(command_card)
            ret_list.append(DispatchedCommandCard(servant_id, CommandCardType(card_type+1), card_idx, False, 0))
        logger.info('Detected command card data: %s (used %f sec(s))' % (str(ret_list), time() - t))
        return ret_list
