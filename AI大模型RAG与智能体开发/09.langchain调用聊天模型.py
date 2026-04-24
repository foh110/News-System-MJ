from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
#得到模型对象，qwen3-max就是聊天模型
model=ChatTongyi(model="qwen-max")

# 准备消息列表
message=[
    SystemMessage(content="你是一个边塞诗人"),
    HumanMessage(content="写一首情诗送给我的女朋友,以唐诗风格"),
    AIMessage(content="锄禾日当午，汗滴禾下土，谁之盘中餐，粒粒皆辛苦"),
    HumanMessage(content="按照你上一个回复的格式，再帮我写一首骂人的诗")
        ]

#调用stream流式执行
res=model.stream(input=message)

#for循环迭代打印输出，通过content来获取到内容
for chuck in res:
    print(chuck.content,end="",flush=True)

