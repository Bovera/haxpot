# haxpot
A xmpp bot for automatically reviewing members

## 安装依赖
可以一个个安装
```
pip install tomli
pip install numpy
pip install slixmpp
```
也可以直接利用导出的环境安装
```
pip install -r requirements.txt
```

## 配置文件
配置文件目录为 `~/.haxpot/config.toml`（优先）及 `./config.toml`，参考示例 `config.toml`，使用时自行修改参数。参数说明如下。

**注意：参考配置文件仅供参考！并不包括所有选项。**

**[account] 账户信息**
|参数|可选性|含义|默认值|
|---|---|---|---|
|`jid`|**must**|账户 JID|
|`password`|**must**|账户密码|
|`log_group`|**must**|审核结果通知和机器人控制群|
|`ctrl_group`|optional|被机器人管理的群|
|`nickname`|optional|在这两个群中机器人的昵称|`"群机器人"`|

**[questions] 题库信息**
|参数|可选性|含义|
|---|---|---|
|`bank`|**must**|题库文件名称|
|`total`|**must**|每张问卷题目总数|
|`pass_score`|**must**|及格线，通过至少要答的题目数|
|`max_seconds`|**must**|限制回答秒数|
|`time_interval`|**must**|两次时间间隔（分钟）|
|`max_per_hour`|**must**|每小时允许的答题数量|
|`max_trial`|**must**|最大尝试次数|

**[reply] 与申请人的对话**
|参数|可选性|含义|
|---|---|---|
|`prompt`|optional|发送任意信息时的提醒|
|`apply`|optional|发送审核信号后的提醒|
|`pass_`|optional|通过后的回复|
|`fail`|optional|未通过的回复|
|`prohibit`|optional|封禁时的回复|
|`passed`|optional|通过后重复申请的回复|
|`prohibited`|optional|封禁后再次申请的回复|
|`exceeded`|optional|同一时段申请过多的回复|
|`too_short`|optional|两次申请时间过短的回复|
|`uninvited`|optional|未被邀请的回复|

**[control] 控制机器人**
|参数|可选性|含义|默认值|
|---|---|---|---|
|`log_file`|optional|日志文件|`log.json`|
|`log_content`|optional|输出的格式|

**[authorization] 权限**
|参数|可选性|含义|默认值|
|---|---|---|---|
|`shutdown`|optional|是否允许操控关机|`false`|
|`full_auto`|optional|是否允许在通过后给予成员权限|`false`|
|`invite`|optional|是否使用邀请人制度|`false`|
|`kick`|optional|定期清除不发言的人（单位天），0 不开启|`0`|