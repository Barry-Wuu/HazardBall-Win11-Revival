# -*- coding: utf-8 -*-
"""反汇编 Hazard.exe 指定 VA 范围（capstone, 32bit）"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
B = open(P, 'rb').read()
IMG = 0x400000
SECT = [(0x1000, 0x1000, 0x42000, '.text'),
        (0x43000, 0x43000, 0x2000, '.rdata'),
        (0x45000, 0x45000, 0x2d000, '.data'),
        (0x72000, 0x72000, 0x13000, '.rsrc'),
        (0x9c000, 0x74000, 0x1000, '.theta')]

def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz, nm in SECT:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

def off2va(off):
    for sva, sraw, ssz, nm in SECT:
        if sraw <= off < sraw + ssz:
            return IMG + sva + (off - sraw)
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.syntax = CS_OPT_SYNTAX_INTEL

def dis(start_va, end_va):
    o = va2off(start_va)
    if o is None:
        print('bad va %08x' % start_va); return
    n = end_va - start_va
    code = B[o:o + n]
    out = []
    for ins in md.disasm(code, start_va):
        out.append('%08x  %-24s %s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str))
    return out

if __name__ == '__main__':
    a = int(sys.argv[1], 16)
    b = int(sys.argv[2], 16)
    for line in dis(a, b):
        print(line)
