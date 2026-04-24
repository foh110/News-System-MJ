"""
基于Streamlit实现的WEB文件上传服务

功能说明:
    1. 提供Web界面供用户上传TXT文件
    2. 读取文件内容并显示基本信息
    3. 将文件内容向量化存储到知识库中
    
安装依赖:
    pip install streamlit

Streamlit核心特性:
    - 当WEB页面元素发生变化(如上传文件)，整个脚本会重新执行一遍
    - 使用st.session_state来持久化保存状态，避免重复初始化
"""
import time

import streamlit as st
from knowledge_base import KnowledgeBaseService

# ========== 页面标题设置 ==========
# st.title() 设置页面主标题，显示在页面顶部
st.title("知识库更新服务")

# ========== 文件上传组件 ==========
# st.file_uploader() 创建文件上传控件
# 参数说明:
#   - label: 上传区域的提示文本
#   - type: 允许上传的文件类型列表
#   - accept_multiple_files: 是否允许多文件上传
uploader_file = st.file_uploader(
    label="请上传TXT文件",              # 上传区域的提示文字
    type=["txt"],                      # 只接受.txt文件
    accept_multiple_files=False        # False表示仅接受一个文件上传
)

# ========== Session State 状态管理 ==========
# Streamlit每次页面变化都会重新执行整个脚本
# 如果不做状态管理，KnowledgeBaseService会被重复创建，导致资源浪费
# 
# st.session_state 是一个类似字典的对象，用于跨脚本执行保存数据
# 原理：检查"service"键是否存在，不存在则创建，已存在则复用
if "service" not in st.session_state:
    # 首次运行时初始化知识库服务
    # KnowledgeBaseService内部会创建Chroma向量数据库连接
    st.session_state["service"] = KnowledgeBaseService()

# ========== 文件处理逻辑 ==========
# 当用户上传文件后，uploader_file不为None
# 此时可以读取文件内容并进行处理
if uploader_file is not None:
    
    # ---------- 步骤1: 提取文件元信息 ----------
    # uploader_file 是 UploadedFile 对象，包含文件的各种属性
    file_name = uploader_file.name       # 获取原始文件名
    file_type = uploader_file.type       # 获取MIME类型 (如 text/plain)
    file_size = uploader_file.size / 1024  # 文件大小(字节)转KB

    # ---------- 步骤2: 在页面上显示文件信息 ----------
    # st.subheader() 显示二级标题
    st.subheader(f"文件名：{file_name}")
    # st.write() 显示普通文本，支持Markdown格式
    # :.2f 表示保留2位小数
    st.write(f"文件格式：{file_type} | 大小：{file_size:.2f} KB")

    # ---------- 步骤3: 读取文件内容 ----------
    # getvalue() 读取文件内容为bytes字节流
    # decode("utf-8") 将字节流转为UTF-8编码的字符串
    text = uploader_file.getvalue().decode("utf-8")

    with st.spinner("载入知识库中..."):   # 在spinner内的代码执行过程，会有一个转圈动画
        time.sleep(1)
        result = st.session_state["service"].upload_by_str(text, file_name)

    # ---------- 步骤5: 显示处理结果 ----------
    # 判断返回结果，如果是None表示成功入库，如果是跳过提示则显示相应信息
    if result is None:
        # st.success() 显示绿色成功提示框
        st.success("✅ 成功，已成功加载到数据库中")
    else:
        # 显示跳过的提示信息（如"[跳过]内容已存在知识库中"）
        st.info(result)


