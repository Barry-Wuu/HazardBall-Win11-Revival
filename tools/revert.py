# -*- coding: utf-8 -*-
"""一键还原 Hazard Ball：还原 Hazard.exe（从 .orig）与 coop10.map（从 .orig）"""
import os, shutil

PAIRS = [
    (r'D:\Hazard Ball\Hazard.exe.orig',   r'D:\Hazard Ball\Hazard.exe'),
    (r'D:\Hazard Ball\DATA\coop10.map.orig', r'D:\Hazard Ball\DATA\coop10.map'),
]

for src, dst in PAIRS:
    if not os.path.exists(src):
        print('缺少备份:', src); continue
    shutil.copy2(src, dst)
    print('已还原: %s  <-  %s' % (dst, src))
print('完成。')
