# -*- coding: utf-8 -*-
"""在 .text 中查找对指定字符串 VA 的引用（Delphi 绝对地址）"""
import struct, re, sys

p = r'D:\Hazard Ball\Hazard.exe'
b = open(p, 'rb').read()

IMG = 0x400000
# .text
TEXT_VA, TEXT_RAW, TEXT_SIZE = 0x1000, 0x1000, 0x42000
# .rdata (va == raw)
RDATA_VA, RDATA_RAW = 0x43000, 0x43000

TARGETS = {
    'TILT': 0x464ec,
    'TIP_LIFT_TO_JUMP': 0x46554,
    'USB_TILT_NOT_DETECTED': 0x46b30,
    'WITH_3AXIS': 0x46ad4,
    'FAILED_SET_AXIS_MODE': 0x45660,
    'JOYSTICK_ENABLED': 0x45dfc,
    'JOYSTICK_DISABLED': 0x45e10,
    'PERFECT_JUMP': 0x4571c,
    'GOOD_JUMP': 0x4572c,
    'NICE_JUMP': 0x4576c,
    'TILTSENSOR_TXT': 0x46438,
    'TILT_AND_ROLL': 0x46bec,
    'SPACEBAR_TO_RESUME': 0x4759c,
    'tilt_map_fmt': 0x465d0,
    'jump_wav': 0x45fb8,
}

text = b[TEXT_RAW:TEXT_RAW + TEXT_SIZE]

def va2off(va):
    rva = va - IMG
    if TEXT_VA <= rva < TEXT_VA + TEXT_SIZE:
        return TEXT_RAW + (rva - TEXT_VA)
    if RDATA_VA <= rva < RDATA_VA + 0x2000:
        return RDATA_RAW + (rva - RDATA_VA)
    return None

for name, rva in TARGETS.items():
    va = IMG + rva
    pat = struct.pack('<I', va)
    hits = [m.start() for m in re.finditer(re.escape(pat), text)]
    print('%-24s RVA=%05x VA=%08x  refs=%d' % (name, rva, va, len(hits)))
    for h in hits[:12]:
        foff = TEXT_RAW + h
        print('     file_off=%08x  va=%08x  bytes=%s' % (foff, va2off and (IMG + TEXT_VA + (foff - TEXT_RAW)), b[foff - 2:foff + 6].hex(' ')))
