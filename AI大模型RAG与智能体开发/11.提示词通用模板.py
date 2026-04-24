from langchain_core.prompts import PromptTemplate
from langchain_community.llms.tongyi import Tongyi

prompt_template= PromptTemplate.from_template(
    "我的邻居姓{lastname},刚生了一个{gender},你帮我起个名字，要有意义，并解释原因"
)
model = Tongyi(model="qwen-max")

chain=prompt_template | model
res=chain.invoke(input={"lastname":"刘","gender":"女儿"})
print(res)