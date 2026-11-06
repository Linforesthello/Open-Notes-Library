# -*- coding: utf-8 -*-
"""统计每个内容流中的“文本基线行数”，用于判断是否发生折行/多出空行。"""
import re, sys, zlib

def objs(b):
    return {int(m.group(1)): m.group(2) for m in re.finditer(rb'(\d+)\s+0\s+obj(.*?)endobj', b, re.S)}

def inflate(raw):
    raw = raw.strip(b'\r\n')
    for cut in (0,1,2,3):
        try: return zlib.decompress(raw[:len(raw)-cut] if cut else raw)
        except Exception: continue
    return None

def streams(raw):
    m = re.search(rb'stream\r?\n(.*?)\r?\nendstream', raw, re.S)
    return inflate(m.group(1)) if m else None

def main(path):
    b = open(path,'rb').read()
    o = objs(b)
    print(f'页数: {len(re.findall(rb"/Type\s*/Page[^s]", b))}')
    total = 0
    for num, raw in o.items():
        d = streams(raw)
        if not d or b'BT' not in d or (b'Tj' not in d and b'TJ' not in d):
            continue
        t = d.decode('latin1')
        ys = []
        for m in re.finditer(r'([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+Tm', t):
            ys.append(round(float(m.group(6)), 1))
        # 也统计 TD/Td 造成的行推进
        td = len(re.findall(r'[-\d.]+\s+[-\d.]+\s+T[dD]', t))
        tstar = len(re.findall(r'T\*', t))
        uniq = sorted(set(ys))
        print(f'  流 obj#{num}: 锚点 {len(ys)}, 不同基线 {len(uniq)}, Td/TD {td}, T* {tstar}')
        if uniq:
            print(f'    基线值(前 12): {uniq[:12]}')
            print(f'    基线值(后 12): {uniq[-12:]}')
        total += len(uniq)
    print(f'  合计不同基线: {total}')

if __name__ == '__main__':
    main(sys.argv[1])
