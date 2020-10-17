from enum import IntEnum
from typing import *
if TYPE_CHECKING:
    from fsm.battle_seq_executor import BattleSequenceExecutor


# 指令卡类型
class CommandCardType(IntEnum):
    Buster = 1
    Quick = 2
    Arts = 3


class EatAppleType(IntEnum):
    DontEatMyApple = 0
    SaintQuartz = 1  # 大概不会真有人用这个吧
    GoldApple = 2
    SilverApple = 3
    BronzeApple = 4


# 一般情况下的指令卡类
class CommandCard:
    __slots__ = ['svt_id', 'card_type']

    def __init__(self, svt_id: int, card_type: CommandCardType):
        self.svt_id = svt_id
        self.card_type = card_type

    def __repr__(self):
        return '<%s card for servant %d>' % (self.card_type.name, self.svt_id)


# 战斗中的指令卡发牌类（实际使用是这个）
class DispatchedCommandCard(CommandCard):
    __slots__ = ['svt_id', 'card_type', 'location', 'is_support', 'critical_rate']

    def __init__(self, svt_id: int, card_type: CommandCardType, location: int, is_support: bool,
                 critical_rate: int = 0):
        super().__init__(svt_id, card_type)
        self.location = location
        self.is_support = is_support
        self.critical_rate = critical_rate

    def __repr__(self):
        s = '<[%d] %s card for servant %d' % (self.location, self.card_type.name, self.svt_id)
        if self.is_support:
            s += ' (support)'
        if self.critical_rate > 0:
            s += ' (critical rate: %d%%)' % self.critical_rate
        return s + '>'


class BattleController:
    def __init__(self, battle_executor: 'BattleSequenceExecutor'):
        self.executor = battle_executor

    def __call__(self, current_battle: int, max_battle: int, turn: int,
                 dispatched_cards: Optional[Sequence[DispatchedCommandCard]]):
        raise NotImplementedError

    def __getattr__(self, item):
        return getattr(self.executor, item)


# 配队时使用的从者设置
# 注：自动配队未实现
class ServantConfiguration:
    __slots__ = ['svt_id', 'craft_essence_id']

    def __init__(self, svt_id: int, craft_essence_id: int):
        self.svt_id = svt_id
        self.craft_essence_id = craft_essence_id

    def __repr__(self):
        return '<ServantConfiguration for svt. %d and c.e. %d>' % (self.svt_id, self.craft_essence_id)


# 助战从者设置
# 注：技能等级检测未实现
class SupportServantConfiguration(ServantConfiguration):
    __slots__ = ['svt_id', 'craft_essence_id', 'craft_essence_max_break', 'friend_only', 'skill_requirement']

    def __init__(self, svt_id: int, craft_essence_id: int, craft_essence_max_break: bool = False,
                 friend_only: bool = False, skill_requirement: Optional[Sequence[int]] = None):
        super().__init__(svt_id, craft_essence_id)
        self.craft_essence_max_break = craft_essence_max_break
        self.friend_only = friend_only
        self.skill_requirement = skill_requirement

    def __repr__(self):
        s = '<SupportServantConfiguration for svt. %d and c.e. %d' % (self.svt_id, self.craft_essence_id)
        if self.craft_essence_max_break:
            s += ' (max break)'
        if self.friend_only:
            s += ' (friend only)'
        if self.skill_requirement:
            s += ' (skill: %s)' % str(self.skill_requirement)
        return s + '>'


# 出击队伍设置
class TeamConfiguration:
    def __init__(self, servants: Sequence[ServantConfiguration]):
        assert len(servants) == 6, 'Invalid team configuration, servants must be 6'
        self.servants = servants
        self.self_owned_servants = []  # type: List[ServantConfiguration]
        self.support_servant = None  # type: Optional[SupportServantConfiguration]
        self.support_location = None  # type: Optional[int]
        self._apply_servant_list()

    def _apply_servant_list(self):
        for i, svt in enumerate(self.servants):
            assert isinstance(svt, ServantConfiguration), \
                '%s is not a subclass of ServantConfiguration' % str(type(svt))
            if isinstance(svt, SupportServantConfiguration):
                if self.support_location is not None:
                    raise ValueError('Multiple support servant found, check your team configuration')
                self.support_location = i
                self.support_servant = svt
            else:
                self.self_owned_servants.append(svt)
        if self.support_location is None:
            raise ValueError('Could not find support servant in the team configuration')
