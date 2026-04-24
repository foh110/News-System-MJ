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
        {"role":"system","content":"你是一个AI助手，回答问题很简洁"},
        {"role": "user", "content": "小明有两条宠物狗"},
        {"role":"assistant","content":"好的"},
        {"role": "user", "content": "小明有两条宠物猫"},
        {"role":"assistant","content":"好的"},
        {"role": "user", "content": "小明有几条宠物"},
    ],
    stream=True    # 开启了流式输出的功能
)
# 3.处理结果
# print(response.choices[0].message.content)+
for chunk in response:
    print(
          chunk.choices[0].delta.content,
          end="",       #每一段之间以空格分隔
          flush=True)   #立刻刷新缓冲区