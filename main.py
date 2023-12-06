import logging
import sys
import os
import slixmpp
from slixmpp import stanza

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
            jid = msg["from"].bare # 用户的 JID
            # 正在申请
            naire = self.naires.get(jid)
            if naire is not None:
                reply = naire.question(msg["body"])
                # 未完成则继续提问
                if reply is not None:
                    msg.reply(reply).send()
                    return
                # 已经完成
                if not naire.finish():
                    msg.reply(self.log_data.failed(jid)).send()
                    del self.naires[jid]
                    return
                msg.reply(self.log_data.passed(jid)).send()
                del self.naires[jid] # 删除问卷（引用的）
                # 如果允许，则邀请进群
                if self.config.full_auto:
                    self.invite(jid)
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
                msg.reply(self.config.prompt).send()
        
    # 群内指令
    def muc_message(self, msg: stanza.Message):
        nick = self.config.nickname
        # 如果消息是自己发出的且与自己无关
        if msg["mucnick"] == nick or not msg["body"].startswith(nick + ": "):
            return
        # 来自日志群
        if msg["from"].bare == self.config.log_group:
            command: str = msg["body"][len(nick)+2:]
            if command.startswith("解封"):
                jid = command[2:].strip()
                self.log_data.allow(jid)
            elif command.startswith("封禁"):
                jid = command[2:].strip()
                self.log_data.prohibit(jid)
            elif command.startswith("关机"):
                if self.config.shutdown:
                    self.shutdown()
                else:
                    self.println("本机器人没有权限关闭计算机！")
            return
        # 没启用了邀请人制度就不管了
        if not self.config.invite:
            return
        # 消息来自被控制群
        if msg["from"].bare == self.config.ctrl_group:
            command: str = msg["body"][len(nick)+2:]
            if command.startswith("邀请"):
                jid = command[2:].strip()
                self.send_message(self.config.log_group, self.log_data.invite(jid), mtype="groupchat")

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
    def invite(self, jid: str):
        self.plugin['xep_0045'].invite(self.config.ctrl_group, jid)
        nick = self.plugin['xep_0045'].get_nick(self.config.ctrl_group, jid)
        self.plugin['xep_0045'].set_role(self.config.ctrl_group, nick, 'participant')

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
