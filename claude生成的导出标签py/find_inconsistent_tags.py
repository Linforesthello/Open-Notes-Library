import os
import re
from collections import defaultdict

VAULT_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library"
OUTPUT_PATH = r"C:\Users\86173\Desktop\obsidian_tag_issues.txt"

def extract_tags(content):
    tags = set()
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        inline = re.search(r'tags:\s*\[([^\]]+)\]', fm)
        if inline:
            for t in inline.group(1).split(','):
                tags.add(t.strip().strip('"').strip("'"))
        block = re.search(r'tags:\s*\n((?:\s+-\s+\S+\n?)+)', fm)
        if block:
            for t in re.findall(r'-\s+(\S+)', block.group(1)):
                tags.add(t.strip())
    body_tags = re.findall(r'(?<!\w)#([\w\u4e00-\u9fff/\-]+)', content)
    for t in body_tags:
        tags.add(t)
    return tags

def collect_all_tags(vault_path):
    tag_to_notes = defaultdict(list)
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in files:
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, vault_path)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                    content = f.read()
            for tag in extract_tags(content):
                tag_to_notes[tag].append(rel_path)
    return tag_to_notes

def find_issues(tag_to_notes):
    tags = list(tag_to_notes.keys())
    issues = {
        "case_conflicts": [],       # 大小写不一致
        "separator_conflicts": [],  # 分隔符不一致 (/ vs _)
        "lang_duplicates": [],      # 中英文同义重复
        "orphan_tags": [],          # 只出现1次的标签
        "root_and_child": [],       # 同时存在父标签和子标签（如 #A 和 #A/B）
    }

    # 1. 大小写冲突
    lower_map = defaultdict(list)
    for tag in tags:
        lower_map[tag.lower()].append(tag)
    for lower, variants in lower_map.items():
        if len(variants) > 1:
            issues["case_conflicts"].append(variants)

    # 2. 分隔符不一致 (/ vs _)
    def normalize_sep(tag):
        return tag.replace('_', '/').lower()
    sep_map = defaultdict(list)
    for tag in tags:
        sep_map[normalize_sep(tag)].append(tag)
    for norm, variants in sep_map.items():
        if len(variants) > 1 and variants not in issues["case_conflicts"]:
            # Only flag if difference is actually _ vs /
            has_slash = any('/' in t for t in variants)
            has_under = any('_' in t for t in variants)
            if has_slash and has_under:
                issues["separator_conflicts"].append(variants)

    # 3. 父子标签同时存在 (e.g. #FreeRTOS and #FreeRTOS/Queue)
    tag_set = set(tags)
    checked = set()
    for tag in tags:
        if '/' in tag:
            root = tag.split('/')[0]
            if root in tag_set and root not in checked:
                children = [t for t in tags if t.startswith(root + '/')]
                issues["root_and_child"].append((root, children))
                checked.add(root)

    # 4. 只出现1次的标签（孤儿标签）
    for tag, notes in tag_to_notes.items():
        if len(notes) == 1:
            issues["orphan_tags"].append((tag, notes[0]))

    # 5. 疑似中英文同义 (手工映射常见对)
    known_pairs = [
        ("问题", "Problems"),
        ("规划", "plan"),
        ("复现", "reproduce"),
        ("整理", "organize"),
        ("烧录", "flash"),
        ("回顾", "review"),
    ]
    for zh, en in known_pairs:
        zh_tags = [t for t in tags if zh in t]
        en_tags = [t for t in tags if en.lower() in t.lower()]
        if zh_tags and en_tags:
            issues["lang_duplicates"].append((zh_tags, en_tags))

    return issues

def write_report(issues, tag_to_notes, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Obsidian Tag Issues Report\n")
        f.write("=" * 60 + "\n\n")

        # Case conflicts
        f.write(f"【1】大小写冲突 ({len(issues['case_conflicts'])} 组)\n")
        f.write("    同一标签存在不同大小写写法，建议统一\n")
        f.write("-" * 40 + "\n")
        for variants in issues["case_conflicts"]:
            counts = [f"#{v} ({len(tag_to_notes[v])}篇)" for v in variants]
            f.write("  " + "  vs  ".join(counts) + "\n")
        f.write("\n")

        # Separator conflicts
        f.write(f"【2】分隔符不一致 ({len(issues['separator_conflicts'])} 组)\n")
        f.write("    同一概念混用 / 和 _ 作为层级分隔符，建议统一用 /\n")
        f.write("-" * 40 + "\n")
        for variants in issues["separator_conflicts"]:
            counts = [f"#{v} ({len(tag_to_notes[v])}篇)" for v in variants]
            f.write("  " + "  vs  ".join(counts) + "\n")
        f.write("\n")

        # Root and child
        f.write(f"【3】父子标签同时存在 ({len(issues['root_and_child'])} 组)\n")
        f.write("    既有 #A 又有 #A/B，父标签可能是多余的\n")
        f.write("-" * 40 + "\n")
        for root, children in issues["root_and_child"]:
            f.write(f"  父: #{root} ({len(tag_to_notes[root])}篇)\n")
            for child in children:
                f.write(f"      子: #{child} ({len(tag_to_notes[child])}篇)\n")
        f.write("\n")

        # Lang duplicates
        f.write(f"【4】疑似中英文同义标签 ({len(issues['lang_duplicates'])} 组)\n")
        f.write("    同一概念中英文混用，建议选一种\n")
        f.write("-" * 40 + "\n")
        for zh_tags, en_tags in issues["lang_duplicates"]:
            f.write(f"  中文: {', '.join('#'+t for t in zh_tags)}\n")
            f.write(f"  英文: {', '.join('#'+t for t in en_tags)}\n\n")

        # Orphan tags
        f.write(f"【5】孤儿标签（只出现1次，共 {len(issues['orphan_tags'])} 个）\n")
        f.write("    这些标签只用过一次，考虑是否值得保留为标签\n")
        f.write("-" * 40 + "\n")
        for tag, note in sorted(issues["orphan_tags"], key=lambda x: x[0].lower()):
            f.write(f"  #{tag:<40} → {note}\n")

    print(f"报告已生成：{output_path}")

def main():
    print("正在扫描 vault...")
    tag_to_notes = collect_all_tags(VAULT_PATH)
    print(f"共找到 {len(tag_to_notes)} 个标签，分析中...")
    issues = find_issues(tag_to_notes)
    write_report(issues, tag_to_notes, OUTPUT_PATH)

if __name__ == "__main__":
    main()
