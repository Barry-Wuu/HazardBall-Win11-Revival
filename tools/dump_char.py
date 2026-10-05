# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hz import parse, get, DATA

def char_of(v):
    if v == 0: return ' '
    if v == 76: return '~'          # LAVA
    if 2 <= v <= 5: return 'p'      # P2 checkpoint
    if 6 <= v <= 9: return 'P'      # P1 checkpoint
    if 46 <= v <= 54: return '.'    # textured floor / edge
    if v == 1: return '@'           # warp
    if v == 36: return 'E'          # exit
    return '#'

def dump(fn, x0, y0, x1, y1):
    m = parse(os.path.join(DATA, fn))
    t, s = get(m)
    print('=== %s (%s) %dx%d ===' % (m['name'], fn, m['w'], m['h']))
    print('     ' + ''.join(str(x // 100 % 10) for x in range(x0, x1 + 1)))
    print('     ' + ''.join(str(x // 10 % 10) for x in range(x0, x1 + 1)))
    print('     ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
    for y in range(y0, y1 + 1):
        print('%4d ' % y + ''.join(char_of(t[y][x]) for x in range(x0, x1 + 1)))

if __name__ == '__main__':
    dump('coop10.map', 38, 4, 78, 34)
