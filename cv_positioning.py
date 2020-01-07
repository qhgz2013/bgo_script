# 自动战斗脚本中关于计算机视觉（CV）部分的参数
# 坐标X和Y归一化到[0, 1]，以便适用于不同大小的窗口

# 截图的缩放分辨率X和Y
CV_SCREENSHOT_RESOLUTION_X = 1280
CV_SCREENSHOT_RESOLUTION_Y = 720
# 任务列表两端的X坐标
CV_QUEST_LIST_X1 = 0.484
CV_QUEST_LIST_X2 = 0.961
# AP条的X、Y坐标
CV_AP_BAR_X1 = 0.148
CV_AP_BAR_X2 = 0.25
CV_AP_BAR_Y1 = 0.958
CV_AP_BAR_Y2 = 0.972
# 检查AP的阈值
CV_AP_GREEN_THRESHOLD = 100
# 跑狗的黑屏坐标
CV_FUFU_Y1 = 0.862
CV_FUFU_Y2 = 0.972
CV_FUFU_X1 = 0
CV_FUFU_X2 = 0.703
CV_FUFU_BLANK_THRESHOLD = 10
CV_FUFU_BLANK_RATIO_THRESHOLD = 0.995
# Attack按钮
CV_ATTACK_BUTTON_X1 = 0.8140625
CV_ATTACK_BUTTON_X2 = 0.95859375
CV_ATTACK_BUTTON_Y1 = 0.71527778
CV_ATTACK_BUTTON_Y2 = 0.97222223
CV_ATTACK_BUTTON_ANCHOR = 'cv_data/attack_button.png'
CV_ATTACK_DIFF_THRESHOLD = 0.1  # 0.075
# 助战的scrollbar
CV_SUPPORT_SCROLLBAR_X1 = 0.961
CV_SUPPORT_SCROLLBAR_X2 = 0.977
CV_SUPPORT_SCROLLBAR_Y1 = 0.25
CV_SUPPORT_SCROLLBAR_Y2 = 0.973
CV_SUPPORT_BAR_GRAY_THRESHOLD = 200

# 助战的检测
CV_SUPPORT_X1 = 0.5938
CV_SUPPORT_X2 = 0.6328
# 2阶段的助战定位阈值（基于饱和度）
CV_SUPPORT_S_STAGE1_LO = 0
CV_SUPPORT_S_STAGE1_HI = 50
CV_SUPPORT_S_STAGE2_LO = 70
CV_SUPPORT_S_STAGE2_HI = 95
CV_SUPPORT_STAGE1_LEN = 60  # 带签名的为 75，不带的大概是60
CV_SUPPORT_STAGE1_LEN2 = 75
CV_SUPPORT_STAGE2_LEN = 80

CV_SUPPORT_SERVANT_X1 = 0.0375
CV_SUPPORT_SERVANT_X2 = 0.1657

# 出本检测
CV_EXIT_QUEST_X1 = 0.043
CV_EXIT_QUEST_X2 = 0.9571
CV_EXIT_QUEST_Y1 = 0.2153
CV_EXIT_QUEST_Y2 = 0.757

CV_EXIT_QUEST_TITLE_MASK_X1 = 0.0171
CV_EXIT_QUEST_TITLE_MASK_X2 = 0.2095
CV_EXIT_QUEST_TITLE_MASK_Y1 = 0.0385
CV_EXIT_QUEST_TITLE_MASK_Y2 = 0.1283

CV_EXIT_QUEST_SERVANT_MASK_Y1 = 0.1924
CV_EXIT_QUEST_SERVANT_MASK_Y2 = 0.9359
CV_EXIT_QUEST_SERVANT_MASK_X1S = [0.0471, 0.2351, 0.4274, 0.6154, 0.8077]
CV_EXIT_QUEST_SERVANT_MASK_X2S = [0.1924, 0.3847, 0.5727, 0.765, 0.953]

CV_EXIT_QUEST_GRAY_THRESHOLD = 25
CV_EXIT_QUEST_GRAY_RATIO_THRESHOLD = 0.99

CV_FGO_DATABASE_FILE = 'cv_data/fgo_new.db'
CV_SUPPORT_EMPTY_FILE = 'cv_data/support_empty.png'
CV_SUPPORT_CRAFT_ESSENCE_FILE = 'cv_data/support_craft_essence_empty.png'

CV_BATTLE_DETECTION_X1 = 0.6718
CV_BATTLE_DETECTION_X2 = 0.7344
CV_BATTLE_DETECTION_Y1 = 0.0138
CV_BATTLE_DETECTION_Y2 = 0.0556
CV_BATTLE_DIGIT_DIRECTORY = 'cv_data/battle_digit'

CV_COMMAND_CARD_X1S = [0.0407, 0.24, 0.4391, 0.6399, 0.8438]
CV_COMMAND_CARD_X2S = [0.1602, 0.3594, 0.5586, 0.7601, 0.964]
CV_COMMAND_CARD_Y = 0.5556
CV_COMMAND_CARD_TOP_BORDER_H_LO = 28
CV_COMMAND_CARD_TOP_BORDER_H_HI = 35
CV_COMMAND_CARD_HEIGHT = 0.2778
