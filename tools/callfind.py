# -*- coding: utf-8 -*-
"""查找 call/jmp 目标为指定 VA 的位置，并打印上下文"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
B = open(P, 'rb').read()
IMG = 0x400000
SECS = [(0x1000, 0x1000, 0x42000), (0x43000, 0x43000, 0x2000), (0x45000, 0x45000, 0x2d000),
        (0x72000, 0x72000, 0x13000), (0x9c000, 0x74000, 0x1000)]

def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz in SECS:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

def off2va(off):
    for sva, sraw, ssz in SECS:
        if sraw <= off < sraw + ssz:
            return IMG + sva + (off - sraw)
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.syntax = CS_OPT_SYNTAX_INTEL
CODE = B[0x1000:0x1000 + 0x42000]
BASE = IMG + 0x1000

def calls_to(target):
    return [ins.address for ins in md.disasm(CODE, BASE)
            if ins.mnemonic in ('call', 'jmp') and ins.op_str.lower() == '0x%x' % target]

def ctx(va, before=40, after=60):
    o = va2off(va)
    s = o - before
    lines = list(md.disasm(B[s:o + after], off2va(s)))
    for ins in lines:
        mark = ' <<<' if ins.address == va else ''
        print('   %08x  %-18s %s %s%s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str, mark))

if __name__ == '__main__':
    for a in sys.argv[1:]:
        t = int(a, 16)
        cs = calls_to(t)
        print('### call/jmp -> %08x   count=%d' % (t, len(cs)))
        for c in cs:
            print('  at %08x' % c)
            ctx(c)
        print()
