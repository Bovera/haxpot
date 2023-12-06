import json
import numpy as np
import threading

import config

# 一份问卷
class Questionaire:
    def __init__(self, data: list, config: config.Config):
        self.data = data
        # 状态，已经回答的、答对的
        self.total_num = 0
        self.passed_num = 0
        self.config = config
        # 计时，超时不通过
        self.in_time = True
        self.t = threading.Timer(self.config.max_seconds, self.__clock)
        self.t.start()
    
    # 检查答案并返回下一题的问题（带题号），结束返回 None
    def question(self, answer):
        # 第一题
        if answer == None:
            return "1. " + self.data[0][0]
        # 不是第一题
        if self.__judge(answer, self.data[self.total_num][1]):
            self.passed_num += 1
        self.total_num += 1
        if self.total_num < len(self.data):
            return str(self.total_num+1) + ". " + self.data[self.total_num][0]
        return None
    
    # 完成后检查是否通过
    def finish(self):
        """检查是否通过审核"""
        if not self.in_time:
            return False
        if self.passed_num < self.config.pass_score:
            return False
        return True
    
    # 计时器
    def __clock(self):
        self.in_time = False
    
    # 判断回答是否正确，给了多种回答选择
    def __judge(self, answer: str, real: bool):
        """判断回复，转化成bool值。
        比如把“是”、“对”、“正确”等都转化成True，把“否”、“错”、“错误”等都转化成False
        """
        answer = answer.strip().rstrip(".").rstrip("。")  # 去除前后空格，句尾句号

        positive_responses = ("是", "对", "正确", "没错", "是的", "对的", "正确的", "对了")
        negative_responses = ("否", "错", "错误", "不对", "错的", "错误的", "错了")

        if real:
            return answer in positive_responses
        else:
            return answer in negative_responses

# 题库
class Bank:
    def __init__(self, config: config.Config):
        f = open(config.bank, "r")
        self.data = json.loads(f.read())
        self.config = config
        f.close()
    
    # 随机选题生成问卷
    def new_naire(self):
        keys = list(self.data.keys())
        l = []
        for i in np.random.choice(keys, self.config.total, replace = False):
            l.append([i, self.data[i]])
        return Questionaire(l, self.config)
