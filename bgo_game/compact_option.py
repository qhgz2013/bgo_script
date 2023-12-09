class CompactOption:
    def __init__(self, class_score: bool = False) -> None:
        # 是否启用职介天赋树--会影响助战检测的技能box位置
        self.class_score = class_score
