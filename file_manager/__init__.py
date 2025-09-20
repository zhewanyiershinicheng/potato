from nonebot.params import Depends
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageSegment,Event,GroupMessageEvent,Message,PrivateMessageEvent
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State
from .listfile import get_list
from .fetchfile import fetch_file
import os
import requests
__version__="v0.1.0"
__author__="chongkai"
__bot_uid__=3590605579

download=on_command("save",priority=10,block=True)
list=on_command("list",priority=10,block=True)
fetch=on_command("fetch",priority=10,block=True)
delete=on_command("del",priority=10,block=True)

"""
如果直接用Message对象，要保证和got的参数中的名字一致，才能正常接收使用
state则是存储在state["参数名"]中，但是这个东西是存储上下文中got或者receive
的参数,彼此跨越访问使用。使用Message传递就是只能使用自己的（虽然命名都要严格相等
即使是state也要保证是其内容是存在got语句，不过传参时由于无需指定，所以不会出现message
由于两个名称不匹配而接收不到的问题）
下面的state:T_state等效于file:Meassage=None，但是实际上T_state[file]也是Messsage
所以遍历消息还是必要的
"""

@download.got("file",prompt="请发送需要上传的文件，取消上传请发送q")
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    text=event.get_plaintext().strip()
    if text=="q":
        await download.finish("已结束操作")
    file_info=None
    file_message=state["file"]
    for seg in file_message:
        if seg.type=="file":
            file_info=seg.data
            break
    if not file_info:
        await download.reject("Is fIle?")
        return
    try:
        file_id = file_info["file_id"]
        file_name = file_info["file_name"]
        #file_size = file_info.get("file_size", "未知")
        busid=file_info.get("busid",0)
        resp = await bot.get_group_file_url(
            group_id=event.group_id,
            file_id=file_id,
            busid=busid
        )
        url=resp["url"]
    except Exception as e:
        await download.send(f"Error:{str(e)}")
        return
    #python的try-except可以有一个else语句，在没有异常时执行（似乎很鸡肋的功能
    #await download.send(Message(url))
    uid=str(event.get_user_id())
    save_path="C:\\Users\\SCHWI\\bot\\bot1\save\\" + uid
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    full_path=os.path.join(save_path,file_name)
    try:
        """下载部分"""
        response=requests.get(url,stream=True)
        if response.status_code==200:
            with open(full_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            await download.send(f"文件保存成功{file_name}")
        else:
            await download.send(f"下载失败，HTTP:{response.status_code}")
    except Exception as e:
        await download.finish(f"Error:{str(e)}")
    download.finish()
@download.got("file",prompt="请发送需要上传的文件，取消上传请发送q")
async def _(bot:Bot,event:PrivateMessageEvent,state:T_State):
    text=event.get_plaintext().strip()
    if text=="q":
        await download.finish("已结束操作")
    file_info=None
    file_message=state["file"]
    for seg in file_message:
        if seg.type=="file":
            file_info=seg.data
            break
    if not file_info:
        await download.reject("Is fIle?")
        return
    try:
        file_id = file_info["file_id"]
        file_name = file_info["file_name"]
        #file_size = file_info.get("file_size", "未知")
        file_hash=file_info.get("file_hash",0)
        resp = await bot.get_private_file_url(
            user_id=__bot_uid__,
            file_id=file_id,
            file_hash=file_hash
        )
        url=resp["url"]
    except Exception as e:
        await download.send(f"Error:{str(e)}")
        return
    uid=str(event.get_user_id())
    save_path="C:\\Users\\SCHWI\\bot\\bot1\save\\" + uid
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    full_path=os.path.join(save_path,file_name)
    try:
        """下载部分"""
        response=requests.get(url,stream=True)
        if response.status_code==200:
            with open(full_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            await download.send(f"文件保存成功{file_name}")
        else:
            await download.send(f"下载失败，HTTP:{response.status_code}")
    except Exception as e:
        await download.finish(f"Error:{str(e)}")
    download.finish()

@list.handle()
async def _(bot:Bot,event:Event,lists:str=Depends(get_list,use_cache=False)):
    await list.finish(f"找到的部分\n{lists}")

@fetch.handle()
async def _(bot:Bot,event:Event,path=Depends(fetch_file,use_cache=False)):
    if path==None:
        await fetch.finish("没有这个文件!可以使用/list获取已经上传的文件")
        return
    else:
        # path类似于"C:/Users/SCHWI/bot/bot1/save/xxx"
        try:
            index = path.rfind('/')
            if index == -1:
                name="什么情况这是？？？"
            else:
                # 返回从最后一个'/'后面到字符串末尾的部分
                name = path[index + 1:]
            if isinstance(event,GroupMessageEvent):
                await bot.call_api("upload_group_file", group_id=event.group_id, file=path, name=name)
            elif isinstance(event,PrivateMessageEvent):
                await bot.call_api("upload_private_file",user_id=event.user_id,file=path, name=name)#不知道为什么，这里不能用get_user_id,，而且api调用也并非内置方法
        except Exception as e:
            await fetch.finish(f"Error!{e}")
        await fetch.finish("文件发送成功")

@delete.handle()
async def _(bot:Bot,event:Event):
    get_msg = str(event.get_message()).strip()
    file_to_fetch = get_msg.strip('/del ').replace('\\', '').replace('/', '')
    uid = str(event.get_user_id())
    path = "C:/Users/SCHWI/bot/bot1/save/" + uid + f"/{file_to_fetch}"
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            await delete.finish("删不掉或者不存在！")
        await delete.finish("删除成功")