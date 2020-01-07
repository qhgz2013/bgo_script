# GLOBAL CONFIGURATION
import typing as _typing
import battle_action as _battle_action

MAX_AP = 141
EAT_APPLE_AP_THRESHOLD = 0
SUPPORT_SERVANT_ID = 150
SUPPORT_CRAFT_ESSENCE_ID = 330


# noinspection PyUnusedLocal
def apply_action(battle: int, turn: int, card_type: _typing.List[int], card_svt_id: _typing.List[int],
                 card_critical_rate: _typing.List[int], actions: _battle_action.FgoBattleAction):
    """
    比起V1的固定点击配置而言，V2采用的是回调式自动化，即每次发牌后都会调用该函数决定要怎么做
    ど-れ-に-し-よ-う-か-な
    ふふ、こういうこともできる
    :param battle: 当前第几面
    :param turn: 当前第几T
    :param card_type: 当前回合5张指令卡的卡色，1: Buster，2: Quick，3: Arts
    :param card_svt_id: 当前回合5张指令卡所属的从者ID
    :param card_critical_rate: 当前回合5张指令卡的暴击概率(0~100)，暂时未实现检测
    :param actions: 当前回合要怎么动（比如点什么技能出哪张卡，etc）
    :return: 无
    """
    # attack指定使用第`command_card_index`张（从0开始计数）指令卡攻击，
    # 可选参数enemy_location用于指定敌方第`enemy_location`个目标（从左开始，从0计数），若不指定目标，则为默认值-1
    # actions.attack(command_card_index, enemy_location=-1)

    # remove_servant用于某些没有良心的场合，需要我方退场的时候使用（比如大英雄宝具后退场，以及未来实装的陈宫等）
    # actions.remove_servant(servant_id)

    # use_skill用于使用从者的技能，`skill_index`指定需要使用的技能（从左数起，从0开始计数）
    # 若使用单体技能需要指定从者，则在to_servant_id填上对应的从者ID，对敌方单体使用技能时enemy_location作用同上
    # actions.use_skill(servant_id, skill_index, to_servant_id=-1, enemy_location=-1)
    raise NotImplementedError
