# -*- coding: utf-8 -*-
"""Hazard Ball .map / .cmp 解析与小工具"""
import struct, os, sys

DATA = r'D:\Hazard Ball\DATA'

def parse(path):
    b = open(path, 'rb').read()
    i = 0
    j = b.index(b'\n', i); tileset = b[i:j].decode('latin1'); i = j + 1
    w, h, tw, th = struct.unpack_from('<HHHH', b, i); i += 8
    j = b.index(b'\n', i); name = b[i:j].decode('latin1'); i = j + 1
    lvl = struct.unpack_from('<h', b, i)[0]; i += 2
    ter_off = i
    ter = bytearray(b[i:i + w * h]); i += w * h
    cell_off = i
    cells = b[i:i + w * h * 2]
    return dict(raw=b, tileset=tileset, w=w, h=h, tw=tw, th=th, name=name,
                lvl=lvl, ter=ter, cells=cells, ter_off=ter_off, cell_off=cell_off,
                path=path)

def get(m):
    """返回 terrain 二维 & cell 二维 (sprite_id)"""
    w, h = m['w'], m['h']
    t = m['ter']
    terrain = [[t[y * w + x] for x in range(w)] for y in range(h)]
    c = m['cells']
    spr = [[c[(y * w + x) * 2] + 256 * c[(y * w + x) * 2 + 1] for x in range(w)] for y in range(h)]
    return terrain, spr

# 地形索引 -> 短名（依据 ima 技术档案权威表）
TERNAME = {
    0: 'VOID', 1: 'WARP',
    2: 'P2ck_a', 3: 'P2ck_b', 4: 'P2ck_c', 5: 'P2ck_d',
    6: 'P1ck_a', 7: 'P1ck_b', 8: 'P1ck_c', 9: 'P1ck_d',
    30: 'MUD', 31: 'WATER', 32: 'ACID', 33: 'SURP', 34: 'CONSTR',
    35: 'THORN', 36: 'EXIT', 37: 'JUMPPAD', 76: 'LAVA',
}

def cells_with(terrain, vals):
    w = len(terrain[0]); h = len(terrain)
    out = []
    for y in range(h):
        for x in range(w):
            if terrain[y][x] in vals:
                out.append((x, y, terrain[y][x]))
    return out

def dump_win(terrain, spr, x0, y0, x1, y1, show_spr=False):
    """打印一个矩形窗口的 ASCII 视图"""
    lines = []
    header = '    ' + ''.join('%3d' % x for x in range(x0, x1 + 1))
    lines.append(header)
    for y in range(y0, y1 + 1):
        row = '%3d ' % y
        for x in range(x0, x1 + 1):
            v = terrain[y][x]
            ch = '%3d' % v
            row += ch
        lines.append(row)
    return '\n'.join(lines)

if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv) > 1 else 'coop10.map'
    p = fn if os.path.isabs(fn) else os.path.join(DATA, fn)
    m = parse(p)
    print(m['name'], m['w'], m['h'], m['tileset'], m['lvl'])
    terrain, spr = get(m)
    hits = cells_with(terrain, set(range(2, 10)))
    print('checkpoint cells:', len(hits))
    for x, y, v in hits:
        print('  (%d,%d)=%d %s' % (x, y, v, TERNAME.get(v, '')))
