# -*- coding: utf-8 -*-
"""补齐 coop10 'TEMPLE OF DOOM' 两个起点块的缺失角(6 / 2)"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hz import parse, get, DATA

FN = 'coop10.map'
p = os.path.join(DATA, FN)
m = parse(p)
w, h, off = m['w'], m['h'], m['ter_off']
ter = m['ter']

targets = [(55, 17, 6), (58, 17, 2)]   # x, y, 期望地形值
print('terrain offset =', off, 'w,h =', w, h)

fixed = 0
for x, y, want in targets:
    i = y * w + x
    old = ter[i]
    print('(%d,%d) idx=%d file_off=%d  old=%d -> new=%d' % (x, y, i, off + i, old, want))
    ter[i] = want
    fixed += 1

bak = p + '.orig'
if not os.path.exists(bak):
    shutil.copy2(p, bak)
    print('backup ->', bak)
else:
    print('backup exists, keep:', bak)

with open(p, 'wb') as f:
    f.write(m['raw'][:off] + bytes(ter) + m['raw'][off + w * h:])
print('patched, %d cells' % fixed)

# 回读校验
m2 = parse(p)
t2, s2 = get(m2)
for x, y, want in [(55, 17, 6), (58, 17, 2)]:
    print('verify (%d,%d)=%d (want %d) %s' % (x, y, t2[y][x], want, 'OK' if t2[y][x] == want else 'FAIL'))
