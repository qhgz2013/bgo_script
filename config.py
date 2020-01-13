# GLOBAL CONFIGURATION
import typing as _typing
import battle_action as _battle_action
import team_config as _team_config

# 当前等级的最大AP，用于自动恰苹果
MAX_AP = 141
# 低于该AP时自动恰金苹果，目前只实现了恰金苹果，后面不排除实装恰其他苹果
EAT_APPLE_AP_THRESHOLD = 0
# 默认的配队信息
DEFAULT_TEAM_CONFIGURATION = _team_config.FgoTeamConfiguration(
    # 队伍的从者ID（除去助战）
    team_servant_id=[215, 183, 37, 106, 219],
    # 队伍的礼装ID（除去助战），用于自动配队，目前未实现
    team_craft_essence_id=[],
    # 助战在队伍中的位置，从左开始，从0计数
    support_position=3,
    # 助战从者ID，用于自动检测好友助战
    support_servant_id=215,
    # 助战礼装ID，用于自动检测好友助战，若不指定礼装则为0
    support_craft_essence_id=924,
    # 助战技能最低需求，未实现
    support_skill_requirement=None,
    # 助战礼装是否需要满破
    support_craft_essence_max_break=True,
    # 是否只选择好友助战，未实现
    friend_only=False,
)


# noinspection PyUnusedLocal
def apply_action(battle: int, turn: int, card_type: _typing.List[int], card_svt_id: _typing.List[int],
                 card_critical_rate: _typing.List[int], team_config: _team_config.FgoTeamConfiguration,
                 actions: _battle_action.FgoBattleAction):
    """
    每次发牌后都会调用该函数决定要怎么做
    比起V1 (提交tag: v0.1.0 prealpha)的固定点击配置而言，V2采用的是回调式自动化，提供比V1更灵活的选卡使用技能的方式
    ど-れ-に-し-よ-う-か-な
    ふふ、こういうこともできる
    :param battle: 当前第几面
    :param turn: 当前第几T（简单起见，该数值在换面的时候重置为1，不进行累计）
    :param card_type: 当前回合5张指令卡的卡色，1: Buster，2: Quick，3: Arts
    :param card_svt_id: 当前回合5张指令卡所属的从者ID
    :param card_critical_rate: 当前回合5张指令卡的暴击概率(0~100)，暂时未实现检测
    :param team_config: 当前的队伍配置
    :param actions: 当前回合要怎么动（比如点什么技能出哪张卡，etc）
    :return: 无
    """
    import numpy as np
    # attack指定使用第i张指令卡攻击（i为下面参数的command_card_index，从0开始计数），
    # 可选参数enemy_location用于指定敌方第j个目标（j为enemy_location参数，从左到右顺序，从0计数），若不指定目标，则为默认值-1
    # actions.attack(command_card_index, enemy_location=-1)

    # remove_servant用于某些没有良心的场合，需要我方退场的时候使用（比如大英雄宝具后退场，以及未来实装的陈宫等）
    # actions.remove_servant(servant_id)
    # remove_support_servant同理，用于移除助战从者
    # actions.remove_support_servant()

    # use_skill用于使用从者的技能，`skill_index`指定需要使用的技能（从左数起，从0开始计数）
    # 若使用单体技能需要指定从者，则在to_servant_id填上对应的从者ID，对敌方单体使用技能时enemy_location作用同上
    # actions.use_skill(servant_id, skill_index, to_servant_id=-1, enemy_location=-1)
    # use_support_skill同理，用于助战从者使用技能
    # actions.use_support_skill(skill_index, to_servant_id=-1, enemy_location=-1)

    # noble_phantasm用于使用宝具卡，servant_id指定是哪位从者的宝具，若是单体宝具需要指定地方位置，则通过enemy_location指定，
    # 效果同上
    # actions.noble_phantasm(servant_id, enemy_location=-1)
    # support_noble_phantasm同理
    # actions.support_noble_phantasm(enemy_location=-1)

    # use_clothes_skill为使用衣服技能，skill_index为使用哪一个衣服技能（从左数起，从0开始计数）
    # actions.use_clothes_skill(skill_index, to_servant_id=-1)
    # 特别地，对于换人操作，to_servant_id需要传入一个tuple: (a, b)，a和b分别是两个从者的ID，若需要对支援从者进行换人，
    # 则其中一个ID填0
    # 下面的例子展示了助战和自带的孔明间的换人操作
    # actions.use_clothes_skill(skill_index=2, to_servant_id=(0, 37))
    # 换人后若需要更新当前发牌，使用：
    # actions.refresh_command_card_list()

    # 注意：请遵循实际操作中先技能后攻击的顺序

    # SAMPLE: WCBA + 大英雄 (满破虚数) + 狂兰 (50 NP) + 极地服

    used = np.zeros(5, 'uint8')

    def _select_servant_card(remain_card_cnt, select_svt_id, select_card_type, v, target=-1):
        for i in range(5):
            if remain_card_cnt == 0:
                break
            if (select_svt_id is None or card_svt_id[i] == select_svt_id) and \
                    card_type[i] == select_card_type and v[i] == 0:
                actions.attack(i, enemy_location=target)
                remain_card_cnt -= 1
                v[i] = 1
        return remain_card_cnt

    # def _select_other_card(remain_card_cnt, v):
    #     score_dict = {1: 1, 2: 3, 3: 2}
    #     card_score = [score_dict[x] for x in card_type]
    #     order = np.argsort(card_score)
    #     for i in order:
    #         if remain_card_cnt == 0:
    #             break
    #         if v[i] == 0:
    #             actions.attack(i)
    #             remain_card_cnt -= 1
    #             v[i] = 1
    #     return remain_card_cnt

    if battle == 1:
        # 孔明
        actions.use_skill(37, 1).use_skill(37, 2).use_skill(37, 0, to_servant_id=183)
        # 换人cba
        actions.use_clothes_skill(2, (0, 37))
        actions.refresh_command_card_list()
        # wcba魔放
        actions.use_skill(215, 0, to_servant_id=183).use_support_skill(0, to_servant_id=183)
        actions.use_skill(183, 0)
        # cba/雪山樱红卡打头
        if _select_servant_card(1, 215, 1, used, target=0) == 0 or _select_servant_card(1, 183, 1, used, target=0) == 0:
            actions.noble_phantasm(183)
            # 补一张没用过的攻击
            for card in range(5):
                if not used[card]:
                    actions.attack(card)
                    break
        else:
            # 无cba/雪山樱红卡，优先选雪山樱绿卡->cba蓝卡->雪山樱蓝卡->cba绿卡
            remain = _select_servant_card(2, 183, 2, used, target=0)
            remain = _select_servant_card(remain, 215, 3, used, target=0)
            remain = _select_servant_card(remain, 183, 3, used, target=0)
            remain = _select_servant_card(remain, 215, 2, used, target=0)
            actions.noble_phantasm(183)
    elif battle == 2:
        actions.use_skill(215, 2, to_servant_id=183)
        actions.noble_phantasm(183).attack(0).attack(1)
    else:
        actions.use_skill(215, 1).use_support_skill(1).use_support_skill(2, to_servant_id=183)
        actions.use_clothes_skill(0)
        actions.use_skill(183, 1).use_skill(183, 2, to_servant_id=183)
        actions.noble_phantasm(183).attack(0).attack(1)
