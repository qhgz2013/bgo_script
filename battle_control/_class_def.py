from enum import IntEnum
from typing import *
if TYPE_CHECKING:
    from fsm.battle_seq_executor import BattleSequenceExecutor
__all__ = ['CommandCard', 'CommandCardType', 'EatAppleType', 'DispatchedCommandCard', 'BattleController',
           'ServantConfiguration', 'SupportCraftEssenceConfiguration', 'SupportServantConfiguration',
           'TeamConfiguration', 'CommandCardNotFoundException']


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
        """
        DO NOT OVERLOAD __INIT__ METHOD OF BATTLE CONTROLLER! Use __initialize__ instead.
        :param battle_executor: executor instance
        """
        self.executor = battle_executor

    def __initialize__(self):
        """
        Order: __init__ -> __initialize__ -> turn(s) -> __finalize__, battle related flags or control variables can be
        set here

        :return: none
        """
        pass

    def __turn_initialize__(self, current_battle: int, max_battle: int, turn: int):
        """
        For each turn: __turn_initialize__ -> __call__ -> __turn_finalize__, turn-related flags or variables can be set
        here

        :param current_battle: current battle
        :param max_battle: max battle
        :param turn: current turn (turn will be reset to 1 if battle changes, accumulation is meaningless)
        :return: none
        """
        pass

    def __turn_finalize__(self, current_battle: int, max_battle: int, turn: int):
        """
        For each turn: __turn_initialize__ -> __call__ -> __turn_finalize__, post-turn actions is defined here

        :param current_battle: current battle
        :param max_battle: max battle
        :param turn: current turn (turn will be reset to 1 if battle changes, accumulation is meaningless)
        :return: none
        """
        pass

    def __finalize__(self):
        """
        Order: __init__ -> __initialize__ -> turn(s) -> __finalize__, post-battle related codes are here

        :return: none
        """
        pass

    def __call__(self, current_battle: int, max_battle: int, turn: int,
                 dispatched_cards: Optional[Sequence[DispatchedCommandCard]]):
        """
        For each turn: __turn_initialize__ -> __call__ -> __turn_finalize__, post-turn actions is defined here

        :param current_battle: current battle
        :param max_battle: max battle
        :param turn: current turn (turn will be reset to 1 if battle changes, accumulation is meaningless)
        :param dispatched_cards: list of dispatched command cards if enabled command card detection, or none otherwise
        :return: none
        """
        raise NotImplementedError

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def __require_battle_card_detection__(self, current_battle: int, max_battle: int, turn: int) -> bool:
        """
        This function will be called right after __turn_initialize__ to determine whether a battle card detection
        should be performed in current turn.

        NOTE FOR COMPATIBILITY: This functionality is disabled when "detect_command_card" field in global script
        configuration is set (no matter true or false), to enable it, please set detect_command_card=None.

        :param current_battle: current battle
        :param max_battle: max battle
        :param turn: current turn (turn will be reset to 1 if battle changes, accumulation is meaningless)
        :return: a flag telling whether the battle card should be detected, which is set to false by default
        """
        return False

    def __getattr__(self, item):
        # forwarding actions
        assert isinstance(item, str), 'Invalid call for __getattr__ in BattleController'
        if not item.startswith('_'):
            return getattr(self.executor, item)
        else:
            return object.__getattribute__(self, item)


# 配队时使用的从者设置
# 注：自动配队未实现
class ServantConfiguration:
    __slots__ = ['svt_id']

    def __init__(self, svt_id: int):
        self.svt_id = svt_id

    def __repr__(self):
        return f'<ServantConfiguration svt: {self.svt_id}>'


class SupportCraftEssenceConfiguration:
    __slots__ = ['id', 'max_break']

    def __init__(self, id_: int, max_break: bool = False):
        self.id = id_
        self.max_break = max_break

    def __repr__(self):
        return f'<SupportCraftEssenceConfiguration id: {self.id}, max_break: {self.max_break}'


# 助战从者设置
class SupportServantConfiguration(ServantConfiguration):
    __slots__ = ['svt_id', 'craft_essence_cfg', 'friend_only', 'skill_requirement']

    def __init__(self, svt_id: int, craft_essence_cfg: Union[SupportCraftEssenceConfiguration,
                                                             Sequence[SupportCraftEssenceConfiguration]],
                 friend_only: bool = False, skill_requirement: Optional[Sequence[int]] = None):
        super().__init__(svt_id)
        self.craft_essence_cfg = craft_essence_cfg
        if isinstance(self.craft_essence_cfg, SupportCraftEssenceConfiguration):
            self.craft_essence_cfg = [self.craft_essence_cfg]
        self.friend_only = friend_only
        self.skill_requirement = skill_requirement

    def __repr__(self):
        s = f'<SupportServantConfiguration svt: {self.svt_id} and {len(self.craft_essence_cfg)} c.e. config(s)'
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


class CommandCardNotFoundException(Exception):
    pass
