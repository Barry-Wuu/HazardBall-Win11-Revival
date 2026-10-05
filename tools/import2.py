# -*- coding: utf-8 -*-
"""精确解析 Hazard.exe 导入表 (含 IAT 地址)"""
import struct

P = r'D:\Hazard Ball\Hazard.exe'
b = open(P, 'rb').read()
IMG = 0x400000
e = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, e + 6)[0]
opt = e + 24
magic = struct.unpack_from('<H', b, opt)[0]
sec_off = opt + (224 if magic == 0x10b else 240)
SECT = []
for i in range(nsec):
    o = sec_off + i * 40
    name = b[o:o + 8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', b, o + 8)
    SECT.append((name, vaddr, vsize, rawptr, rawsize))

def rva2off(rva):
    for nm, va, vs, rp, rs in SECT:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

dd = opt + (96 if magic == 0x10b else 112)
imp_rva, imp_sz = struct.unpack_from('<II', b, dd + 8)
off = rva2off(imp_rva)
print('%-16s %-10s %-10s %s' % ('DLL', 'IAT_RVA', 'OFT_RVA', 'FUNCS'))
while True:
    oft, ts, fc, name_rva, first_thunk = struct.unpack_from('<IIIII', b, off)
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    dll = b[no:b.index(b'\x00', no)].decode('latin1')
    src = oft or first_thunk
    fo = rva2off(src)
    funcs = []
    k = 0
    while True:
        ent = struct.unpack_from('<I', b, fo + k * 4)[0]
        if ent == 0:
            break
        if ent & 0x80000000:
            funcs.append('ord#%d' % (ent & 0xffff))
        else:
            fn = rva2off(ent)
            nm = b[fn + 2:b.index(b'\x00', fn + 2)].decode('latin1')
            funcs.append(nm)
        k += 1
    iat_va = IMG + first_thunk
    print('%-16s %08x  %08x  %d funcs' % (dll, first_thunk, src, len(funcs)))
    if dll.lower() in ('dinput.dll', 'ddraw.dll', 'dsound.dll', 'winmm.dll'):
        for i, f in enumerate(funcs):
            print('      [%2d] IAT=%08x  %s' % (i, iat_va + i * 4, f))
    off += 20
