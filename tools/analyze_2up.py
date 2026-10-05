# -*- coding: utf-8 -*-
"""
分析 Hazard Ball 的 2UP GAME.sav (coop 进度存档)。

前提: 需要先在游戏里进 2UP GAME -> RESUME GAME, 让它生成真实存档。
本脚本会 hexdump + 尝试常见整数布局, 找出"当前 coop 关号"字段。
"""
import os, struct, sys

SAVE = r'D:\Hazard Ball\DATA\SAVE'
TARGET = os.path.join(SAVE, '2UP GAME.sav')

def hexdump(d, base=0, n=None):
    n = n or len(d)
    for i in range(0, n, 16):
        ch = d[i:i+16]
        txt = ''.join(chr(c) if 32 <= c < 127 else '.' for c in ch)
        print('  %04x  %-47s  %s' % (base + i, ch.hex(' '), txt))

def try_layouts(d):
    print()
    print('=== 尝试解析 ===')
    n = len(d)
    # 逐字节扫, 找值在 1..10 的位置( coop 关号候选 )
    print('  值为 1..10 的字节偏移 (coop 关号候选):')
    for i in range(n):
        if 1 <= d[i] <= 10:
            print('     off %3d = %d' % (i, d[i]))
    # 逐 dword 看
    print()
    print('=== dword 视图 ===')
    for i in range(0, min(n, 256) - 3, 4):
        v = struct.unpack_from('<i', d, i)[0]
        mark = ''
        if 0 < v < 100000:
            mark = '  <-'
        print('  off %3d : %-12d (0x%08x)%s' % (i, v, v & 0xFFFFFFFF, mark))
    # 短整数组视图
    print()
    print('=== word 视图 (前 128 字节) ===')
    for i in range(0, min(n, 128) - 1, 2):
        v = struct.unpack_from('<H', d, i)[0]
        if 0 < v <= 10:
            print('  off %3d : word = %d   <== 候选' % (i, v))

if __name__ == '__main__':
    if not os.path.exists(TARGET):
        print('!! 存档不存在:', TARGET)
        print()
        print('请先在游戏里: 主菜单 -> 2UP GAME -> RESUME GAME')
        print('(即使没有存档, 游戏也会创建/尝试读取, 之后本文件可能出现)')
        print()
        print('当前 SAVE 目录内容:')
        for f in sorted(os.listdir(SAVE)):
            print('   %-28s %d 字节' % (f, os.path.getsize(os.path.join(SAVE, f))))
        sys.exit(1)

    d = open(TARGET, 'rb').read()
    print('=== %s (%d 字节) ===' % (TARGET, len(d)))
    hexdump(d)
    try_layouts(d)
