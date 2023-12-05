import json
import time
import numpy as np
import threading

# 一份问卷
class Questionaire:
    def __init__(self, data: list, config: dict):
        self.data = data
        # 状态，已经回答的、答对的
        self.total_num = 0
        self.passed_num = 0
        self.config = config
        # 计时，超时不通过
        self.in_time = True
        self.t = threading.Timer(self.config["max_seconds"], self.__clock)
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
        if not self.in_time:
            return False
        if self.passed_num < self.config["pass_num"]:
            return False
        return True
    
    # 计时器
    def __clock(self):
        self.in_time = False
    
    # 判断回答是否正确，给了多种回答选择
    def __judge(self, answer: str, real: bool):
        answer = answer.lstrip().rstrip() # 如果多打了空格，去掉
        if answer[-1] in (".", "。"):
            answer = answer[:-1]
        if real == True:
            if answer in ("是", "对", "正确", "没错", "是的", "对的", "正确的", "对了"):
                return True
            else:
                return False
        if answer in ("否", "错", "错误", "不对", "错的", "错误的", "错了"):
            return True
        return False

# 题库
class Bank:
    def __init__(self, config: dict):
        f = open(config["question_bank"], "r")
        self.data = json.loads(f.read())
        self.config = config
        f.close()
    
    # 随机选题生成问卷
    def new_naire(self):
        keys = list(self.data.keys())
        l = []
        for i in np.random.choice(keys, self.config["question_num"], replace=False):
            l.append([i, self.data[i]])
        return Questionaire(l, self.config)
