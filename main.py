import logging
import sys
import os
import slixmpp
from slixmpp import stanza
from slixmpp import jid

import config
import log
import bank

class HaxpotBot(slixmpp.ClientXMPP):

    def __init__(self):
        self.config = config.Config()
        self.log_data = log.Log(self.config, self.println)
        self.bank_data = bank.Bank(self.config)
        self.naires:dict[str, bank.Questionaire] = {} # 正在进行的问卷

        # 账户、密码登陆
        slixmpp.ClientXMPP.__init__(self, self.config.jid, self.config.password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)

    async def start(self, event):
        """
        初始化，发送在线状态并获取好友列表，加入群聊
        :param event: 事件对象
        """
        self.send_presence()
        await self.get_roster()
        nick = self.config.nickname
        self.plugin['xep_0045'].join_muc(self.config.log_group, nick)
        self.plugin['xep_0045'].join_muc(self.config.ctrl_group, nick)

    # 用户申请消息
    def message(self, msg: stanza.Message):
        """处理用户申请消息"""
        if msg["type"] in ("normal", "chat"):
            jid_ = msg["from"].bare # 用户的 JID
            # 正在申请
            naire = self.naires.get(jid_)
            if naire is not None:
                reply = naire.question(msg["body"])
                # 未完成则继续提问
                if reply is not None:
                    msg.reply(reply).send()
                    return
                # 已经完成
                if not naire.finish():
                    msg.reply(self.log_data.failed(jid_)).send()
                    del self.naires[jid_]
                    return
                msg.reply(self.log_data.passed(jid_)).send()
                del self.naires[jid_] # 删除问卷（引用的）
                # 如果允许，则邀请进群
                if self.config.full_auto:
                    self.invite(jid_)
                return
            
            # 开始回答
            if msg["body"] == "开始":
                ok, reply = self.log_data.apply(jid_)
                if not ok:
                    msg.reply(reply).send()
                    return
                # 允许使用，新建问卷开始提问
                self.naires[jid_] = self.bank_data.new_naire()
                msg.reply(reply + "\n" + self.naires[jid_].question(None)).send()
                return
            
            if msg["body"] != "":
                msg.reply(self.config.prompt).send()
        
    # 群内指令
    def muc_message(self, msg: stanza.Message):
        nick = self.config.nickname
        # 如果消息是自己发出的
        if msg["mucnick"] == nick:
            return
        # 如果消息来自被控制群且要统计发言
        if msg["from"].bare == self.config.ctrl_group:
            whom = self.plugin['xep_0045'].get_jid_property(self.config.ctrl_group, msg["mucnick"], 'jid')
            whom = jid.JID(whom).bare
            if self.config.kick > 0:
               self.log_data.find_user(whom)
        # 如果消息与自己无关
        if not msg["body"].startswith(nick + ": "):
            return
        # 来自日志群
        if msg["from"].bare == self.config.log_group:
            command: str = msg["body"][len(nick)+2:]
            if command.startswith("解封"):
                jid_ = command[2:].strip()
                self.log_data.allow(jid_)
            elif command.startswith("封禁"):
                jid_ = command[2:].strip()
                self.log_data.prohibit(jid_)
            elif command.startswith("关机"):
                if self.config.shutdown:
                    self.shutdown()
                else:
                    self.println("本机器人没有权限关闭计算机！")
            elif command.startswith("检查沉默用户"):
                self.log_data.check_user()
            return
        # 没启用了邀请人制度就不管了
        if not self.config.invite:
            return
        # 消息来自被控制群
        if msg["from"].bare == self.config.ctrl_group:
            command: str = msg["body"][len(nick)+2:]
            if command.startswith("邀请"):
                jid_ = command[2:].strip()
                reply = self.log_data.invite(jid_, whom)
                self.send_message(self.config.ctrl_group, reply, mtype="groupchat")

    # 关机
    def shutdown(self):
        """断开连接并关机"""
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
        """发送消息到审核群"""
        self.send_message(self.config.log_group, msg, mtype="groupchat")
    
    # 邀请 JID 进群
    def invite(self, jid_: str):
        self.plugin['xep_0045'].invite(self.config.ctrl_group, jid_)

if __name__ == '__main__':
    # Setup logging.
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    xmpp = HaxpotBot()
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.register_plugin('xep_0045') # Multi-User Chat

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process(forever=False) # False 才能在 disconnect 后自动结束
