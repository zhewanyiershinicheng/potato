import os
from nonebot.adapters.onebot.v11 import Bot, MessageSegment,Event,GroupMessageEvent,Message
def fetch_file(event:Event):
    get_msg = str(event.get_message()).strip()
    file_to_fetch = get_msg.strip('/fetch ').replace('\\', '').replace('/', '')
    uid=str(event.get_user_id())
    path="C:/Users/SCHWI/bot/bot1/save/"+uid+f"/{file_to_fetch}"
    if os.path.exists(path):
        return path
    return None





