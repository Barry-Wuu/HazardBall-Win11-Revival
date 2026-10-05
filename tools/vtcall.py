# -*- coding: utf-8 -*-
"""扫描 .text 中的间接调用 call dword ptr [reg+off]，统计间接 vtable 调用"""
import re, sys, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
B = open(P, 'rb').read()
IMG = 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.syntax = CS_OPT_SYNTAX_INTEL
CODE = B[0x1000:0x1000 + 0x42000]

pat = re.compile(rb'call dword ptr \[(e[a-d]x|e[sd]i|e[bp]p) \+ (0x[0-9a-f]+)\]')
dump = sys.argv[1] if len(sys.argv) > 1 else None
cnt = collections.Counter()
for ins in md.disasm(CODE, IMG + 0x1000):
    if ins.mnemonic == 'call' and ins.op_str.startswith('dword ptr ['):
        cnt[ins.op_str] += 1
        if dump:
            print('%08x  %s' % (ins.address, ins.op_str))
if not dump:
    for k, v in cnt.most_common():
        print('%4d  %s' % (v, k))
