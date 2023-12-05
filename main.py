import json
import logging
import sys
import os
import slixmpp

import log
import bank

class EchoBot(slixmpp.ClientXMPP):
    def __init__(self):
        # 读取配置文件
        f = open("config.json", "r")
        self.config = json.loads(f.read())
        f.close()
        self.log_data = log.Log(self.config, self.println)
        self.bank_data = bank.Bank(self.config)
        self.naires = {} # 正在进行的问卷
        # 账户、密码登陆
        slixmpp.ClientXMPP.__init__(self, self.config["jid"], self.config["password"])
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        self.plugin['xep_0045'].join_muc(self.config["log_group"], self.config["group_nick"])

    # 用户申请消息
    def message(self, msg):
        if msg["type"] in ("normal", "chat"):
            jid = msg["from"].bare
            # 正在申请
            if self.naires.get(jid) != None:
                reply = self.naires[jid].question(msg["body"])
                # 已经完成
                if reply == None:
                    if self.naires[jid].finish():
                        msg.reply(self.log_data.passed(jid)).send()
                    else:
                        msg.reply(self.log_data.failed(jid)).send()
                    del self.naires[jid]
                    return
                # 未完成
                msg.reply(reply).send()
                return
            
            # 开始回答
            if msg["body"] == "开始":
                ok, reply = self.log_data.apply(jid)
                if not ok:
                    msg.reply(reply).send()
                    return
                # 允许使用，新建问卷开始提问
                self.naires[jid] = self.bank_data.new_naire()
                msg.reply(reply + "\n" + self.naires[jid].question(None)).send()
                return
            
            if msg["body"] != "":
                msg.reply(self.config["prompt"]).send()
        
    # 群内指令
    def muc_message(self, msg):
        nick = self.config["group_nick"]
        if msg["from"].bare == self.config["log_group"]:
            if msg["mucnick"] != nick and msg["body"].startswith(nick + ": "):
                command = msg["body"][len(nick)+2:]
                if command.startswith("解封"):
                    jid = command[2:].lstrip().rstrip()
                    self.log_data.allow(jid)
                elif command.startswith("封禁"):
                    jid = command[2:].lstrip().rstrip()
                    self.log_data.prohibit(jid)
                elif command.startswith("关机"):
                    if self.config["allow_shutdown"]:
                        self.shutdown()
                    else:
                        self.println("本机器人没有权限关闭计算机！")

    # 关机
    def shutdown(self):
        self.println("正在关机...")
        self.disconnect()
        # 根据操作系统判断关机指令
        if sys.platform == "linux":
            os.system("shutdown -h 1")
        elif sys.platform == "win32":
            os.system("shutdown -s -t 60")
        elif sys.platform == "darwin":
            os.system("shutdown -h +1")

    # 输出到审核群
    def println(self, msg: str):
        self.send_message(mto=self.config["log_group"], mbody=msg, mtype="groupchat")

if __name__ == '__main__':
    # Setup logging.
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    xmpp = EchoBot()
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.register_plugin('xep_0045') # Multi-User Chat

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process(forever=False) # False 才能在 disconnect 后自动结束