from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

#模型创建
model=ChatTongyi(model="qwen3-max")

#创建所需要德解析器
str_paper=StrOutputParser()
#第一个提示词模板
first_prompt=PromptTemplate.from_template(
    "我邻居姓：{lastname},刚生了{gender},请帮忙取个名字，仅告诉我名字，不要废话，给我5个名字"
)
#第二个提示词模板
second_prompt=PromptTemplate.from_template(
    "姓名:{name},请帮我解析其含义"
)
#函数的入参：AIMessage ->  dict ({"name":xxx})
my_func=RunnableLambda(lambda ai_msg:{"name":ai_msg.content})
#构建链
chain=first_prompt | model | my_func |second_prompt|model|str_paper
for chunk in chain.stream({"lastname":"刘","gender":"女儿"}):
    print(chunk,end="",flush=True)