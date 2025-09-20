import json
import aiohttp
import asyncio  # 需要导入asyncio来运行异步函数


async def call_glm_api():
    payload = {
        "model": "glm-4.5-flash",
        "stream": False,
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
                "content": "ddd"
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url="https://open.bigmodel.cn/api/paas/v4/async/chat/completions",
                headers={
                    "Authorization": "Bearer 86de7ae9bfbe4154932af405bd409762.ERmE9iAJRpdDtx8h",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload)
        ) as response:
            # 关键修正：异步获取响应需要使用await
            result = await response.json()
            ai_response = result.get("response")
            print(result)


# 运行异步函数
asyncio.run(call_glm_api())
