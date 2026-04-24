from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import CSVLoader

vector_store=InMemoryVectorStore (
    embedding=DashScopeEmbeddings()
)#指定使用哪个模型

loader = CSVLoader(
    file_path="./data/info.csv",#文件路径
    encoding="utf-8",           #编码语言
    source_column="source"  #指定本条数据数据来源是哪里
)

documents = loader.load()
#id1、id2、id3 ...
#向量存储的 新增 删除 检索
vector_store.add_documents(
    documents=documents,   #被添加的文件，类型：list[Document]
    ids=["id"+str(i) for i in range(1,len(documents)+1)]) #给添加的文件提供id（字符串） list[str]

#删除  传入 [id,id,id]
vector_store.delete("id1","id2")

#检索
result=vector_store.similarity_search(
    "python是不是简单易学啊",
    3
)
print(result)