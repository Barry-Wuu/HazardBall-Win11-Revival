# -*- coding: utf-8 -*-
"""Hazard.exe 侦察：PE 信息 + 关键字符串"""
import struct, re, sys, os

p = r'D:\Hazard Ball\Hazard.exe'
b = open(p, 'rb').read()
print('size', len(b))

# --- PE 基本信息 ---
e_lfanew = struct.unpack_from('<I', b, 0x3c)[0]
print('PE sig', b[e_lfanew:e_lfanew + 4])
machine, nsec, tstamp = struct.unpack_from('<HHI', b, e_lfanew + 4)
print('machine %04x  sections %d  timestamp %d' % (machine, nsec, tstamp))
opt = e_lfanew + 24
magic = struct.unpack_from('<H', b, opt)[0]
print('opt magic %04x (%s)' % (magic, 'PE32' if magic == 0x10b else 'PE32+'))
imagebase = struct.unpack_from('<I', b, opt + 28)[0]
print('imagebase %08x' % imagebase)

# sections
sec_off = opt + (224 if magic == 0x10b else 240)
secs = []
for i in range(nsec):
    o = sec_off + i * 40
    name = b[o:o + 8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', b, o + 8)
    secs.append((name, vaddr, vsize, rawptr, rawsize))
    print('sec %-8s va=%08x vsize=%x raw=%08x rawsize=%x' % (name, vaddr, vsize, rawptr, rawsize))

# --- imports ---
def rva2off(rva):
    for name, va, vs, rp, rs in secs:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va)
    return None

dd = opt + (96 if magic == 0x10b else 112)
imp_rva, imp_sz = struct.unpack_from('<II', b, dd + 8)
print('import dir rva=%x' % imp_rva)
off = rva2off(imp_rva)
print('--- imports ---')
while True:
    oft, tstamp2, fchain, name_rva, first_thunk = struct.unpack_from('<IIIII', b, off)
    if name_rva == 0:
        break
    no = rva2off(name_rva)
    dll = b[no:b.index(b'\x00', no)].decode('latin1')
    funcs = []
    fo = rva2off(oft or first_thunk)
    k = 0
    while True:
        ent = struct.unpack_from('<I', b, fo + k * 4)[0]
        if ent == 0:
            break
        if ent & 0x80000000:
            funcs.append('ord#%d' % (ent & 0xffff))
        else:
            fn = rva2off(ent)
            funcs.append(b[fn:b.index(b'\x00', fn)].decode('latin1'))
        k += 1
    print('  %-16s %s' % (dll, ', '.join(funcs) if len(funcs) < 30 else '%d funcs' % len(funcs)))
    if dll.lower().startswith(('dinput', 'd3d', 'ddraw', 'xinput', 'winmm', 'user32')):
        print('     ->', ', '.join(funcs))
    off += 20
