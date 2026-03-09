import os
import re
import shutil
from datetime import datetime

VAULT_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library"
BACKUP_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = r"C:\Users\86173\Desktop\obsidian_tag_fix_log.txt"

# ============================================================
# 标签替换规则
# 格式: (旧标签, 新标签)
# 只替换完整标签，不会误伤正文内容
# ============================================================
REPLACEMENTS = [
    # 【1】统一"问题"体系：中文 → 英文
    ("#问题/重复出现",                      "#Problems/recurring"),
    ("#问题/tree可以单独对某一个下属文件夹展开吗",   "#Problems/unsolved/obsidian-tree"),
    ("#问题",                              "#Problems"),

    # 【2】统一"待办"体系：#待做/... → #待/...
    ("#待做/已实现",                         "#待/做/已实现"),
    ("#待做/正在进行",                        "#待/做/正在进行"),

    # 【3】统一"复现"标签：独立的 #复现 合并到 #回顾/复现
    ("#复现",                              "#回顾/复现"),
]

# ============================================================
# 孤儿父标签：只出现1次且子标签更具体，直接删除父标签
# （从笔记中移除这些标签行，不替换为其他标签）
# ============================================================
REMOVE_TAGS = [
    "#depth_camera",   # 子标签 depth_camera/xxx 更具体
    "#lidar",          # 子标签 lidar/xxx 更具体
    "#回顾",            # 子标签 回顾/复现 更具体
    "#长期项目",         # 只出现1次，子标签更具体
]

def backup_vault(vault_path, backup_path):
    print(f"正在备份 vault 到: {backup_path}")
    shutil.copytree(vault_path, backup_path)
    print("备份完成！\n")

def replace_tag_in_text(content, old_tag, new_tag):
    """
    替换正文和 frontmatter 中的标签。
    只匹配完整标签（后面不跟字母/数字/斜杠），避免误替换子标签。
    """
    # old_tag 里的特殊字符需要转义
    escaped = re.escape(old_tag[1:])  # 去掉 # 再转义
    # 匹配 #tag 后面不跟 / 或 \w（确保是完整标签）
    pattern = r'(?<![/\w\u4e00-\u9fff])#' + escaped + r'(?![/\w\u4e00-\u9fff])'
    return re.sub(pattern, new_tag, content)

def remove_tag_in_text(content, tag):
    """
    从正文中删除孤儿父标签（整个 #tag，包括前后空格）。
    如果该标签独占一行，删除整行；否则只删除标签本身。
    """
    escaped = re.escape(tag[1:])
    pattern = r'(?<![/\w\u4e00-\u9fff])#' + escaped + r'(?![/\w\u4e00-\u9fff])'

    lines = content.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # 如果这行只有这个标签（可能加空格），整行删除
        if re.fullmatch(r'\s*#' + escaped + r'\s*', line):
            continue
        else:
            # 否则只删除标签，保留其他内容
            new_line = re.sub(r'\s*' + pattern, '', line)
            new_lines.append(new_line)
    return '\n'.join(new_lines)

def process_vault(vault_path, replacements, remove_tags):
    log_entries = []
    total_files_changed = 0

    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in files:
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, vault_path)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    original = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                    original = f.read()

            content = original

            file_changes = []

            # 执行替换
            for old_tag, new_tag in replacements:
                new_content = replace_tag_in_text(content, old_tag, new_tag)
                if new_content != content:
                    file_changes.append(f"  替换: {old_tag}  →  {new_tag}")
                    content = new_content

            # 执行删除
            for tag in remove_tags:
                new_content = remove_tag_in_text(content, tag)
                if new_content != content:
                    file_changes.append(f"  删除: {tag}")
                    content = new_content

            if file_changes:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                total_files_changed += 1
                log_entries.append(f"\n[修改] {rel_path}")
                log_entries.extend(file_changes)

    return log_entries, total_files_changed

def write_log(log_entries, total_files, log_path, backup_path):
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("Obsidian Tag Fix Log\n")
        f.write(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"备份位置: {backup_path}\n")
        f.write(f"共修改文件: {total_files} 个\n")
        f.write("=" * 60 + "\n")
        f.write("\n".join(log_entries))
    print(f"\n日志已保存至: {log_path}")

def main():
    print("=" * 60)
    print("Obsidian 标签批量修复脚本")
    print("=" * 60)
    print(f"\nVault 路径: {VAULT_PATH}")
    print(f"\n将执行以下操作:")
    print(f"  替换规则: {len(REPLACEMENTS)} 条")
    for old, new in REPLACEMENTS:
        print(f"    {old}  →  {new}")
    print(f"  删除标签: {len(REMOVE_TAGS)} 个")
    for t in REMOVE_TAGS:
        print(f"    {t}")

    print("\n请确认是否继续？备份将自动创建。(输入 y 继续，其他键退出)")
    confirm = input("> ").strip().lower()
    if confirm != 'y':
        print("已取消。")
        return

    # 备份
    backup_vault(VAULT_PATH, BACKUP_PATH)

    # 处理
    print("正在处理标签...")
    log_entries, total = process_vault(VAULT_PATH, REPLACEMENTS, REMOVE_TAGS)

    # 写日志
    write_log(log_entries, total, LOG_PATH, BACKUP_PATH)

    print(f"\n完成！共修改 {total} 个文件。")
    print(f"如需还原，备份在: {BACKUP_PATH}")

if __name__ == "__main__":
    main()
