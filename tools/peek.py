# -*- coding: utf-8 -*-
"""hexdump + GUID 格式化"""
import struct, sys, uuid

P = r'D:\Hazard Ball\Hazard.exe'
B = open(P, 'rb').read()
IMG = 0x400000
SECS = [(0x1000, 0x1000, 0x42000, '.text'), (0x43000, 0x43000, 0x2000, '.rdata'),
        (0x45000, 0x45000, 0x2d000, '.data'), (0x72000, 0x72000, 0x13000, '.rsrc'),
        (0x9c000, 0x74000, 0x1000, '.theta')]

def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz, nm in SECS:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

def dword(va):
    return struct.unpack_from('<I', B, va2off(va))[0]

def guid(va):
    o = va2off(va)
    d1, d2, d3 = struct.unpack_from('<IHH', B, o)
    d4 = B[o + 8:o + 10]
    d5 = B[o + 10:o + 16]
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, d4.hex().upper(), d5.hex().upper())

def dump(va, n):
    o = va2off(va)
    for i in range(0, n, 16):
        chunk = B[o + i:o + i + 16]
        print('%08x  %-47s  %s' % (va + i, chunk.hex(' '), ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)))

def datfmt(va, name):
    print('--- DIDATAFORMAT @ %08x (%s) ---' % (va, name))
    dwSize, dwObjSize, dwFlags, dwDataSize, dwNumObjs, rgodf = struct.unpack_from('<IIIIII', B, va2off(va))
    print('  dwSize=%d dwObjSize=%d dwFlags=%d(%s) dwDataSize=%d dwNumObjs=%d rgodf=%08x'
          % (dwSize, dwObjSize, dwFlags, 'ABS' if dwFlags == 1 else ('REL' if dwFlags == 2 else '?'), dwDataSize, dwNumObjs, rgodf))
    ro = va2off(rgodf)
    for i in range(dwNumObjs):
        pguid, dwOfs, dwType, dwFlags2 = struct.unpack_from('<IIII', B, ro + i * 16)
        g = guid(pguid) if pguid else '(no guid)'
        CONST = {0x04: 'GUID_XAxis', 0x08: 'GUID_YAxis', 0x0c: 'GUID_ZAxis', 0x10: 'GUID_RxAxis',
                 0x14: 'GUID_RyAxis', 0x18: 'GUID_RzAxis', 0x1c: 'GUID_Slider', 0x20: 'GUID_Button',
                 0x24: 'GUID_POV', 0x28: 'GUID_Unknown'}
        gname = CONST.get(pguid - 0x443000 if pguid else 0, g)
        print('   [%d] ofs=0x%02x type=0x%08x flags=0x%08x  pguid=%s' % (i, dwOfs, dwType, dwFlags2, g))

if __name__ == '__main__':
    for v in [0x443540, 0x443550, 0x443600, 0x4434e0, 0x443510, 0x4434f8, 0x443500]:
        print('GUID @ %08x = %s' % (v, guid(v)))
    print()
    dump(0x4434e0, 0x60)
    print()
    for v in [0x4434f8, 0x443510]:
        datfmt(v, hex(v))
