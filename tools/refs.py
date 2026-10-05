# -*- coding: utf-8 -*-
"""查找对任意 VA 的引用，并在每个引用点附近反汇编"""
import struct, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
B = open(P, 'rb').read()
IMG = 0x400000
SECT = [(0x1000, 0x1000, 0x42000, '.text'), (0x43000, 0x43000, 0x2000, '.rdata'),
        (0x45000, 0x45000, 0x2d000, '.data'), (0x72000, 0x72000, 0x13000, '.rsrc'),
        (0x9c000, 0x74000, 0x1000, '.theta')]

def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz, nm in SECT:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.syntax = CS_OPT_SYNTAX_INTEL
TEXT = B[0x1000:0x1000 + 0x42000]

def find(va, show=3, before=16, after=24):
    pat = struct.pack('<I', va)
    hits = [m.start() for m in re.finditer(re.escape(pat), TEXT)]
    print('### VA=%08x  refs=%d' % (va, len(hits)))
    for h in hits:
        foff = 0x1000 + h
        ins_va = IMG + 0x1000 + h
        s = max(0x1000, foff - before)
        code = B[s:foff + after]
        print('  -- file_off=%08x (ref va=%08x)' % (foff, ins_va))
        for ins in md.disasm(code, IMG + s):
            mark = ' <<<' if ins.address <= ins_va < ins.address + ins.size else ''
            print('     %08x  %s %s%s' % (ins.address, ins.mnemonic, ins.op_str, mark))
    print()

if __name__ == '__main__':
    for a in sys.argv[1:]:
        find(int(a, 16))
