from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import PromptTemplate
from openai import OpenAI
# 1. 获取client对象，OpenAI类对象
client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-73ca16a84f75459f804ca9ea4fdb9624",
)
#创建所需要德解析器
str_paper=StrOutputParser()
json_paper=JsonOutputParser()

#模型创建
model=ChatTongyi(model="qwen3-max")
#第一个提示词模板
first_prompt=PromptTemplate.from_template(
    "我邻居姓：{lastname},刚生了{gender},请帮忙取个名字，"
    "并封装为Json格式返回给我。要求key是name，value是你起的名字，请严格遵守格式要求"
)

#第二个提示词模板
second_prompt=PromptTemplate.from_template(
    "姓名:{name},请帮我解析其含义"
)

#构建链

chain=first_prompt | model | json_paper|second_prompt|model|str_paper

for chunk in chain.stream({"lastname":"刘","gender":"女儿"}):
    print(chunk,end="",flush=True)