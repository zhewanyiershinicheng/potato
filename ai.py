from nonebot import on_command, on_message,get_driver
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message, Event
from nonebot.rule import Rule
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg, EventMessage
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from nonebot_plugin_session import Session, SessionLevel
from nonebot.params import CommandStart,CommandArg
from typing import Dict
import json
import aiohttp
import asyncio
"""单轮"""

generate=on_command("ai",priority=10,block=True)
generate0=on_command("super",priority=10,block=True)
@generate0.handle()
async def _(bot:Bot,event:Event,state:T_State,comm:str=CommandStart(),raw:Message=CommandArg()):
    text=raw.extract_plain_text()
    if text == "":
        await generate0.finish("不允许发送空内容")
    payload={
        "model": "glm-4.5-flash",
        "stream": False,
        "message": text,
        "thinking": {
            "type": "enabled"
        },
        "do_sample": True,
        "temperature": 0.6,
        "top_p": 0.95,
        "response_format": {
            "type": "text"
        },
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url="https://open.bigmodel.cn/api/paas/v4/async/chat/completions",
                headers={"Authorization":"Bearer 86de7ae9bfbe4154932af405bd409762.ERmE9iAJRpdDtx8h","Content-Type": "application/json"},
                data=json.dumps(payload)
        ) as response:
            result = await response.json()
            task_id = result.get("id")
            if task_id=="None":
                await generate0.finish("printf('gg');")
            max_attempts = 40  # 最大轮询次数
            interval = 2  # 轮询间隔(秒)
            attempts = 0
            while attempts < max_attempts:
                # 调用查询接口
                async with session.get(
                        url=f"https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}",
                        headers={"Authorization": "Bearer 86de7ae9bfbe4154932af405bd409762.ERmE9iAJRpdDtx8h"}
                ) as responses:
                    results = await responses.json()
                    status = results.get("task_status")
                    if status == "SUCCESS":
                        # 假设完成后结果在result字段中
                        ai_message = results.get("choices", [{}])[0].get("message", {})
                        ai_content = ai_message.get("content", "未获取到有效响应")
                        await generate0.finish(ai_content)
                    elif status == "PROCESSING":
                        # 处理中，继续轮询
                        attempts += 1
                        if attempts < max_attempts:
                            await asyncio.sleep(interval)
                    else:
                        await generate0.finish("bug?")
            await generate0.finish("超时")

@generate.handle()
async def _(bot:Bot,event:Event,state:T_State,comm:str=CommandStart(),raw:Message=CommandArg()):
    text=raw.extract_plain_text()
    if text == "":
        await generate.finish("不允许发送空内容")
    payload={
        "model":"gemma3:1b",
        "prompt":text,
        "stream":False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url="http://127.0.0.1:11434/api/generate",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
        ) as response:
            result = await response.json()
            ai_response = result.get("response")
            await generate.finish(ai_response)

"""多轮"""
import os

STORAGE_FILE = "chat_sessions.json"

# 初始化存储文件（若不存在则创建空字典）
if not os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# 读取会话数据（按用户ID获取）
async def get_session_data(user_id: str) -> Dict:
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    # 返回该用户的数据，无则返回默认值
    return all_data.get(user_id, {"in_chat": False, "chat_history": []})

# 写入会话数据（按用户ID更新）
async def set_session_data(user_id: str, data: Dict):
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    all_data[user_id] = data
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

# 删除会话数据（用户退出时）
async def delete_session_data(user_id: str):
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    if user_id in all_data:
        del all_data[user_id]
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


chat = on_command("chat", priority=1, block=True)

def in_chat() -> Rule:
    async def _in_chat(event: Event) -> bool:
        user_id = event.get_user_id()
        session_data = await get_session_data(user_id)
        return session_data["in_chat"] is True
    return Rule(_in_chat)

listener = on_message(priority=2, rule=in_chat(), block=True)

@chat.handle()
async def handle_chat_start(bot: Bot, event: Event):
    user_id = event.get_user_id()
    init_data = {
        "in_chat": True,
        "chat_history": []
    }
    await set_session_data(user_id, init_data)
    await chat.send("已进入对话，输入q退出（退出后会话将被销毁）")

@listener.handle()
async def handle_continuous_chat(bot: Bot, event: Event):
    user_id = event.get_user_id()
    user_input = event.get_plaintext()

    if user_input.lower() == "q":
        await delete_session_data(user_id)
        await listener.finish("已退出对话，会话已销毁")

    # 正常对话：读取历史→调用Ollama→更新记录
    session_data = await get_session_data(user_id)
    chat_history = session_data["chat_history"]  # 获取历史记录

    # 追加用户消息
    chat_history.append({"role": "user", "content": user_input})

    try:
        # 调用Ollama获取回复
        ai_response = await call_ollama_with_history(chat_history)
        # 追加AI回复
        chat_history.append({"role": "assistant", "content": ai_response})
        # 更新会话数据（保存新的历史记录）
        await set_session_data(user_id, {
            "in_chat": True,
            "chat_history": chat_history
        })
        # 发送回复
        await listener.send(ai_response)
    except Exception as e:
        await listener.send(f"调用失败：{str(e)}")


#API调用

async def call_ollama_with_history(chat_history) -> str:
    ollama_url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": "gemma3:1b",
        "messages": chat_history,
        "stream": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=ollama_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
        ) as response:
            result = await response.json()
            return result.get("message", {}).get("content", "未获取到AI回复")











