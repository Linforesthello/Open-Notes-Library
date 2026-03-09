import os

VAULT_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library"
targets = ["#depth_camera", "#lidar", "#回顾", "#长期项目"]

found = False
for root, dirs, files in os.walk(VAULT_PATH):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        if not f.endswith('.md'): continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            for i, line in enumerate(fh, 1):
                for t in targets:
                    if t in line:
                        print(f"{os.path.relpath(path, VAULT_PATH)} 行{i}: {line.rstrip()}")
                        found = True

if not found:
    print("未找到任何残留标签，文件已修改成功，是Obsidian索引未刷新")

# import os, re

# VAULT_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library"
# targets = ["#问题", "#待做", "#复现"]

# for root, dirs, files in os.walk(VAULT_PATH):
#     dirs[:] = [d for d in dirs if not d.startswith('.')]
#     for f in files:
#         if not f.endswith('.md'): continue
#         path = os.path.join(root, f)
#         with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
#             for i, line in enumerate(fh, 1):
#                 for t in targets:
#                     if t in line:
#                         print(f"{os.path.relpath(path, VAULT_PATH)} 行{i}: {line.rstrip()}")