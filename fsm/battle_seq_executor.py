from typing import *
from attacher import AbstractAttacher
from battle_control import ScriptConfiguration, CommandCardDetector, CommandCard
from cv_positioning import *
from click_positioning import *
from time import sleep
import threading
import logging
from .fgo_state import FgoState

logger = logging.getLogger('bgo_script.fsm')
SERVANT_ID_EMPTY = -1
ENEMY_LOCATION_EMPTY = -1
SERVANT_ID_SUPPORT = -2
TIME_WAIT_ATTACK_BUTTON = -1


def _init_battle_vars(d: Dict[str, Any]):
    d.clear()
    d['SGN_BATTLE_STATE_CHANGED'] = threading.Event()
    d['BATTLE_LOOP_NEXT_STATE'] = None
    d['SGN_THD_INIT_FINISHED'] = threading.Event()
    d['SKIP_QUEST_INFO_DETECTION'] = False
    # d['SKIP_TURN_COUNTING'] = False
    d['SGN_WAIT_STATE_TRANSITION'] = threading.Event()
    d['CURRENT_BATTLE'] = 0
    d['MAX_BATTLE'] = 0
    d['TURN'] = 0
    d['DELEGATE_THREAD_EXCEPTION'] = None


class BattleSequenceExecutor:
    def __init__(self, attacher: AbstractAttacher, cfg: ScriptConfiguration, enable_card_reselection_feat: bool = True):
        # enable_card_reselection_feat: when it is set, command cards (including NPs)
        self.SERVANT_ID_EMPTY = SERVANT_ID_EMPTY
        self.ENEMY_LOCATION_EMPTY = ENEMY_LOCATION_EMPTY
        self.SERVANT_ID_SUPPORT = SERVANT_ID_SUPPORT

        self.attacher = attacher
        self.cfg = cfg
        self.team_config = cfg.team_config
        self.enable_card_reselection_feature = enable_card_reselection_feat
        _init_battle_vars(cfg.DO_NOT_MODIFY_BATTLE_VARS)
        self._controller = cfg.battle_controller(self)
        # use another thread to keep execution context while running __call__
        logger.debug('Creating thread to handle controller execution, waiting initialization response')
        thd = threading.Thread(target=self._thd_callback, daemon=True, name='Script controller context')
        thd.start()
        self.cfg.DO_NOT_MODIFY_BATTLE_VARS['SGN_THD_INIT_FINISHED'].wait()
        logger.debug('Thread initialized with TID = %d' % thd.ident)
        self._attack_button_clicked = False
        self._dispatched_cards = None
        self._selected_cmd_cards = []
        self._servants = [x.svt_id for x in self.team_config.self_owned_servants]
        self._servants.insert(self.team_config.support_location, SERVANT_ID_SUPPORT)
        self._last_selected_enemy = None

    def _reset_turn_state(self):
        self._attack_button_clicked = False
        self._selected_cmd_cards = []
        self._last_selected_enemy = None

    def _thd_callback(self):
        var = self.cfg.DO_NOT_MODIFY_BATTLE_VARS
        var['SGN_THD_INIT_FINISHED'].set()
        state_changed = var['SGN_BATTLE_STATE_CHANGED']
        try:
            self._controller.__initialize__()
            while True:
                # recv state_battle_loop signal
                logger.debug('Wait SGN_BATTLE_STATE_CHANGED')
                state_changed.wait()
                state_changed.clear()
                if var['BATTLE_LOOP_NEXT_STATE'] == FgoState.STATE_EXIT_QUEST:
                    break
                var['SKIP_QUEST_INFO_DETECTION'] = True
                self._emit_new_turn(var['CURRENT_BATTLE'], var['MAX_BATTLE'], var['TURN'])
                var['SKIP_QUEST_INFO_DETECTION'] = False
                var['SGN_WAIT_STATE_TRANSITION'].set()
        except Exception as ex:
            type_exc = type(ex)
            logger.critical('Unexpected exception raised in controller thread (type: %s.%s): %s' %
                            (type_exc.__module__, type_exc.__qualname__, str(ex)))
            var['DELEGATE_THREAD_EXCEPTION'] = ex
        finally:
            self._controller.__finalize__()
            var['SGN_WAIT_STATE_TRANSITION'].set()

    def _emit_new_turn(self, current_battle: int, max_battle: int, turn: int):
        self._reset_turn_state()
        self._controller.__turn_initialize__(current_battle, max_battle, turn)
        self._refresh_command_card_list()
        self._controller.__call__(current_battle, max_battle, turn, self._dispatched_cards)
        self._controller.__turn_finalize__(current_battle, max_battle, turn)

    def _lookup_servant_position(self, servant_id: int) -> int:
        if servant_id != SERVANT_ID_EMPTY:
            for i, team_servant_id in enumerate(self._servants):
                if team_servant_id == servant_id:
                    return i
        return -1

    def _submit_click_event(self, t: float, loc: Optional[Tuple[float, float]] = None):
        if t == TIME_WAIT_ATTACK_BUTTON:
            var = self.cfg.DO_NOT_MODIFY_BATTLE_VARS
            var['SGN_WAIT_STATE_TRANSITION'].set()
            logger.debug('Wait SGN_BATTLE_STATE_CHANGED')
            var['SGN_BATTLE_STATE_CHANGED'].wait()
            var['SGN_BATTLE_STATE_CHANGED'].clear()
        elif t > 0:
            sleep(t)
        if loc is not None:
            self.attacher.send_click(loc[0], loc[1])

    def _enter_attack_mode(self):
        if not self._attack_button_clicked:
            self._attack_button_clicked = True
            self._submit_click_event(0.5, (ATTACK_BUTTON_X, ATTACK_BUTTON_Y))
            # re-select previous selected command cards (when executing ATTACK/NP -> SKILL -> ATTACK/NP sequence)
            if self.enable_card_reselection_feature and len(self._selected_cmd_cards) > 0:
                logger.debug('Enabled card reselection feature: perform %d selection' % len(self._selected_cmd_cards))
                for call_fn, args in self._selected_cmd_cards:
                    call_fn(*args)

    def _exit_attack_mode(self):
        if self._attack_button_clicked:
            self._attack_button_clicked = False
            self._submit_click_event(0.5, (ATTACK_BACK_BUTTON_X, ATTACK_BACK_BUTTON_Y))

    def _select_enemy(self, enemy_location: int):
        if enemy_location == ENEMY_LOCATION_EMPTY:
            return
        if self._attack_button_clicked and len(self._selected_cmd_cards) != 0:
            logger.warning('Ignored enemy_location param: it can be specified for the first selection')
            return
        if self._last_selected_enemy is None or self._last_selected_enemy != enemy_location:
            self._submit_click_event(0.5, (ENEMY_XS[enemy_location], ENEMY_Y))
            self._last_selected_enemy = enemy_location

    def remove_servant(self, servant_id: int) -> 'BattleSequenceExecutor':
        # removes the servant like some kind of archer, which dead after NP
        # for SUPPORT SERVANT, refers to SERVANT_ID_SUPPORT
        servant_pos = self._lookup_servant_position(servant_id)
        assert servant_pos >= 0, 'Could not find servant in current team'
        if len(self._servants) <= 3:
            self._servants.remove(servant_id)
        else:
            self._servants[servant_pos] = self._servants[3]
            self._servants = self._servants[:3] + self._servants[4:]
        return self

    def remove_support_servant(self) -> 'BattleSequenceExecutor':
        return self.remove_servant(SERVANT_ID_SUPPORT)

    def order_change(self, svt_id1: int, svt_id2: int) -> 'BattleSequenceExecutor':
        servant_pos1 = self._lookup_servant_position(svt_id1)
        servant_pos2 = self._lookup_servant_position(svt_id2)
        assert servant_pos1 >= 0 and servant_pos2 >= 0, 'Could not find servant in current team'
        t = self._servants[servant_pos1]
        self._servants[servant_pos1] = self._servants[servant_pos2]
        self._servants[servant_pos2] = t
        return self

    def use_skill(self, servant_id: int, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
                  enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        servant_pos = self._lookup_servant_position(servant_id)
        assert 0 <= servant_pos < 3, 'Could not find servant in current team'
        to_servant_pos = self._lookup_servant_position(to_servant_id)
        assert to_servant_pos < 3, 'Could not use skill to backup member'
        self._exit_attack_mode()
        self._select_enemy(enemy_location)
        # 点击技能
        self._submit_click_event(0.5, (SKILL_XS[servant_pos * 3 + skill_index], SKILL_Y))
        # 若是我方单体技能，则选定我方一个目标
        if to_servant_pos != SERVANT_ID_EMPTY:
            self._submit_click_event(0.5, (TO_SERVANT_X[to_servant_pos], TO_SERVANT_Y))
        self._submit_click_event(1, None)
        self._submit_click_event(TIME_WAIT_ATTACK_BUTTON, None)
        return self

    def use_support_skill(self, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
                          enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        return self.use_skill(SERVANT_ID_SUPPORT, skill_index, to_servant_id, enemy_location)

    def _noble_phantasm(self, servant_id: int, enemy_location: int = ENEMY_LOCATION_EMPTY):
        servant_pos = self._lookup_servant_position(servant_id)
        assert 0 <= servant_pos < 3, 'Could not find servant in current team'
        assert len(self._selected_cmd_cards) < 3, 'Reached attack limitation (3 attacks per turn)'
        # 未出卡前指定敌方单体
        self._enter_attack_mode()
        self._select_enemy(enemy_location)
        # 点宝具（第一张卡选宝具的话会等更长的时间）
        self._submit_click_event(2 if len(self._selected_cmd_cards) == 0 else 0.5, (NP_XS[servant_pos], NP_Y))

    def noble_phantasm(self, servant_id: int, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        self._noble_phantasm(servant_id, enemy_location)
        self._selected_cmd_cards.append((self._noble_phantasm, (servant_id, enemy_location)))
        return self

    def support_noble_phantasm(self, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        return self.noble_phantasm(SERVANT_ID_SUPPORT, enemy_location)

    def _attack(self, command_card_index: int, enemy_location: int = ENEMY_LOCATION_EMPTY):
        assert len(self._selected_cmd_cards) < 3, 'Reached attack limitation (3 attacks per turn)'
        self._enter_attack_mode()
        self._select_enemy(enemy_location)
        # 选卡
        self._submit_click_event(1 if len(self._selected_cmd_cards) == 0 else 0.2,
                                 (COMMAND_CARD_XS[command_card_index], COMMAND_CARD_Y))

    def attack(self, command_card_index: int, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        self._attack(command_card_index, enemy_location)
        self._selected_cmd_cards.append((self._attack, (command_card_index, enemy_location)))
        return self

    def use_clothes_skill(self, skill_index: int, to_servant_id: Union[int, Tuple[int, int]] = SERVANT_ID_EMPTY,
                          enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'BattleSequenceExecutor':
        assert 0 <= skill_index < 3, 'invalid skill index'
        self._exit_attack_mode()
        self._select_enemy(enemy_location)
        # 搓按钮
        self._submit_click_event(1, (CLOTHES_BUTTON_X, CLOTHES_BUTTON_Y))
        self._submit_click_event(0.5, (CLOTHES_SKILL_XS[skill_index], CLOTHES_BUTTON_Y))
        # 选技能
        if isinstance(to_servant_id, int):
            servant_pos = self._lookup_servant_position(to_servant_id)
            assert servant_pos < 3, 'Could not use skill to backup member'
            self._submit_click_event(1, (TO_SERVANT_X[servant_pos], TO_SERVANT_Y))
        else:
            assert (isinstance(to_servant_id, tuple) or isinstance(to_servant_id, list)) and len(to_servant_id) == 2, \
                'invalid type or length of input servant tuple (used for changing servants)'
            servant_pos1 = self._lookup_servant_position(to_servant_id[0])
            servant_pos2 = self._lookup_servant_position(to_servant_id[1])
            assert servant_pos1 >= 0 and servant_pos2 >= 0, 'Could not find servant in current team'
            t = self._servants[servant_pos1]
            self._servants[servant_pos1] = self._servants[servant_pos2]
            self._servants[servant_pos2] = t
            # 选择第一个servant
            self._submit_click_event(1, (CHANGE_SERVANT_XS[servant_pos1], CHANGE_SERVANT_Y))
            # 选择第二个servant
            self._submit_click_event(0.2, (CHANGE_SERVANT_XS[servant_pos2], CHANGE_SERVANT_Y))
            # 点确定
            self._submit_click_event(0.2, (APPLY_CHANGE_SERVANT_BUTTON_X, APPLY_CHANGE_SERVANT_BUTTON_Y))
        self._submit_click_event(1, None)
        self._submit_click_event(TIME_WAIT_ATTACK_BUTTON, None)
        return self

    def _refresh_command_card_list(self, force: bool = False):
        # backward compatibility
        var = self.cfg.DO_NOT_MODIFY_BATTLE_VARS
        if force:
            should_detect_command_card = True
        elif self.cfg.detect_command_card is None:
            should_detect_command_card = self._controller.__require_battle_card_detection__(
                var['CURRENT_BATTLE'], var['MAX_BATTLE'], var['TURN'])
        else:
            should_detect_command_card = self.cfg.detect_command_card
        if should_detect_command_card:
            self._enter_attack_mode()
            sleep(0.5)
            img = self.attacher.get_screenshot(CV_SCREENSHOT_RESOLUTION_X, CV_SCREENSHOT_RESOLUTION_Y)
            new_cards = CommandCardDetector.detect_command_cards(img[..., :3])
            if self._dispatched_cards is None:
                self._dispatched_cards = new_cards
            else:
                self._dispatched_cards.clear()
                self._dispatched_cards.extend(new_cards)
        else:
            self._dispatched_cards = None

    def refresh_command_card_list(self):
        self._refresh_command_card_list(force=True)

    # noinspection PyMethodMayBeStatic, PyUnusedLocal,PyUnreachableCode
    def select_remain_command_card(self, priority: Optional[Sequence[CommandCard]] = None,
                                   avoid_chain_or_extra_atk: bool = True):
        raise NotImplementedError
        priority = priority or []
        if avoid_chain_or_extra_atk:
            pass
        else:
            pass
