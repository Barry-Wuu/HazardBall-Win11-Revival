# -*- coding: utf-8 -*-
"""
扫描 coop*.map 的双人出生点块完整性。

背景
----
多人模式(co-op)每张图有两个出生点, 各占一个 2x2 的 4 格地块, 以 terrain 编号区分:
    玩家 1 = terrain 6/7/8/9  (左上/右上/左下/右下)
    玩家 2 = terrain 2/3/4/5
原版 coop10 "TEMPLE OF DOOM" 的两个起点各缺左上角(a 格), 缺口被普通地板占据,
两个起点块又被第 57 列的岩浆隔开, 出生即卡死。本脚本扫描全部 coop 图,
用"该编号集合恰好构成一个完整 2x2"为判据, 列出所有残缺起点。

只扫 coop*.map: 单关卡(level*.map)与标题画面(menus.map)本就没有双人出生点。

用法:  python scan_ck.py [DATA目录]
"""
import os, re, struct, sys

DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DATA')

def parse(path):
    """.map 结构: tileset\\n + w,h,tw,th(u16 x4) + name\\n + level(i16) + terrain[w*h] + cells[w*h*2]"""
    b = open(path, 'rb').read()
    i = b.index(b'\n'); tileset = b[:i].decode('latin1'); i += 1
    w, h, tw, th = struct.unpack_from('<HHHH', b, i); i += 8
    j = b.index(b'\n', i); name = b[i:j].decode('latin1'); i = j + 1
    lvl = struct.unpack_from('<h', b, i)[0]; i += 2
    ter = b[i:i + w * h]
    return dict(tileset=tileset, w=w, h=h, tw=tw, th=th, name=name, lvl=lvl,
                ter=ter, off_ter=i)

def check(fn):
    """返回 (残缺列表, 地图信息)。残缺项 = (起点terrain基号, [(坐标, 应为, 实为), ...])"""
    m = parse(os.path.join(DATA, fn))
    w, h, ter = m['w'], m['h'], m['ter']

    # 找出所有 2x2 块, 统计哪些"恰好"被某个起点编号集合完整占据
    bad = []
    for base in (6, 2):
        want = {base: None, base + 1: None, base + 2: None, base + 3: None}
        found_complete = False
        cands = []
        for y in range(h - 1):
            for x in range(w - 1):
                quad = (ter[y*w + x], ter[y*w + x + 1],
                        ter[(y+1)*w + x], ter[(y+1)*w + x + 1])
                # 标准排布: base base+1 / base+2 base+3
                if quad == (base, base+1, base+2, base+3):
                    found_complete = True
                    break
            if found_complete:
                break
        if found_complete:
            continue
        # 没有完整块 -> 找"部分存在"的区域作为残缺候选
        for y in range(h - 1):
            for x in range(w - 1):
                quad = (ter[y*w + x], ter[y*w + x + 1],
                        ter[(y+1)*w + x], ter[(y+1)*w + x + 1])
                hit = sum(1 for v, t in zip(quad, (base, base+1, base+2, base+3)) if v == t)
                if 0 < hit < 4:
                    cands.append((x, y, quad))
        if cands:
            # 取最靠上(数值最小)的候选作为报告点
            x, y, quad = min(cands, key=lambda c: (c[1], c[0]))
            miss = []
            for dx, dy, t in ((0,0,base), (1,0,base+1), (0,1,base+2), (1,1,base+3)):
                cur = ter[(y+dy)*w + (x+dx)]
                if cur != t:
                    miss.append(((x+dx, y+dy), t, cur))
            bad.append((base, miss))
    return bad, m

if __name__ == '__main__':
    maps = [f for f in os.listdir(DATA) if f.lower().startswith('coop') and f.lower().endswith('.map')]
    def key(f):
        mm = re.match(r'([a-z]+)(\d*)', f.lower())
        return (mm.group(1), int(mm.group(2)) if mm.group(2) else -1)
    print('扫描 %d 张 coop 地图 ...' % len(maps))
    badmaps = []
    for fn in sorted(maps, key=key):
        try:
            bad, m = check(fn)
        except Exception as e:
            print('  [跳过] %s: %s' % (fn, e)); continue
        if bad:
            badmaps.append((fn, bad, m))
    print()
    if not badmaps:
        print('✅ 全部 coop 地图的双人起点块均为完整 2x2')
    else:
        print('❌ 发现 %d 张地图起点残缺:' % len(badmaps))
        for fn, bad, m in badmaps:
            print('  %s  (%d x %d, 关号 %d, "%s")' % (fn, m['w'], m['h'], m['lvl'], m['name']))
            for base, miss in bad:
                print('     起点 terrain %d 缺:' % base)
                for (x, y), v, cur in miss:
                    print('        (%d,%d) 应为 %d, 实为 %d' % (x, y, v, cur))
