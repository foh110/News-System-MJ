"""
知识库服务模块
功能：将文本数据进行向量化存储到Chroma向量数据库中，支持MD5去重
"""
from datetime import datetime
import hashlib
import os

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config_data as config

def check_md5(md5_str):
    """
    检查传入的md5字符串是否已经被处理过
    
    参数:
        md5_str: 待检查的MD5哈希值字符串
    
    返回值:
        False: MD5未处理过，是新内容
        True: 已经处理过，是重复内容
    
    实现逻辑:
        1. 检查MD5记录文件是否存在，不存在则创建空文件
        2. 逐行读取记录文件，比对是否存在相同的MD5值
    """
    if not os.path.exists(config.md5_path):
        # MD5记录文件不存在，创建一个空文件
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        # 读取MD5记录文件，逐行比对
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()  # 去除行首行尾的空白字符
            if line == md5_str:
                return True  # 找到匹配，说明已处理过
    return False  # 遍历完未找到匹配，说明未处理过


def save_md5(md5_str):
    """
    将传入的md5字符串追加写入到记录文件中
    
    参数:
        md5_str: 需要保存的MD5哈希值字符串
    
    实现逻辑:
        以追加模式('a')打开文件，将MD5值写入并换行
        每个MD5值占一行，便于后续逐行读取比对
    """
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')

def get_string_md5(input_str: str, encoding='utf-8'):
    """
    将传入的字符串转换为MD5哈希值
    
    参数:
        input_str: 需要计算MD5的原始字符串
        encoding: 字符串编码方式，默认UTF-8
    
    返回值:
        32位十六进制的MD5哈希字符串
    
    实现步骤:
        1. 将字符串编码为字节数组(bytes)
        2. 创建MD5哈希对象
        3. 更新哈希对象(填入数据)
        4. 获取十六进制哈希值
    
    用途:
        通过MD5唯一标识文本内容，用于去重判断
    """
    # 步骤1: 将字符串转换为bytes字节数组，MD5算法处理的是字节序列
    str_bytes = input_str.encode(encoding=encoding)
    
    # 步骤2: 创建MD5哈希对象
    md5_obj = hashlib.md5()
    
    # 步骤3: 将字节数据填充到MD5对象中
    md5_obj.update(str_bytes)
    
    # 步骤4: 获取16进制格式的MD5哈希值(32位字符)
    md5_hex = md5_obj.hexdigest()
    
    return md5_hex

class KnowledgeBaseService(object):
    """
    知识库服务类
    
    功能:
        1. 管理Chroma向量数据库的连接
        2. 将文本数据向量化并存储
        3. 支持长文本自动分割
    
    核心组件:
        - Chroma: 向量数据库，存储文本向量
        - DashScopeEmbeddings: 阿里云嵌入模型，将文本转为向量
        - RecursiveCharacterTextSplitter: 文本分割器，处理长文本
    """
    
    def __init__(self):
        """
        初始化知识库服务
        
        初始化内容:
            1. 创建向量数据库存储目录
            2. 初始化Chroma向量数据库连接
            3. 初始化文本分割器
        """
        # 创建本地向量数据库的文件夹
        # exist_ok=True 表示如果文件夹已存在则不报错
        os.makedirs(config.persist_directory, exist_ok=True)

        # 初始化Chroma向量数据库
        # 向量数据库的作用：存储文本的向量表示，支持相似度检索
        self.chroma = Chroma(
            collection_name=config.collection_name,      # 集合名称(类似数据库表名)
            embedding_function=DashScopeEmbeddings(       # 嵌入函数：将文本转为向量
                model="text-embedding-v4"                 # 使用阿里云text-embedding-v4模型
            ),
            persist_directory=config.persist_directory,   # 数据持久化存储路径
        )

        # 初始化文本分割器
        # 作用：将长文本分割成多个小片段，便于向量化处理
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,          # 每个文本片段的最大字符数
            chunk_overlap=config.chunk_overlap,    # 相邻片段之间的重叠字符数(保持上下文连贯)
            separators=config.separators,          # 分隔符优先级，按段落、句子等自然边界分割
            length_function=len,                   # 长度计算函数，使用Python内置len()
        )


    def upload_by_str(self, data, filename):
        """
        将字符串内容向量化后存入知识库
        
        参数:
            data: 要存储的文本内容字符串
            filename: 文本来源文件名，用于元数据记录
        
        返回值:
            None 或 "[跳过]内容已存在知识库中"
        
        处理流程:
            1. 计算文本MD5，检查是否已存在(去重)
            2. 如果文本过长，分割成多个片段
            3. 为每个片段创建元数据(来源、时间、操作者)
            4. 调用向量数据库存储文本和元数据
            5. 记录MD5防止重复存储
        """
        # ========== 步骤1: 计算MD5并去重检查 ==========
        md5_hex = get_string_md5(data)
        
        # 检查该内容是否已存在知识库中
        if check_md5(md5_hex):
            return "[跳过]内容已存在知识库中"

        # ========== 步骤2: 文本分割处理 ==========
        # 如果文本长度超过阈值，需要分割成多个片段
        # 原因：嵌入模型有输入长度限制，且小片段检索更精准
        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]  # 短文本直接作为单片段

        # ========== 步骤3: 构建元数据 ==========
        # 元数据：附加信息，便于后续检索时了解数据来源
        metadata = {
            "source": filename,                                      # 文件来源
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 入库时间
            "operator": "小毛",                                      # 操作者
        }

        # ========== 步骤4: 存入向量数据库 ==========
        # add_texts 方法会自动:
        #   1. 调用embedding_function将文本转为向量
        #   2. 存储向量到Chroma数据库
        #   3. 关联元数据便于后续过滤查询
        self.chroma.add_texts(
            texts=knowledge_chunks,                      # 文本片段列表
            metadatas=[metadata for _ in knowledge_chunks],  # 每个片段都附加相同元数据
        )

        # ========== 步骤5: 记录MD5完成去重 ==========
        save_md5(md5_hex)




if __name__ == '__main__':
    save_md5("7a8941058aaf4df5147042ce104568da")
    print(check_md5("7a8941058aaf4df5147042ce104568da"))




        # r1=get_string_md5("周杰伦")
        # r2=get_string_md5("周杰伦的歌曲")
        # r3=get_string_md5("周杰伦的歌曲")

        # print(r1)
        # print(r2)
        # print(r3)

