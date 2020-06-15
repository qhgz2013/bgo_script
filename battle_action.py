from typing import *
from click_positioning import *
from team_config import FgoTeamConfiguration
from logging import root

SERVANT_ID_SUPPORT = 0
SERVANT_ID_EMPTY = -1
ENEMY_LOCATION_EMPTY = -1
# ID_SKILL = 1
# ID_CLOTHES = 2
# ID_COMMAND_CARD = 3
# ID_NP = 4


# TODO：重写该模块，实现实时调用实时操作
class FgoBattleAction:
    def __init__(self, team_config: FgoTeamConfiguration,
                 apply_battle_action_callback: Callable[[List[Tuple[float, Union[None, Tuple[float, float]]]]], None],
                 card_changed_callback: Optional[Callable[[], None]] = None):
        self.team_config = team_config
        self.servants = list(self.team_config.team_servant_id)
        self.servants.insert(self.team_config.support_position, SERVANT_ID_SUPPORT)
        self.reset()
        self.card_changed_callback = card_changed_callback
        self.apply_battle_action_callback = apply_battle_action_callback
        self.is_use_skill_state = True
        self.selected_cards = 0

    def reset(self):
        self.is_use_skill_state = True
        self.selected_cards = 0

    def _lookup_servant_position(self, servant_id: int) -> int:
        if servant_id != SERVANT_ID_EMPTY:
            for i, team_servant_id in enumerate(self.servants):
                if team_servant_id == servant_id:
                    return i
        return -1

    def remove_servant(self, servant_id: int) -> 'FgoBattleAction':
        # removes the servant like some kind of archer, which dead after NP
        # for SUPPORT SERVANT, refers to SERVANT_ID_SUPPORT (= 0)
        servant_pos = self._lookup_servant_position(servant_id)
        assert servant_pos >= 0, 'Could not find servant in current team'
        if len(self.servants) <= 3:
            self.servants.remove(servant_id)
        else:
            self.servants[servant_pos] = self.servants[3]
            self.servants = self.servants[:3] + self.servants[4:]
        return self

    def remove_support_servant(self) -> 'FgoBattleAction':
        return self.remove_servant(SERVANT_ID_SUPPORT)

    def use_skill(self, servant_id: int, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
                  enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        servant_pos = self._lookup_servant_position(servant_id)
        assert 0 <= servant_pos < 3, 'Could not find servant in current team'
        to_servant_pos = self._lookup_servant_position(to_servant_id)
        assert to_servant_pos < 3, 'Could not use skill to backup member'
        click_seq = []
        if enemy_location != ENEMY_LOCATION_EMPTY:
            click_seq.append((1, (ENEMY_XS[enemy_location], ENEMY_Y)))
        # 点击技能
        click_seq.append((0.5, (SKILL_XS[servant_pos * 3 + skill_index], SKILL_Y)))
        # 若是我方单体技能，则选定我方一个目标
        if to_servant_pos != SERVANT_ID_EMPTY:
            click_seq.append((0.5, (TO_SERVANT_X[to_servant_pos], TO_SERVANT_Y)))
        click_seq.append((1, None))
        click_seq.append((-1, None))
        self.apply_battle_action_callback(click_seq)
        return self

    def use_support_skill(self, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
                          enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        return self.use_skill(SERVANT_ID_SUPPORT, skill_index, to_servant_id, enemy_location)

    def noble_phantasm(self, servant_id: int, enemy_location: int = ENEMY_LOCATION_EMPTY) \
            -> 'FgoBattleAction':
        servant_pos = self._lookup_servant_position(servant_id)
        assert 0 <= servant_pos < 3, 'Could not find servant in current team'
        assert self.selected_cards < 3, 'Reached attack limitation (3 attacks per turn)'
        # 未出卡前指定敌方单体
        click_seq = []
        if self.is_use_skill_state:
            self.is_use_skill_state = False
            click_seq.append((0.5, (ATTACK_BUTTON_X, ATTACK_BUTTON_Y)))
        if self.selected_cards == 0 and enemy_location != ENEMY_LOCATION_EMPTY:
            click_seq.append((0.5, (ENEMY_XS[enemy_location], ENEMY_Y)))
        # 点宝具（第一张卡选宝具的话会等更长的时间）
        click_seq.append((2 if self.selected_cards == 0 else 0.5, (NP_XS[servant_pos], NP_Y)))
        self.selected_cards += 1
        self.apply_battle_action_callback(click_seq)
        return self

    def support_noble_phantasm(self, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        return self.noble_phantasm(SERVANT_ID_SUPPORT, enemy_location)

    def attack(self, command_card_index: int, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        assert self.selected_cards < 3, 'Reached attack limitation (3 attacks per turn)'
        click_seq = []
        if self.is_use_skill_state:
            self.is_use_skill_state = False
            click_seq.append((0.5, (ATTACK_BUTTON_X, ATTACK_BUTTON_Y)))
        if self.selected_cards == 0 and enemy_location != ENEMY_LOCATION_EMPTY:
            click_seq.append((0.5, (ENEMY_XS[enemy_location], ENEMY_Y)))
        # 选卡
        click_seq.append((1 if self.selected_cards == 0 else 0.2,
                          (COMMAND_CARD_XS[command_card_index], COMMAND_CARD_Y)))
        self.selected_cards += 1
        self.apply_battle_action_callback(click_seq)
        return self

    def use_clothes_skill(self, skill_index: int, to_servant_id: Union[int, Tuple[int, int]] = SERVANT_ID_EMPTY,
                          enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        assert 0 <= skill_index < 3, 'invalid skill index'
        # 搓按钮
        click_seq = []
        if enemy_location != ENEMY_LOCATION_EMPTY:
            click_seq.append((0.5, (ENEMY_XS[enemy_location], ENEMY_Y)))
        click_seq.append((1, (CLOTHES_BUTTON_X, CLOTHES_BUTTON_Y)))
        click_seq.append((0.5, (CLOTHES_SKILL_XS[skill_index], CLOTHES_BUTTON_Y)))
        # 选技能
        if type(to_servant_id) == int:
            servant_pos = self._lookup_servant_position(to_servant_id)
            assert servant_pos < 3, 'Could not use skill to backup member'
            click_seq.append((1, (TO_SERVANT_X[servant_pos], TO_SERVANT_Y)))
        else:
            assert (type(to_servant_id) == tuple or type(to_servant_id) == list) \
                   and len(to_servant_id) == 2, \
                   'invalid type or length of input servant tuple (used for changing servants)'
            servant_pos1 = self._lookup_servant_position(to_servant_id[0])
            servant_pos2 = self._lookup_servant_position(to_servant_id[1])
            assert servant_pos1 >= 0 and servant_pos2 >= 0, 'Could not find servant in current team'
            t = self.servants[servant_pos1]
            self.servants[servant_pos1] = self.servants[servant_pos2]
            self.servants[servant_pos2] = t
            # 选择第一个servant
            click_seq.append((1, (CHANGE_SERVANT_XS[servant_pos1], CHANGE_SERVANT_Y)))
            # 选择第二个servant
            click_seq.append((0.2, (CHANGE_SERVANT_XS[servant_pos2], CHANGE_SERVANT_Y)))
            # 点确定
            click_seq.append((0.2, (APPLY_CHANGE_SERVANT_BUTTON_X, APPLY_CHANGE_SERVANT_BUTTON_Y)))
        click_seq.append((1, None))
        click_seq.append((-1, None))
        self.apply_battle_action_callback(click_seq)
        return self

    def refresh_command_card_list(self):
        if self.card_changed_callback is None:
            root.warning('No card_changed_callback set in FgoBattleAction, refresh command card action will be ignored')
        else:
            try:
                self.card_changed_callback()
            except Exception as ex:
                root.warning('Detected exception while calling card_changed_callback, result maybe incorrect',
                             exc_info=ex)
