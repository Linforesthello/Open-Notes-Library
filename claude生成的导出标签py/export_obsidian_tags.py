import os
import re
from collections import defaultdict

VAULT_PATH = r"C:\Users\86173\Desktop\Open_Notes_Library"
OUTPUT_PATH = r"C:\Users\86173\Desktop\obsidian_tags_export.txt"

def extract_tags(content):
    tags = set()

    # YAML frontmatter tags (e.g. tags: [ros, stm32] or tags:\n  - ros)
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        # Inline list: tags: [a, b, c]
        inline = re.search(r'tags:\s*\[([^\]]+)\]', fm)
        if inline:
            for t in inline.group(1).split(','):
                tags.add('#' + t.strip().strip('"').strip("'"))
        # Block list: tags:\n  - a\n  - b
        block = re.search(r'tags:\s*\n((?:\s+-\s+\S+\n?)+)', fm)
        if block:
            for t in re.findall(r'-\s+(\S+)', block.group(1)):
                tags.add('#' + t.strip())

    # Inline tags in body: #tagname (including nested like #STM32/ADC)
    body_tags = re.findall(r'(?<!\w)#([\w\u4e00-\u9fff/\-]+)', content)
    for t in body_tags:
        tags.add('#' + t)

    return tags

def main():
    tag_to_notes = defaultdict(list)

    for root, dirs, files in os.walk(VAULT_PATH):
        # Skip hidden folders (e.g. .obsidian)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in files:
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, VAULT_PATH)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                    content = f.read()

            for tag in extract_tags(content):
                tag_to_notes[tag].append(rel_path)

    # Sort tags alphabetically
    sorted_tags = sorted(tag_to_notes.items(), key=lambda x: x[0].lower())

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out:
        out.write(f"Obsidian Tag Export\n")
        out.write(f"Vault: {VAULT_PATH}\n")
        out.write(f"Total unique tags: {len(sorted_tags)}\n")
        out.write("=" * 50 + "\n\n")
        for tag, notes in sorted_tags:
            out.write(f"{tag:<40} ({len(notes)} {'note' if len(notes)==1 else 'notes'})\n")
            for note in sorted(notes):
                out.write(f"    - {note}\n")
            out.write("\n")

    print(f"Done! Found {len(sorted_tags)} unique tags.")
    print(f"Output saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
