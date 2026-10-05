# -*- coding: utf-8 -*-
"""
只回退「鼠标/窗口 clamp」补丁，保留空格跳跃补丁。
用于 A/B 对比：确认分身问题是否由 clamp 造成。
Hazard.exe.preclamp = 注入 clamp 补丁之前的状态（含跳跃补丁，不含 clamp）。
"""
import os, shutil

SRC = r'D:\Hazard Ball\Hazard.exe.preclamp'
DST = r'D:\Hazard Ball\Hazard.exe'

if not os.path.exists(SRC):
    print('缺少备份:', SRC)
else:
    shutil.copy2(SRC, DST)
    print('已回退 clamp 补丁（保留跳跃补丁）:')
    print('  %s  <-  %s' % (DST, SRC))
