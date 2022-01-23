# 自动战斗脚本中关于计算机视觉（CV）部分的参数

# 截图的缩放分辨率X和Y
CV_SCREENSHOT_RESOLUTION_X = 1280
CV_SCREENSHOT_RESOLUTION_Y = 720
# 任务列表两端的X坐标
# CV_QUEST_LIST_X1 = 620
# CV_QUEST_LIST_X2 = 1230
# AP条的X、Y坐标
CV_AP_BAR_X1 = 190
CV_AP_BAR_X2 = 320
CV_AP_BAR_Y1 = 690
CV_AP_BAR_Y2 = 695
# 检查AP的阈值
CV_AP_GREEN_THRESHOLD = 100
# 跑狗的黑屏坐标
CV_FUFU_Y1 = 625
CV_FUFU_Y2 = 700
CV_FUFU_X1 = 0
CV_FUFU_X2 = 900
CV_FUFU_BLANK_THRESHOLD = 195  # original: 45, 195 is used to detect support
CV_FUFU_BLANK_RATIO_THRESHOLD = 0.995
# Attack按钮
CV_ATTACK_BUTTON_X1 = 1042
CV_ATTACK_BUTTON_X2 = 1227
CV_ATTACK_BUTTON_Y1 = 515
CV_ATTACK_BUTTON_Y2 = 700
CV_ATTACK_BUTTON_ANCHOR = 'cv_data/attack_button.png'
CV_ATTACK_DIFF_THRESHOLD = 10
# 助战的scrollbar
CV_SUPPORT_SCROLLBAR_X1 = 1245
CV_SUPPORT_SCROLLBAR_X2 = 1265
CV_SUPPORT_SCROLLBAR_Y1 = 180
CV_SUPPORT_SCROLLBAR_Y2 = 700
CV_SUPPORT_BAR_GRAY_THRESHOLD = 200

# 助战界面的垂直位置检测
CV_SUPPORT_DETECT_X1 = 300
CV_SUPPORT_DETECT_X2 = 1000
CV_SUPPORT_DETECT_DIFF_THRESHOLD = 80
CV_SUPPORT_TD_PIXEL = 2
CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_LO = 176
CV_SUPPORT_DETECT_Y_LEN_THRESHOLD_HI = 181
# 助战从者框的水平位置（垂直位置通过上面的参数给出）
CV_SUPPORT_SERVANT_X1 = 48
CV_SUPPORT_SERVANT_X2 = 212
# 助战从者框部分resize的大小（对齐数据库图像）
CV_SUPPORT_SERVANT_IMG_SIZE = (144, 132)
# 助战从者与礼装分割位置
CV_SUPPORT_SERVANT_SPLIT_Y = 107
# 助战识别
CV_FGO_DATABASE_FILE = 'cv_data/fgo_new.db'
CV_SUPPORT_EMPTY_FILE = 'cv_data/support_empty.png'
CV_SUPPORT_CRAFT_ESSENCE_FILE = 'cv_data/support_craft_essence_empty.png'
CV_SUPPORT_CRAFT_ESSENCE_FILE2 = 'cv_data/support_craft_essence_empty2.png'
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_FILE = 'cv_data/max_break.png'
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_THRESHOLD = 1.8
# 助战礼装满破图标位置
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y1 = -24
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_Y2 = -4
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X1 = 134
CV_SUPPORT_CRAFT_ESSENCE_MAX_BREAK_X2 = 154
# 助战好友识别
CV_SUPPORT_FRIEND_DISCRETE_THRESHOLD = 200
CV_SUPPORT_FRIEND_DETECT_X1 = 360
CV_SUPPORT_FRIEND_DETECT_X2 = 600
CV_SUPPORT_FRIEND_DETECT_Y1 = 130
CV_SUPPORT_FRIEND_DETECT_Y2 = 155
CV_SUPPORT_FRIEND_DETECT_THRESHOLD = 5 / 255
# 助战技能框位置
CV_SUPPORT_SKILL_BOX_SIZE = 55  # 宽高=55px
CV_SUPPORT_SKILL_BOX_MARGIN_X = 23  # 两个技能框间的margin像素
CV_SUPPORT_SKILL_BOX_OFFSET_Y = 115  # 技能框从检测到的助战Y1开始往下偏移的像素
CV_SUPPORT_SKILL_BOX_OFFSET_X1 = 837
CV_SUPPORT_SKILL_BOX_OFFSET_X1S = [
    CV_SUPPORT_SKILL_BOX_OFFSET_X1,
    CV_SUPPORT_SKILL_BOX_OFFSET_X1+(CV_SUPPORT_SKILL_BOX_SIZE+CV_SUPPORT_SKILL_BOX_MARGIN_X),
    CV_SUPPORT_SKILL_BOX_OFFSET_X1+(CV_SUPPORT_SKILL_BOX_SIZE+CV_SUPPORT_SKILL_BOX_MARGIN_X)*2]
CV_SUPPORT_SKILL_BOX_OFFSET_X2S = [x+CV_SUPPORT_SKILL_BOX_SIZE for x in CV_SUPPORT_SKILL_BOX_OFFSET_X1S]
CV_SUPPORT_SKILL_BOX_OFFSET_X2 = CV_SUPPORT_SKILL_BOX_OFFSET_X2S[-1]
CV_SUPPORT_SKILL_V_DIFF_THRESHOLD = 30  # original: 40
CV_SUPPORT_SKILL_V_DIFF_STEP_SIZE = 2
CV_SUPPORT_SKILL_V_DIFF_EDGE_SIZE = 3
CV_SUPPORT_SKILL_BINARIZATION_THRESHOLD = 80 / 255  # original 85 / 255, found it's higher
CV_SUPPORT_SKILL_DIGIT_DIR = 'cv_data/support_skill_digit'

# 出本检测
CV_EXIT_QUEST_X1 = 55
CV_EXIT_QUEST_X2 = 1225
CV_EXIT_QUEST_Y1 = 155
CV_EXIT_QUEST_Y2 = 545

# TODO [PRIOR: nice-to-have]: 改成alpha mask
CV_EXIT_QUEST_TITLE_MASK_X1 = 0.0171
CV_EXIT_QUEST_TITLE_MASK_X2 = 0.2095
CV_EXIT_QUEST_TITLE_MASK_Y1 = 0.0385
CV_EXIT_QUEST_TITLE_MASK_Y2 = 0.1283

CV_EXIT_QUEST_SERVANT_MASK_Y1 = 0.1924
CV_EXIT_QUEST_SERVANT_MASK_Y2 = 0.9359
CV_EXIT_QUEST_SERVANT_MASK_X1S = [0.0471, 0.2351, 0.4274, 0.6154, 0.8077]
CV_EXIT_QUEST_SERVANT_MASK_X2S = [0.1924, 0.3847, 0.5727, 0.765, 0.953]

CV_EXIT_QUEST_GRAY_THRESHOLD = 25  # 该值最好在1.5.4 free本进行测试
CV_EXIT_QUEST_GRAY_RATIO_THRESHOLD = 0.98  # origin: 0.99 (lower bound found: 0.989)
CV_IN_BATTLE_BLANK_SCREEN_THRESHOLD = 30
CV_IN_BATTLE_BLANK_SCREEN_RATIO = 0.75  # 该值最好在1.5.4 free本进行测试


# 战斗场次识别
CV_BATTLE_DETECTION_X1 = 860
CV_BATTLE_DETECTION_X2 = 940
CV_BATTLE_DETECTION_Y1 = 10
CV_BATTLE_DETECTION_Y2 = 40
CV_BATTLE_DIGIT_DIRECTORY = 'cv_data/battle_digit'
CV_BATTLE_FILTER_PIXEL_THRESHOLD = 40
CV_BATTLE_DIGIT_THRESHOLD = 140

# 指令卡识别
# 5张卡的X坐标
CV_COMMAND_CARD_X1S = [51, 307, 562, 820, 1080]
CV_COMMAND_CARD_X2S = [204, 460, 715, 973, 1233]
# 指令卡的Y坐标（由于Y是浮动的，所以这里给出的是大概的最小值）
CV_COMMAND_CARD_Y = 400
# 计算浮动坐标的参数
CV_COMMAND_CARD_Y_DETECTION_OFFSET = 75
CV_COMMAND_CARD_Y_DETECTION_LENGTH = 30
CV_COMMAND_CARD_HEIGHT = 200
# BQA，对应RGB顺序
CV_COMMAND_CARD_TYPE_FILES = ['cv_data/buster_anchor.png', 'cv_data/quick_anchor.png', 'cv_data/arts_anchor.png']
CV_COMMAND_CARD_TYPE_OFFSET = [90, 90, 77]
CV_COMMAND_CARD_MASK = ['cv_data/buster_cmd_card_mask3.png', 'cv_data/quick_cmd_card_mask2.png',
                        'cv_data/arts_cmd_card_mask3.png']
# 指令卡框扩大的范围
CV_COMMAND_CARD_EXTEND_TOP = 25
CV_COMMAND_CARD_EXTEND_BOTTOM = 12
CV_COMMAND_CARD_EXTEND_LEFT = 42
CV_COMMAND_CARD_EXTEND_RIGHT = 42
CV_COMMAND_CARD_IMG_SIZE = (256, 256)
# 助战指令卡标志（相对每张指令卡的坐标）
CV_COMMAND_CARD_SUPPORT_Y1 = 29
CV_COMMAND_CARD_SUPPORT_Y2 = 54
CV_COMMAND_CARD_SUPPORT_X1 = 130
CV_COMMAND_CARD_SUPPORT_X2 = 220
CV_COMMAND_CARD_SUPPORT_ANCHOR_FILE = 'cv_data/command_card_support_anchor.png'
# CV_COMMAND_CARD_SUPPORT_HSV_THRESHOLD = 8  # < 12!
CV_COMMAND_CARD_SUPPORT_GRAY_THRESHOLD = 35

CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y1 = 540
CV_SUPPORT_REFRESH_REFUSED_DETECTION_Y2 = 580
CV_SUPPORT_REFRESH_REFUSED_DETECTION_X1 = 550
CV_SUPPORT_REFRESH_REFUSED_DETECTION_X2 = 750
CV_SUPPORT_REFRESH_REFUSED_DETECTION_S_THRESHOLD = 5

CV_REQUEST_SUPPORT_UI_FILE = 'cv_data/request_support_ui.png'
CV_EAT_APPLE_UI_FILE = 'cv_data/eat_apple_ui.png'
CV_CONTINUOUS_BATTLE_UI_FILE = 'cv_data/continuous_battle.png'

CV_ENABLE_SUPPORT_CRAFT_ESSENCE_CACHE = True
CV_SUPPORT_CRAFT_ESSENCE_CACHE_FILE_PATH = 'cv_data/support_craft_essence_cache.pkl'
