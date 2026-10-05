# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hz import parse, get, DATA, TERNAME

def win(fn, x0, y0, x1, y1):
    p = fn if os.path.isabs(fn) else os.path.join(DATA, fn)
    m = parse(p)
    t, s = get(m)
    print('=== %s (%s) %dx%d  window x[%d..%d] y[%d..%d] ===' % (m['name'], fn, m['w'], m['h'], x0, x1, y0, y1))
    print('TERRAIN   ' + ''.join('%5d' % x for x in range(x0, x1 + 1)))
    for y in range(y0, y1 + 1):
        print('y=%3d     ' % y + ''.join('%5d' % t[y][x] for x in range(x0, x1 + 1)))
    print('SPRITE    ' + ''.join('%5d' % x for x in range(x0, x1 + 1)))
    for y in range(y0, y1 + 1):
        print('y=%3d     ' % y + ''.join('%5d' % s[y][x] for x in range(x0, x1 + 1)))
    print()

if __name__ == '__main__':
    win('coop10.map', 52, 14, 62, 22)
