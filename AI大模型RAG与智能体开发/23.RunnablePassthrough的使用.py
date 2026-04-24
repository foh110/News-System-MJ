# 提示词：用户的提问 + 向量库中检索到的参考资料

from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser

model = ChatTongyi(model="qwen3-max")
prompt = ChatPromptTemplate.from_messages(
    [
        ("system","以我提供的已知参考资料为主，简洁和专业的回答用户的问题，参考资料：{context}."),
        ("user","用户提问:{input}")
    ]
)
vector_store = InMemoryVectorStore(embedding=DashScopeEmbeddings(model="text-embedding-v4"))

#准备一下材料（向量库的数据）
#add_texts传入一个list[str]

vector_store.add_texts(["减肥就是要少吃多练","在减脂期间吃东西很重要，清淡少油控制卡路里摄入并运动起来","跑步是很好的运动哦"])

input_text="怎么减肥?"

#langchain中向量存储对象，有一个办法：as_retriever,可以返回可以Runnable接口的的子类实例对象

# 将向量存储转换为检索器，k=2表示检索时返回最相似的2个文档
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

#chain

chain={"input":RunnablePassthrough(),"context":retriever | format_func|prompt|model|StrOutputParser()}

"""
retriever:
    输入：用户问题    str
    输出：向量库的检索结果    list[Document]
prompt:
    输入：用户问题+向量库的检索结果    dict
    输出：完整的提示词    PromptValue
model:
    输入：提示词    

"""










