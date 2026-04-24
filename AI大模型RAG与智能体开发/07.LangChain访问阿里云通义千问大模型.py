# LangChain_community
from langchain_community.llms.tongyi import Tongyi

#不用qwen—3，因为qwen-3是聊天模型，qwen-max是大语言模型
model = Tongyi(model="qwen-max")

#调用invoke向模型提问
res=model.invoke(input="你是谁呀，你能做什么？")

print(res)