from AI大模型RAG与智能体开发.RAG项目案例.vector_stores import VectorStoreService

md5_path="./md5.text"


#Chroma
collection_name="rag"
persist_directory="./chroma_db"


#spliter
chunk_size=1000
chunk_overlap=0
separators=["。","；","：","！","？"," ","\n","\n\n",".","，","。","！","？"""]
max_split_char_number=1000  #文本分割的阈值

#
similarity_threshold=1  #检索返回匹配的文档数，建议3-5条以获取更全面的参考信息

embedding_model_name="text-embedding-v4"
chat_model_name="qwen3-max"