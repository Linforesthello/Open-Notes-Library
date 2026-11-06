# -*- coding: utf-8 -*-
"""从 Chromium 生成的 PDF 中抽取文字（ToUnicode CMap），输出到 UTF-8 文件。"""
import re, sys, zlib, io

def get_objects(b):
    objs = {}
    for m in re.finditer(rb'(\d+)\s+0\s+obj(.*?)endobj', b, re.S):
        objs[int(m.group(1))] = m.group(2)
    return objs

def inflate(raw):
    raw = raw.strip(b'\r\n')
    for cut in (0, 1, 2, 3):
        try:
            return zlib.decompress(raw[:len(raw)-cut] if cut else raw)
        except Exception:
            continue
    return None

def stream_data(raw):
    m = re.search(rb'stream\r?\n(.*?)\r?\nendstream', raw, re.S)
    if not m:
        return None
    return inflate(m.group(1))

def parse_cmap(data):
    cmap = {}
    txt = data.decode('latin1')
    for blk in re.findall(r'beginbfchar(.*?)endbfchar', txt, re.S):
        for a, b in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            try:
                cmap[int(a, 16)] = ''.join(chr(int(b[i:i+4], 16)) for i in range(0, len(b), 4))
            except Exception:
                pass
    for blk in re.findall(r'beginbfrange(.*?)endbfrange', txt, re.S):
        for lo, hi, dst in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            lo_i, hi_i, d_i = int(lo, 16), int(hi, 16), int(dst, 16)
            for k in range(lo_i, min(hi_i, lo_i + 4096) + 1):
                cmap[k] = chr(d_i + (k - lo_i))
    return cmap

def decode_hex(hx, cmap):
    out = []
    for i in range(0, len(hx) - 1, 4):
        code = int(hx[i:i+4], 16)
        out.append(cmap.get(code, '\uFFFD'))
    return ''.join(out)

def main(path, outpath):
    b = open(path, 'rb').read()
    objs = get_objects(b)

    # 字体对象 -> CMap
    font_maps = {}
    for num, raw in objs.items():
        m = re.search(rb'/ToUnicode\s+(\d+)\s+0\s+R', raw)
        if m:
            data = stream_data(objs.get(int(m.group(1)), b''))
            if data:
                font_maps[num] = parse_cmap(data)

    # 资源名 -> 字体对象
    name2obj = {}
    for num, raw in objs.items():
        for fm in re.finditer(rb'/Font\s*<<(.*?)>>', raw, re.S):
            for nm, on in re.findall(rb'/(\w+)\s+(\d+)\s+0\s+R', fm.group(1)):
                name2obj.setdefault(nm.decode(), int(on))

    # 所有含 BT 的流都是内容流
    contents = []
    for num, raw in objs.items():
        data = stream_data(raw)
        if data and b'BT' in data and (b'Tj' in data or b'TJ' in data):
            contents.append((num, data))

    lines = []
    for num, data in contents:
        txt = data.decode('latin1')
        cur_name = None
        cur = {}
        buf = []
        pos = 0
        pat = re.compile(r'/(\w+)\s+[\d.]+\s+Tf|<([0-9A-Fa-f]+)>\s*Tj|\[(.*?)\]\s*TJ|(-?[\d.]+)\s+(-?[\d.]+)\s+Td|(T\*)', re.S)
        for tok in pat.finditer(txt):
            if tok.group(1):
                nm = tok.group(1)
                if nm != cur_name:
                    cur_name = nm
                    cur = font_maps.get(name2obj.get(nm, -1), {})
                continue
            if tok.group(2):
                buf.append(decode_hex(tok.group(2), cur))
            elif tok.group(3):
                for hx in re.findall(r'<([0-9A-Fa-f]+)>', tok.group(3)):
                    buf.append(decode_hex(hx, cur))
                if re.search(r'\]\s*TJ', txt[tok.start():tok.end()+3]):
                    pass
            elif tok.group(4) is not None or tok.group(6):
                if buf:
                    lines.append(''.join(buf))
                    buf = []
        if buf:
            lines.append(''.join(buf))

    text = '\n'.join(l for l in lines if l.strip())
    with io.open(outpath, 'w', encoding='utf-8') as f:
        f.write(f'对象数: {len(objs)}\n字体对象: {len(font_maps)}\n内容流: {len(contents)}\n')
        f.write(f'抽取行数: {len(lines)}\n字符数: {len(text)}\n')
        f.write('=' * 60 + '\n')
        f.write(text)
        f.write('\n' + '=' * 60 + '\n')
        for kw in ['技能特长', '导航与 SLAM', '状态估计', 'ROS2 与系统', '运动控制底座', '强化学习', '工程素养',
                   '核心能力', '获奖经历', '教育背景', '项目经历', '低矮障碍', 'Robocon']:
            f.write(f'  {kw:14}: {"有" if kw in text else "缺"}\n')
    print('done ->', outpath)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
