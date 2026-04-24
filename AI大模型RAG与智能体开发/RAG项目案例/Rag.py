"""
RAG (Retrieval-Augmented Generation) 检索增强生成服务

核心流程：
    1. 接收用户问题
    2. 从向量数据库检索相关文档
    3. 将检索结果作为上下文，结合用户问题构建提示词
    4. 调用大语言模型生成回答

LangChain Runnable 管道说明：
    - RunnablePassthrough: 透传输入数据
    - retriever: 向量检索器，返回相关文档
    - format_document: 格式化文档内容为字符串
    - ChatPromptTemplate: 构建对话提示词模板
    - ChatTongyi: 通义千问大模型
    - StrOutputParser: 解析模型输出为字符串
"""

# ========== 导入依赖模块 ==========
# DashScopeEmbeddings: 阿里云DashScope嵌入模型，将文本转为向量
from langchain_community.embeddings import DashScopeEmbeddings

# Document: LangChain文档对象，包含内容和元数据
from langchain_core.documents import Document

# StrOutputParser: 将模型输出解析为字符串
from langchain_core.output_parsers import StrOutputParser

# ChatPromptValue: 提示词值对象（此行导入未实际使用，可删除）
from langchain_core.prompt_values import ChatPromptValue

# ChatPromptTemplate: 对话提示词模板，format_document用于格式化文档（此行format_document未使用）
from langchain_core.prompts import ChatPromptTemplate, format_document

# ChatTongyi: 阿里云通义千问聊天模型
from langchain_community.chat_models.tongyi import ChatTongyi

# RunnablePassthrough: 可运行对象，用于透传数据
from langchain_core.runnables import RunnablePassthrough

# VectorStoreService: 自定义向量存储服务类
from vector_stores import VectorStoreService

# config_data: 配置文件，包含模型名称、阈值等参数
import config_data as config


def print_prompt(prompt):
    """
    调试函数：打印最终生成的提示词内容
    
    参数:
        prompt: ChatPromptValue对象，包含完整的提示词信息
    
    返回值:
        原封不动返回prompt，便于在管道中链式调用
    
    作用:
        在控制台输出分隔线和提示词内容，方便调试查看
    """
    print("=" * 20)
    print(prompt.to_string())  # 将提示词转为字符串打印
    print("=" * 20)
    return prompt  # 必须返回，否则管道中断


class RagService(object):
    """
    RAG服务类
    
    功能:
        封装完整的RAG流程，包括向量检索、提示词构建、模型调用
    
    核心组件:
        - vector_service: 向量存储服务，负责文档检索
        - prompt_template: 提示词模板，定义系统指令和用户输入格式
        - chat_model: 大语言模型，生成最终回答
        - chain: 组合后的执行链，一键调用完成全流程
    """
    
    def __init__(self):
        """
        初始化RAG服务
        
        初始化步骤:
            1. 创建向量存储服务（连接Chroma数据库）
            2. 定义提示词模板（系统角色 + 用户输入）
            3. 初始化大语言模型（通义千问）
            4. 构建执行链（组合所有组件）
        """
        
        # ========== 步骤1: 初始化向量存储服务 ==========
        # VectorStoreService封装了Chroma向量数据库的连接
        # DashScopeEmbeddings将文本转为向量，用于相似度检索
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )
        # 注意：第22行有一个多余的逗号，会导致self.vector_service变成元组
        # 应该删除逗号

        # ========== 步骤2: 定义提示词模板 ==========
        # ChatPromptTemplate.from_messages 从消息列表创建模板
        # 消息格式：(角色, 内容)
        #   - system: 系统角色，定义AI的行为准则和背景知识
        #   - user: 用户角色，包含用户的问题
        # {context} 和 {input} 是占位符，运行时会被替换为实际值
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system", 
                    "以我提供的已知参考资料为主，简洁并专业的回答用户问题。参考资料:{context}。"
                ),
                ("user", "请回答用户问题：{input}")
            ]
        )

        # ========== 步骤3: 初始化大语言模型 ==========
        # ChatTongyi是阿里云通义千问的LangChain封装
        # model参数指定使用的模型版本，从配置文件读取
        self.chat_model = ChatTongyi(model=config.chat_model_name)

        # ========== 步骤4: 构建执行链 ==========
        # __get_chain() 方法组合所有组件形成处理管道
        self.chain = self.__get_chain()


    def __get_chain(self):
        """
        构建并返回最终的LangChain执行链
        
        执行链结构（数据流向）：
            用户输入 
                ↓
            {input: 透传, context: 检索结果} 
                ↓
            prompt_template (填充提示词)
                ↓
            print_prompt (调试打印)
                ↓
            chat_model (大模型生成)
                ↓
            StrOutputParser (解析为字符串)
                ↓
            最终回答
        
        返回值:
            chain: 可调用对象，支持 chain.invoke("问题") 方式使用
        """
        
        # 从向量服务获取检索器
        # retriever是一个可调用对象，输入查询字符串，返回相关文档列表
        retriever = self.vector_service.get_retriever()

        # 定义文档格式化函数
        # 作用：将检索到的Document对象列表转为格式化的字符串，用于填充提示词
        def format_document(docs: list[Document]):
            """
            将文档列表格式化为字符串
            
            参数:
                docs: Document对象列表，每个包含page_content和metadata
            
            返回值:
                格式化后的字符串，包含所有文档的内容和元数据
            """
            if not docs:
                # 如果没有检索到相关文档，返回提示信息
                return "无相关参考资料"
            
            formatted_str = ""
            for doc in docs:
                # 拼接每个文档的内容和元数据
                formatted_str += f"文档片段：{doc.page_content}\n"
                formatted_str += f"文档元数据：{doc.metadata}\n\n"
            return formatted_str

        # 构建执行链（LangChain表达式语言 LCEL）
        # 使用 | 操作符连接各个组件，数据从左向右流动
        chain = (
            {
                # RunnablePassthrough() 透传用户输入，不做任何修改
                # 结果赋值给 "input" 键，供后续模板使用
                "input": RunnablePassthrough(),
                
                # retriever | format_document 是嵌套管道：
                #   1. retriever接收用户输入，检索相关文档
                #   2. format_document将文档列表转为字符串
                # 注意：这里只写函数名，不加括号，由管道自动调用
                # 结果赋值给 "context" 键，作为参考资料
                "context": retriever | format_document
            } 
            # 以上字典会被传递给prompt_template，填充{input}和{context}占位符
            | self.prompt_template    # 生成完整提示词
            | print_prompt            # 调试：打印提示词内容
            | self.chat_model         # 调用大模型生成回答
            | StrOutputParser()       # 解析模型输出为纯字符串
        )

        return chain


if __name__ == '__main__':
    """
    主程序入口：测试RAG服务
    
    使用方式:
        python Rag.py
    
    流程:
        1. 创建RagService实例（自动初始化所有组件）
        2. 调用chain.invoke()传入用户问题
        3. 打印模型返回的回答
    """
    # 创建RAG服务实例
    rag_service = RagService()
    
    # 调用执行链，传入用户问题
    # invoke() 方法会依次执行：检索 → 格式化 → 构建提示词 → 调用模型 → 解析输出
    res = rag_service.chain.invoke("我体重180斤，尺码推荐")
    
    # 打印最终回答
    print(res)