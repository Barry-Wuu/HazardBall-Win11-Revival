# -*- coding: utf-8 -*-
"""
Hazard Ball — 跳过 2UP 存档校验补丁

原理 (逆向自 Hazard.exe 0x411990 读档函数):
    校验1 (0x411A42~0x411A6F):
        ecx = 存档字段 ^ 0xE0301
        eax = 存档字段 ^ 0xE0301
        edx = 0xFFFEE2B3 - [0x44DC30]      ; [0x44DC30] 是运行时基准
        cmp eax, edx
        je  0x411A82                         ; 相等=通过, 跳过清零
        ; 不等 -> mov [0x44DC30],1 / [0x463420],0 / [0x44B5A8],0 (标记存档无效)
    校验2 (0x411A82~0x411A94):
        eax = [0x44B5A8] - ecx - 0x793B
        cmp ecx, eax
        je  0x411AA2                         ; 相等=通过
        ; 不等 -> 清零 [0x44B5A8] / [0x463420]
    校验3 (0x411AB3~0x411ACB): 与玩家槽位有关, 失败同样置 [0x44DC30]=1

关键: 基准 [0x44DC30]/[0x44B5A8] 由游戏运行时维护(上次成功存档时写入),
      **离线无法算出合法存档** —— 手改 2UP GAME.sav 必被判定无效并回退到第 1 关。

修法: 把三处"通过才跳过失败块"的 je 改成 jmp, 使校验结果恒为通过:
    0x411A6F  74 11 -> EB 11   (je +0x11  ->  jmp +0x11)
    0x411A94  74 0C -> EB 0C
    0x411ACB  c7 05 30 dc 44 00 01 00 00 00  -> 90*10  (直接 NOP 掉置位)
前两处改为无条件跳转后, 失败块永远不执行; 第三处直接 NOP。

结果: 任何 2UP GAME.sav 都被接受, 关号字段 +0 直接生效。
"""
import struct, sys, os, shutil, time
sys.path.insert(0, r'D:\B++\WorkBuddy\hazard_hack')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
BAK = r'D:\Hazard Ball\Hazard.exe.presavcheck'
IMG = 0x400000
SECS = [(0x1000, 0x1000, 0x42000), (0x43000, 0x43000, 0x2000), (0x45000, 0x45000, 0x2d000),
        (0x72000, 0x72000, 0x13000), (0x9c000, 0x74000, 0x1000)]
def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz in SECS:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

PATCHES = [
    (0x411A6F, '7411', 'EB11', '校验1: je -> jmp (恒通过)'),
    (0x411A94, '740C', 'EB0C', '校验2: je -> jmp (恒通过)'),
    (0x411ACB, 'c70530dc440001000000', '90' * 10, '校验3: NOP 掉 [0x44DC30]=1'),
]

def apply():
    b = bytearray(open(P, 'rb').read())
    print('=== 校验原字节 ===')
    ok = True
    for va, oh, nh, desc in PATCHES:
        o = va2off(va)
        want = bytes.fromhex(oh).hex()          # 统一为无空格小写
        cur = bytes(b[o:o + len(bytes.fromhex(oh))]).hex()
        good = (cur == want)
        ok &= good
        print('  %08x  %-28s cur=%s  %s' % (va, desc, cur, 'OK' if good else 'MISMATCH! (期望 %s)' % want))
    if not ok:
        print()
        print('!! 字节不匹配, 已存在补丁或文件已改动 — 中止。')
        return False

    if not os.path.exists(BAK):
        open(BAK, 'wb').write(bytes(b))
        print()
        print('备份 ->', os.path.basename(BAK))

    for va, oh, nh, desc in PATCHES:
        o = va2off(va)
        b[o:o + len(bytes.fromhex(nh))] = bytes.fromhex(nh)

    open(P, 'wb').write(bytes(b))
    print()
    print('=== 打完补丁后反汇编 ===')
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.syntax = CS_OPT_SYNTAX_INTEL
    nb = bytes(b)
    for va, oh, nh, desc in PATCHES:
        o = va2off(va)
        for ins in md.disasm(nb[o:o + 12], va):
            print('  %08x  %-20s %s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str))
            if ins.address > va + 2:
                break
    print()
    print('已写入 3 处。跳关: 用 tools/make_coop10_save.py 生成 +0=10 的存档。')
    return True

if __name__ == '__main__':
    apply()
