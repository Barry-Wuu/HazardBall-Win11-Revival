# -*- coding: utf-8 -*-
"""提取 Hazard.exe 字符串，按关键词过滤"""
import re, sys

p = r'D:\Hazard Ball\Hazard.exe'
b = open(p, 'rb').read()

def strings(buf, minlen=4):
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, buf):
        out.append((m.start(), m.group().decode('latin1')))
    # UTF-16LE
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}' % minlen, buf):
        out.append((m.start(), m.group().decode('utf-16le')))
    return out

S = strings(b)
KW = ['TILT', 'tilt', 'JUMP', 'jump', 'AXIS', 'axis', 'JOY', 'joy', 'GAMEPAD', 'gamepad',
      'PAD', 'DINPUT', 'dinput', 'DEVICE', 'device', 'SPACE', 'SPACEBAR', 'CONTROLLER',
      'SIXAXIS', 'SENSOR', 'sensor', 'ACCEL', 'GYRO', 'BALL', 'SETUP']
seen = set()
for off, s in S:
    up = s
    if any(k in up for k in KW):
        key = (off, s)
        if key in seen:
            continue
        seen.add(key)
        if 3 <= len(s) <= 90:
            print('%08x  %s' % (off, s))
