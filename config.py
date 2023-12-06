import tomli
import os

# 把配置文件转化为类，目的是进行检查，提前报错
class Config:

    def __init__(self):
        # 用户配置文件不存在则使用当前目录的配置文件
        config_file = "~/.haxpot/config.toml"
        if not os.path.exists(config_file):
            config_file = "./config.toml"

        # 读取配置文件
        with open(config_file, "rb") as f:
            config = tomli.load(f)
        
        # 权限信息
        if config.get("authorization") is not None:
            table: dict = config["authorization"]
            self.shutdown: bool = False if table.get("shutdown") is None else table["shutdown"]
            self.full_auto: bool = False if table.get("full_auto") is None else table["full_auto"]
            self.invite: bool = False if table.get("invite") is None else table["invite"]
            self.kick: int = 0 if table.get("kick") is None else table["kick"]
        
        # 账户信息（必填）
        table: dict = config["account"]
        self.jid: str = table["jid"]
        self.password: str = table["password"]
        self.log_group: str = table["log_group"]
        self.nickname: str = "群机器人" if table.get("nickname") is None else table["nickname"]
        
        # 需要配置 ctrl_group
        self.need_ctrl = True if self.full_auto or self.invite or self.kick > 0 else False
        if self.need_ctrl:
            self.ctrl_group: str = config["account"]["ctrl_group"]

        # 控制信息
        if config.get("control") is not None:
            table: dict = config["control"]
            self.log_file: str = "./log.json" if table.get("log_file") is None else table["log_file"]
            self.log_content: str = "%(time)s: 用户“%(jid)s”第 %(num)s 次申请*%(ifpass)s*。本小时申请人次 \
                %(total)i/%(all)i。" if table.get("log_content") is None else table["log_content"]
        
        # 回复
        if config.get("reply") is not None:
            table: dict = config["reply"]
            self.prompt: str = "这里为自动审核测试平台，请不要开启加密，发送“开始”开始答题。" \
                if table.get("prompt") is None else table["prompt"]
            self.apply: str = "审核已开始，请在 %i 秒内完成回答，中途不要终止。请回答“对”或“错”（“是”或“否”）。" \
                if table.get("apply") is None else table["apply"]
            self.pass_: str = "恭喜您已通过自动审核，等待人工审核。" \
                if table.get("pass_") is None else table["pass_"]
            self.fail: str = "您的回答错误太多、超时或回答时间过短，很遗憾未通过审核。" \
                if table.get("fail") is None else table["fail"]
            self.prohibit: str = "您已被封禁，无法再次申请。" \
                if table.get("prohibit") is None else table["prohibit"]
            self.passed: str = "您已通过审核，请不要重复申请！" \
                if table.get("passed") is None else table["passed"]
            self.prohibited: str = "您已被封禁，无法再次申请！" \
                if table.get("prohibited") is None else table["prohibited"]
            self.exceeded: str = "同一时段申请人数过多，请 1 小时后再试。" \
                if table.get("exceeded") is None else table["exceeded"]
            self.too_short: str = "您两次申请之间的时间太短，请 %i 分钟后再试。" \
                if table.get("too_short") is None else table["too_short"]
            self.uninvited: str = "您未被邀请入群，无法申请！" \
                if table.get("uninvited") is None else table["uninvited"]
        
        # 题库信息
        table: dict = config["questions"]
        self.bank: str = table["bank"]
        self.total: int = table["total"]
        self.pass_score: int = table["pass_score"]
        self.max_seconds: int = table["max_seconds"]
        self.time_interval: int = table["time_interval"]
        self.max_per_hour: int = table["max_per_hour"]
        self.max_trial: int = table["max_trial"]