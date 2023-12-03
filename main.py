import json
import logging
import slixmpp

import log
import bank

class EchoBot(slixmpp.ClientXMPP):
    def __init__(self):
        # 读取配置文件
        f = open("config.json", "r")
        self.config = json.loads(f.read())
        f.close()
        self.log_data = log.Log(self.config)
        self.bank_data = bank.Bank(self.config)
        self.naires = {} # 正在进行的问卷
        # 账户、密码登陆
        slixmpp.ClientXMPP.__init__(self, self.config["jid"], self.config["password"])
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

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


if __name__ == '__main__':
    # Setup logging.
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    xmpp = EchoBot()
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()