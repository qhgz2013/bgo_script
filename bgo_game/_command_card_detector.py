# This class is split from fsm.BattleLoopHandler
import numpy as np
from ._class_def import DispatchedCommandCard, CommandCardType
from typing import *
from cv_positioning import *
import image_process
import logging
from time import time
from matcher import ServantCommandCardMatcher

logger = logging.getLogger('bgo_script.bgo_game')


def _proc_cmd_card_alpha():
    ret = []
    for file in CV_COMMAND_CARD_MASK:
        ret.append(image_process.rev_alpha_from_file(file))
    return ret


class CommandCardDetector:
    _command_card_type_anchor = [image_process.imread(x) for x in CV_COMMAND_CARD_TYPE_FILES]
    _command_card_rev_alpha = _proc_cmd_card_alpha()
    _servant_matcher = ServantCommandCardMatcher()
    _command_card_support_anchor = image_process.imread(CV_COMMAND_CARD_SUPPORT_ANCHOR_FILE)
    _command_card_support_rev_alpha = image_process.rev_alpha_from_file(CV_COMMAND_CARD_SUPPORT_ANCHOR_FILE)

    @staticmethod
    def detect_command_cards(img: np.ndarray, candidate_servant_list: Optional[List[int]] = None) \
            -> List[DispatchedCommandCard]:
        """
        Detect in-battle command card for current turn (attack button must be pressed before calling this method!)

        :param img: In-game screenshot, with shape (h, w, 3) in RGB format or (h, w, 4) in RGBA format (A channel will
         be ignored)
        :param candidate_servant_list: An optional parameter, the servant id list to be queried (leave "None" to perform
         full database query)
        :return: A list containing command card info
        """
        assert len(img.shape) == 3, 'Invalid image shape, expected RGB format'
        if img.shape[-1] == 4:
            img = img.shape[..., :3]
        ret_list = []

        # 从者头像与指令卡的padding: Top 25px, Left 42px, Right 42px, Bottom 12px
        t = time()
        for card_idx, (x1, x2) in enumerate(zip(CV_COMMAND_CARD_X1S, CV_COMMAND_CARD_X2S)):
            command_card = img[CV_COMMAND_CARD_Y:, x1:x2, :3].copy()
            card_type = 0
            target_err = float('inf')
            y_offset = 0
            for idx, (command_card_type, offset) in enumerate(zip(CommandCardDetector._command_card_type_anchor,
                                                                  CV_COMMAND_CARD_TYPE_OFFSET)):
                score = np.empty(CV_COMMAND_CARD_Y_DETECTION_LENGTH, np.float)
                h = command_card_type.shape[0]
                for i in range(CV_COMMAND_CARD_Y_DETECTION_LENGTH):
                    y = CV_COMMAND_CARD_Y_DETECTION_OFFSET + i
                    score[i] = image_process.mean_gray_diff_err(command_card[y:y+h, ...], command_card_type)
                min_score = np.min(score)
                if min_score < target_err:
                    card_type = idx
                    target_err = min_score
                    y_offset = np.argmin(score) + CV_COMMAND_CARD_Y_DETECTION_OFFSET - offset + CV_COMMAND_CARD_Y
            # Extend pixels
            command_card = img[y_offset-CV_COMMAND_CARD_EXTEND_TOP:
                               y_offset+CV_COMMAND_CARD_EXTEND_BOTTOM+CV_COMMAND_CARD_HEIGHT,
                               x1-CV_COMMAND_CARD_EXTEND_LEFT:x2+CV_COMMAND_CARD_EXTEND_RIGHT]
            # support detection
            support_part = command_card[CV_COMMAND_CARD_SUPPORT_Y1:CV_COMMAND_CARD_SUPPORT_Y2,
                                        CV_COMMAND_CARD_SUPPORT_X1:CV_COMMAND_CARD_SUPPORT_X2, :]
            # err = image_process.mean_hsv_diff_err(support_part, CommandCardDetector._command_card_support_anchor)
            err = image_process.mean_gray_diff_err(support_part, CommandCardDetector._command_card_support_anchor)
            logger.debug('DEBUG value: command card support detection, gray_err = %f' % err)
            is_support = err < CV_COMMAND_CARD_SUPPORT_GRAY_THRESHOLD
            # mask command card: concat RGB with extra alpha channel
            alpha = CommandCardDetector._command_card_rev_alpha[card_type]
            if command_card.shape[:2] != alpha.shape[:2]:
                logger.warning('Width or height of command card rect does not match the alpha mask, alpha mask must be'
                               ' updated to obtain best matching accuracy')
                alpha = image_process.resize(alpha, command_card.shape[1], command_card.shape[0])
                CommandCardDetector._command_card_rev_alpha[card_type] = alpha
            # composite support mask
            if is_support:
                alpha = alpha.copy()
                alpha[CV_COMMAND_CARD_SUPPORT_Y1:CV_COMMAND_CARD_SUPPORT_Y2,
                      CV_COMMAND_CARD_SUPPORT_X1:CV_COMMAND_CARD_SUPPORT_X2] = \
                    CommandCardDetector._command_card_support_rev_alpha
            command_card = np.concatenate([command_card, np.expand_dims(alpha, 2)], 2)
            servant_id = CommandCardDetector._servant_matcher.match(command_card, candidate_servant_list)
            ret_list.append(DispatchedCommandCard(servant_id, CommandCardType(card_type+1), card_idx, is_support, 0))
        logger.info('Detected command card data: %s (used %f sec(s))' % (str(ret_list), time() - t))
        return ret_list
