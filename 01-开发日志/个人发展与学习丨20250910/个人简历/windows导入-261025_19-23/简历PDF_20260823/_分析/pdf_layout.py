# -*- coding: utf-8 -*-
"""粗略解析 Chromium 生成的 PDF：页数、字体、字号分布、文字包围盒、行距基线"""
import re, sys, zlib, statistics, collections

def streams(b):
    out = []
    for m in re.finditer(rb'stream\r?\n', b):
        start = m.end()
        end = b.find(b'endstream', start)
        if end < 0:
            continue
        try:
            d = zlib.decompress(b[start:end])
        except Exception:
            continue
        if b'BT' in d and (b'Tj' in d or b'TJ' in d):
            out.append(d)
    return out

def analyze(path, label):
    b = open(path, 'rb').read()
    print('=' * 78)
    print(f'[{label}] {path}')
    pages = len(re.findall(rb'/Type\s*/Page[^s]', b))
    print(f'  页数            : {pages}')
    mb = re.search(rb'/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', b)
    if mb:
        w = float(mb.group(3)) - float(mb.group(1))
        h = float(mb.group(4)) - float(mb.group(2))
        print(f'  页面尺寸(pt)    : {w:.1f} x {h:.1f}   (A4 = 595.3 x 841.9)')
    fonts = sorted(set(x.decode('latin1') for x in re.findall(rb'/BaseFont\s*/([#\w\+\-,\.]+)', b)))
    print(f'  嵌入字体        : {fonts}')

    ss = streams(b)
    print(f'  内容流数量      : {len(ss)}')
    all_sizes = collections.Counter()
    for idx, d in enumerate(ss):
        t = d.decode('latin1')
        sizes = collections.Counter()
        for m in re.finditer(r'/(F\d+)\s+([\d.]+)\s+Tf', t):
            sizes[round(float(m.group(2)), 2)] += 1
        all_sizes.update(sizes)
        pos = []
        for m in re.finditer(r'([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+Tm', t):
            pos.append((float(m.group(5)), float(m.group(6))))
        if pos:
            xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
            print(f'  --- 第 {idx+1} 个内容流 ---')
            print(f'    文本锚点数    : {len(pos)}')
            print(f'    文字 x 范围   : {min(xs):.1f} ~ {max(xs):.1f} pt  (左边距 {min(xs):.1f}pt = {min(xs)/72*25.4:.1f}mm, 右边距 {(w-max(xs)):.1f}pt = {(w-max(xs))/72*25.4:.1f}mm)')
            print(f'    文字 y 范围   : {min(ys):.1f} ~ {max(ys):.1f} pt  (上边距 {(h-max(ys)):.1f}pt = {(h-max(ys))/72*25.4:.1f}mm, 下边距 {min(ys):.1f}pt = {min(ys)/72*25.4:.1f}mm)')
            uy = sorted(set(round(y, 1) for y in ys), reverse=True)
            diffs = [round(uy[i]-uy[i+1], 2) for i in range(len(uy)-1)]
            small = [d2 for d2 in diffs if d2 > 2]
            if small:
                print(f'    行基线间距    : 中位数 {statistics.median(small):.2f}pt, 最小 {min(small):.2f}, 最大 {max(small):.2f}')
            print(f'    字号(该页)    : {sorted(sizes.items(), key=lambda kv: -kv[1])[:6]}')
    print(f'  字号(全文统计)  : {sorted(all_sizes.items(), key=lambda kv: -kv[1])[:10]}')
    print()

if __name__ == '__main__':
    analyze(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'x')
