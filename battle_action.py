from typing import *
from click_positioning import *
from team_config import FgoTeamConfiguration

SERVANT_ID_SUPPORT = 0
SERVANT_ID_EMPTY = -1
ENEMY_LOCATION_EMPTY = -1
ID_SKILL = 1
ID_CLOTHES = 2
ID_COMMAND_CARD = 3
ID_NP = 4


class FgoBattleAction:
    def __init__(self, team_config: FgoTeamConfiguration):
        self.skill_sequence = []
        self.attack_sequence = []
        self.team_config = team_config
        self.servants = list(self.team_config.team_servant_id)
        self.servants.insert(self.team_config.support_position, SERVANT_ID_SUPPORT)
        self.reset()

    def reset(self):
        self.skill_sequence = []
        self.attack_sequence = []

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
        self.skill_sequence.append((ID_SKILL, (servant_pos, skill_index, to_servant_pos, enemy_location)))
        return self

    def use_support_skill(self, skill_index: int, to_servant_id: int = SERVANT_ID_EMPTY,
                          enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        return self.use_skill(SERVANT_ID_SUPPORT, skill_index, to_servant_id, enemy_location)

    def noble_phantasm(self, servant_id: int, enemy_location: int = ENEMY_LOCATION_EMPTY) \
            -> 'FgoBattleAction':
        servant_pos = self._lookup_servant_position(servant_id)
        assert 0 <= servant_pos < 3, 'Could not find servant in current team'
        assert len(self.attack_sequence) < 3, 'Reached attack limitation (3 attacks per turn)'
        self.attack_sequence.append((ID_NP, (servant_pos, enemy_location)))
        return self

    def support_noble_phantasm(self, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        return self.noble_phantasm(SERVANT_ID_SUPPORT, enemy_location)

    def attack(self, command_card_index: int, enemy_location: int = ENEMY_LOCATION_EMPTY) -> 'FgoBattleAction':
        assert len(self.attack_sequence) < 3, 'Reached attack limitation (3 attacks per turn)'
        self.attack_sequence.append((ID_COMMAND_CARD, (command_card_index, enemy_location)))
        return self

    def use_clothes_skill(self, skill_index: int, to_servant_id: Union[int, Tuple[int, int]] = SERVANT_ID_EMPTY) \
            -> 'FgoBattleAction':
        assert 0 <= skill_index < 3, 'invalid skill index'
        if type(to_servant_id) == int:
            servant_pos = self._lookup_servant_position(to_servant_id)
            assert servant_pos < 3, 'Could not use skill to backup member'
            self.skill_sequence.append((ID_CLOTHES, (skill_index, servant_pos)))
        else:
            assert (type(to_servant_id) == tuple or type(to_servant_id) == list) \
                   and len(to_servant_id) == 2, \
                   'invalid type or length of input servant tuple (used for changing servants)'
            servant_pos1 = self._lookup_servant_position(to_servant_id[0])
            servant_pos2 = self._lookup_servant_position(to_servant_id[1])
            assert servant_pos1 >= 0 and servant_pos2 >= 0, 'Could not find servant in current team'
            self.skill_sequence.append((ID_CLOTHES, (skill_index, (servant_pos1, servant_pos2))))
            t = self.servants[servant_pos1]
            self.servants[servant_pos1] = self.servants[servant_pos2]
            self.servants[servant_pos2] = t
        return self

    def get_click_actions(self) -> List[Tuple[float, Union[None, Tuple[float, float]]]]:
        # 返回一个list，该list由多个tuple组成，代表当前turn的所有点击事件，每个tuple则只包含一个点击事件
        # tuple的格式如下：(与上一个事件的时间差t，坐标)
        # 需要点击时，则坐标为(点击的坐标x，点击的坐标y)，都是归一化到[0, 1]表示的，不需要（纯粹为了等时间的话）则为None
        # 时间差一般都是大于0或等于-1的，等于-1则需要等到右下角的Attack可以按为止
        click_seq = []
        # 生成点击序列，BUFF first
        for action_id, action_data in self.skill_sequence:
            if action_id == ID_SKILL:
                # 技能
                servant_pos, skill_index, to_servant_pos, enemy_pos = action_data
                # 使用需要选中敌方目标的技能前，先选敌方目标
                if enemy_pos != ENEMY_LOCATION_EMPTY:
                    click_seq.append((1, (ENEMY_XS[enemy_pos], ENEMY_Y)))
                # 点击技能
                click_seq.append((0.5, (SKILL_XS[servant_pos * 3 + skill_index], SKILL_Y)))
                # first_skill = False
                # 若是我方单体技能，则选定我方一个目标
                if to_servant_pos != SERVANT_ID_EMPTY:
                    click_seq.append((0.5, (TO_SERVANT_X[to_servant_pos], TO_SERVANT_Y)))
                click_seq.append((1, None))
            elif action_id == ID_CLOTHES:
                # master技能
                skill_index, servant_pos = action_data
                # 搓按钮
                click_seq.append((1, (CLOTHES_BUTTON_X, CLOTHES_BUTTON_Y)))
                # 选技能
                click_seq.append((0.5, (CLOTHES_SKILL_XS[skill_index], CLOTHES_BUTTON_Y)))
                if type(servant_pos) == tuple:
                    # 特殊的换人情况，需要选择两个servant
                    servant_pos1, servant_pos2 = servant_pos
                    # 选择第一个servant
                    click_seq.append((1, (CHANGE_SERVANT_XS[servant_pos1], CHANGE_SERVANT_Y)))
                    # 选择第二个servant
                    click_seq.append((0.2, (CHANGE_SERVANT_XS[servant_pos2], CHANGE_SERVANT_Y)))
                    # 点确定
                    click_seq.append((0.2, (APPLY_CHANGE_SERVANT_BUTTON_X, APPLY_CHANGE_SERVANT_BUTTON_Y)))
                elif servant_pos != SERVANT_ID_EMPTY:
                    # 普通的单体技能
                    click_seq.append((1, (TO_SERVANT_X[servant_pos], TO_SERVANT_Y)))
                click_seq.append((1, None))
            elif action_id == ID_NP or action_id == ID_COMMAND_CARD:
                # BUFF阶段忽略所有指令卡出卡
                continue
            else:
                raise ValueError('program error, invalid action_id')
            click_seq.append((-1, None))
        # 加了所有BUFF之后再出卡
        click_seq.append((1 if len(self.skill_sequence) > 0 else 2, (ATTACK_BUTTON_X, ATTACK_BUTTON_Y)))
        # 如果是第一张卡就是宝具卡的话，需要更长一点的等待时间
        # 而且选择卡之后无法更换要攻击的敌方目标
        selected_cards = 0
        if len(self.attack_sequence) != 3:
            raise ValueError('Invalid turn sequence: command card selection should be equal to 3')
        for action_id, action_data in self.attack_sequence:
            if action_id == ID_NP:
                # 宝具卡
                servant_pos, enemy_pos = action_data
                # 未出卡前指定敌方单体
                if selected_cards == 0 and enemy_pos != ENEMY_LOCATION_EMPTY:
                    click_seq.append((0.5, (ENEMY_XS[enemy_pos], ENEMY_Y)))
                # 点宝具（第一张卡选宝具的话会等更长的时间）
                click_seq.append((2 if selected_cards == 0 else 0.5, (NP_XS[servant_pos], NP_Y)))
                selected_cards += 1
            elif action_id == ID_COMMAND_CARD:
                # 普通平A卡
                card_index, enemy_pos = action_data
                # 未出卡前指定敌方单体
                if selected_cards == 0 and enemy_pos != ENEMY_LOCATION_EMPTY:
                    click_seq.append((0.5, (ENEMY_XS[enemy_pos], ENEMY_Y)))
                # 选卡
                click_seq.append((0.2, (COMMAND_CARD_XS[card_index], COMMAND_CARD_Y)))
                selected_cards += 1
            else:
                continue
        return click_seq
