import datetime
import time
import json
import threading

# 记录
class Log:
    # 从 log_file 读取内容
    def __init__(self, config: dict):
        f = open(config["log_file"], "r")
        self.data = json.loads(f.read())
        self.config = config
        f.close()
        # 计时，每一个小时重置
        self.t = threading.Thread(target=self.__reset)
        self.t.start()
    
    # 答题未通过时调用
    def failed(self, jid: str):
        reply = self.config["fail_reply"] # 未通过回复
        self.data[jid]["answering_num"] += 1
        # 超过最大答题次数
        if self.data[jid]["answering_num"] >= self.config["max_trial"]:
            self.data[jid]["prohibited"] = True
            reply += self.config["prohibit_reply"] # 封禁回复
        self.data[jid]["last_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.__write()
        return reply
    
    # 答题通过时调用
    def passed(self, jid: str):
        self.data[jid]["answering_num"] += 1
        self.data[jid]["last_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data[jid]["passed"] = True
        self.__write()
        return self.config["pass_reply"] # 通过回复
    
    # 有人申请就调用
    def apply(self, jid: str):
        # 检测是否申请过多
        if self.applied >= self.config["max_per_hour"]:
            return False, self.config["exceeded_reply"]
        data = self.data.get(jid)
        # 不存在就新建地址后返回
        if data == None:
            self.data[jid] = {
              "last_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "answering_num": 0,
              "prohibited": False,
              "passed": False
            }
            self.applied += 1
            return True, self.config["apply_reply"]
        # 检测是否已经通过或者封禁
        if self.data[jid]["passed"]:
            return False, self.config["passed_reply"]
        if self.data[jid]["prohibited"]:
            return False, self.config["prohibited_reply"]
        # 检测两次时间是否过短
        wait_time = datetime.timedelta(minutes = self.config["time_interval"])
        last_time = datetime.datetime.strptime(self.data[jid]["last_time"], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() < last_time + wait_time:
            return False, self.config["too_short_reply"]
        
        self.applied += 1
        return True, self.config["apply_reply"]
    
    # 将内容重新写回文件，每次修改后会自动进行
    def __write(self):
        f = open(self.config["log_file"], "w")
        data = json.dumps(self.data, indent=2)
        f.write(data)
        f.close()
    
    # 一个小时重置为 0
    def __reset(self):
        while True:
            self.applied = 0
            time.sleep(3600)