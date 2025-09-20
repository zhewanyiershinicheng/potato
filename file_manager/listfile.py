import os
from nonebot.adapters.onebot.v11 import Bot, MessageSegment,Event,GroupMessageEvent,Message
def get_list(event:Event):
    """生成目录树字符串（非递归）"""
    lines = []
    uid=str(event.get_user_id())
    startpath="C:\\Users\\SCHWI\\bot\\bot1\save\\"+uid
    stack = [(startpath, 0, True)]  # (路径, 深度, 是否是最后一个)
    if not os.path.exists(startpath):
        return "你似乎从未使用过？"
    while stack:
        path, depth, is_last = stack.pop()
        indent = '    ' * depth
        name = os.path.basename(path) or path  # 处理根目录

        lines.append(f"{indent}{name}{'/' if os.path.isdir(path) else ''}")

        if os.path.isdir(path):
            try:
                items = sorted(os.listdir(path))
                items_paths = [os.path.join(path, item) for item in items]

                # 逆序压入栈
                for i in range(len(items_paths) - 1, -1, -1):
                    is_last_item = (i == len(items_paths) - 1)
                    stack.append((items_paths[i], depth + 1, is_last_item))

            except PermissionError:
                lines.append(f"{indent}    └── [权限不足]")
    return '\n'.join(lines).replace(uid,"your uid")


