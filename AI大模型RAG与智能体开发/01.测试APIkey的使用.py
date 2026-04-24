from openai import OpenAI
import os

client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    api_key="sk-73ca16a84f75459f804ca9ea4fdb9624",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
#2.调用模型
response=client.chat.completions.create(
    model="qwen3-max",
    messages=[
        {"role":"system","content":"你是一个Python编程专家，并且不说废话简单回答"},
        {"role":"assistant","content":"好的，我是编程专家，简单且话不多，你要问什么"},
        {"role": "user", "content": "我想画一个3D爱心立体的"},
    ]
)
# 3.处理结果
print(response.choices[0].message.content)
