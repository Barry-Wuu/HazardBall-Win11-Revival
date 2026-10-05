# -*- coding: utf-8 -*-
"""暴力扫描 E8/E9 相对调用/跳转，统计目标"""
import struct, sys, collections
from peek import B, IMG

# .text raw 0x1000..0x42f15 ; VA = IMG + file_off
LO, HI = 0x1000, 0x42f15
res = collections.defaultdict(list)
for i in range(LO, HI - 4):
    op = B[i]
    if op in (0xE8, 0xE9):
        rel = struct.unpack_from('<i', B, i + 1)[0]
        tgt = IMG + i + 5 + rel
        res[tgt].append((i, op))

targets = [0x408200, 0x408320, 0x408430, 0x408560, 0x4085e0, 0x408720, 0x4087b0,
           0x4086f0, 0x408800, 0x4087d0, 0x40b1c0, 0x4075b0, 0x407720]
for t in targets:
    hits = res.get(t, [])
    print('%08x -> %d %s' % (t, len(hits), ['%06x/%02x' % h for h in hits[:6]]))

# 找出 0x4075b0 所在函数的可能入口：列出所有落在 0x407400-0x4075b0 的 jmp/call 目标
print()
print('call/jmp targets in 0x407300-0x407600:', sorted(hex(k) for k in res if 0x407300 <= k < 0x407600))
