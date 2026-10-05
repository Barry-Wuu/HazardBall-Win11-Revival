#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hazard Ball - 关卡选择器

原版没有选关菜单：冒险模式(20 关) 与双人模式(10 关) 只能逐关通关推进。
本工具直接改写 DATA/SAVE 下的存档首字段(+0 = 下一关关号), 跳到任意关。

存档结构(实测 BARRY.sav / 2UP GAME.sav 同构, 24 字节 = 6 x int32):
    +0   下一关关号        打通第 1 关 -> 2
    +4   固定 4
    +8   累计成绩
    +12  校验位 A   ┐ 基准取自运行时内存, 离线算不出合法值
    +16  校验位 B   ┘ (需配合 exe 的跳过校验补丁)
    +20  模式标识   冒险 = 1 / 双人 = 2

用法: 双击本文件(或打包好的 exe) -> 点关卡 -> 启动游戏 RESUME GAME
"""

import os
import sys
import struct
import shutil
import ctypes
import ctypes.wintypes as wt

try:
    import tkinter as tk
    from tkinter import messagebox, font
except ImportError:
    sys.exit('需要 Python 3 才能运行本工具(或使用打包好的 exe)。')


# ---------------------------------------------------------------- 路径

if getattr(sys, 'frozen', False):
    BASE = os.path.dirname(sys.executable)          # 打包后 exe 同目录
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

SAVE_DIR = os.path.join(BASE, 'DATA', 'SAVE')
SAV_BARRY = os.path.join(SAVE_DIR, 'BARRY.sav')
SAV_2UP = os.path.join(SAVE_DIR, '2UP GAME.sav')

ADV_COUNT = 20
COOP_COUNT = 10


# ---------------------------------------------------------------- 存档构造

# 各字段固定值(实测同模式内除 +0 外完全一致)
ADV_TAIL = (4, 47573, -990800, -948794, 1)     # 末位 1 = 冒险模式
COOP_TAIL = (4, 68830, -990799, -948793, 2)    # 末位 2 = 双人模式


def build_save(level, tail):
    """构造指定关号的 24 字节存档"""
    return struct.pack('<i', level) + struct.pack('<5i', *tail)


def read_level(path):
    """读取存档里的关号; 读不到返回 None"""
    try:
        with open(path, 'rb') as f:
            data = f.read(4)
        if len(data) < 4:
            return None
        return struct.unpack_from('<i', data, 0)[0]
    except OSError:
        return None


def game_running():
    """检测 hazard.exe 是否在运行(运行时存档可能被占用)"""
    TH32CS_SNAPPROCESS = 0x2

    class PE32(ctypes.Structure):
        _fields_ = [
            ('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
            ('th32ProcessID', wt.DWORD),
            ('th32DefaultHeapID', ctypes.POINTER(ctypes.c_ulong)),
            ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD),
            ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', ctypes.c_long),
            ('dwFlags', wt.DWORD), ('szExeFile', ctypes.c_char * 260),
        ]

    snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return False
    try:
        pe = PE32()
        pe.dwSize = ctypes.sizeof(pe)
        if ctypes.windll.kernel32.Process32First(snap, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.decode('latin1').lower() == 'hazard.exe':
                    return True
                if not ctypes.windll.kernel32.Process32Next(snap, ctypes.byref(pe)):
                    break
    finally:
        ctypes.windll.kernel32.CloseHandle(snap)
    return False


def apply_save(mode, level):
    """把指定模式切到指定关。返回 (成功, 提示)"""
    if mode == 'adv':
        target, tail, label = SAV_BARRY, ADV_TAIL, '冒险模式'
    else:
        target, tail, label = SAV_2UP, COOP_TAIL, '双人模式'

    if not os.path.isfile(target):
        return False, ('缺少存档文件:\n%s\n\n'
                       '请先在游戏里打通该模式的第一关, 生成存档后再用本工具。'
                       % os.path.basename(target))

    if game_running():
        return False, '游戏正在运行。\n\n请完全退出 Hazard Ball 后再切换关卡。'

    try:                                    # 备份当前存档
        if os.path.isfile(target):
            shutil.copy2(target, target + '.bak')
    except OSError:
        pass

    try:
        with open(target, 'wb') as f:
            f.write(build_save(level, tail))
    except OSError as e:
        return False, '写入失败:\n%s' % e

    return True, '%s 已切到 level %d' % (label, level)


# ---------------------------------------------------------------- 界面

BG = '#161a22'
PANEL = '#222835'
CARD = '#333c4e'
CARD_HI = '#4a7fd4'
NOW = '#4ad98a'
TEXT = '#e8ecf4'
SUB = '#8e9cb3'
FONT = 'Microsoft YaHei UI'


class App:
    def __init__(self, root):
        self.root = root
        root.title('Hazard Ball - 关卡选择')
        root.configure(bg=BG)
        root.resizable(False, False)

        self.f_title = font.Font(family=FONT, size=18, weight='bold')
        self.f_sec = font.Font(family=FONT, size=11, weight='bold')
        self.f_num = font.Font(family=FONT, size=20, weight='bold')
        self.f_small = font.Font(family=FONT, size=9)
        self.f_now = font.Font(family=FONT, size=20, weight='bold')

        self.adv_cards = {}
        self.coop_cards = {}

        self._build()
        self.refresh()

    # ---------------------------------------------------------- 构建

    def _build(self):
        root = self.root

        top = tk.Frame(root, bg=BG)
        top.pack(fill='x', padx=20, pady=(18, 2))
        tk.Label(top, text='HAZARD BALL', bg=BG, fg=TEXT,
                 font=self.f_title).pack(anchor='w')
        tk.Label(top, text='关卡选择', bg=BG, fg=SUB,
                 font=self.f_small).pack(anchor='w')

        self.status = tk.Label(root, text='', bg=PANEL, fg=NOW,
                               font=self.f_sec, anchor='w', padx=16, pady=10)
        self.status.pack(fill='x', padx=20, pady=(12, 4))

        self._section(root, 'ADVENTURE', '冒险模式', ADV_COUNT,
                      'adv', self.adv_cards, 5)
        self._section(root, 'CO-OPERATIVE', '双人模式', COOP_COUNT,
                      'coop', self.coop_cards, 5)

        foot = tk.Frame(root, bg=BG)
        foot.pack(fill='x', padx=20, pady=(8, 18))
        tk.Label(foot, bg=BG, fg=SUB, font=self.f_small, justify='left',
                 text=('切换后启动游戏 → 主菜单选对应模式 → RESUME GAME\n'
                       '写入前自动备份为 *.sav.bak　·　选 1 即从第一关重新开始'
                       )).pack(anchor='w')

    def _section(self, parent, en, cn, count, mode, store, cols):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(fill='x', padx=20, pady=8)

        head = tk.Frame(box, bg=PANEL)
        head.pack(fill='x', padx=16, pady=(12, 0))
        tk.Label(head, text=en, bg=PANEL, fg=SUB,
                 font=self.f_small).pack(side='left')
        tk.Label(head, text='%s · %d 关' % (cn, count), bg=PANEL, fg=TEXT,
                 font=self.f_sec).pack(side='left', padx=(10, 0))

        grid = tk.Frame(box, bg=PANEL)
        grid.pack(padx=16, pady=(8, 14))

        for i in range(1, count + 1):
            r, c = divmod(i - 1, cols)
            card = tk.Label(grid, text=str(i), bg=CARD, fg=TEXT,
                            font=self.f_num, width=6, height=1,
                            cursor='hand2', padx=4, pady=10)
            card.grid(row=r, column=c, padx=5, pady=5)
            card.bind('<Button-1>', lambda e, m=mode, lv=i: self.on_click(m, lv))
            card.bind('<Enter>', lambda e, w=card: self._hover(w, True))
            card.bind('<Leave>', lambda e, w=card: self._hover(w, False))
            store[i] = card

    @staticmethod
    def _hover(card, on):
        card.configure(bg=CARD_HI if on else CARD,
                       fg='#ffffff' if on else TEXT)

    # ---------------------------------------------------------- 交互

    def on_click(self, mode, level):
        ok, msg = apply_save(mode, level)
        if not ok:
            messagebox.showwarning('无法切换', msg, parent=self.root)
            return
        self.refresh()
        messagebox.showinfo(
            '已切换',
            '%s  →  level %d\n\n现在启动游戏, 主菜单选该模式 → RESUME GAME'
            % (msg.split(' 已切到 ')[0], level),
            parent=self.root)

    def refresh(self):
        cur_adv = read_level(SAV_BARRY)
        cur_coop = read_level(SAV_2UP)
        self.status.configure(text='当前进度　冒险 %s　　双人 %s'
                              % (self._fmt(cur_adv, ADV_COUNT),
                                 self._fmt(cur_coop, COOP_COUNT)))
        self._mark(self.adv_cards, cur_adv)
        self._mark(self.coop_cards, cur_coop)

    @staticmethod
    def _fmt(level, total):
        if level is None:
            return '无存档'
        if 1 <= level <= total:
            return 'level %d' % level
        return 'level %d(越界)' % level

    def _mark(self, store, current):
        for lv, card in store.items():
            if lv == current:
                card.configure(bg=NOW, fg='#0d1a10', font=self.f_now)
            else:
                card.configure(bg=CARD, fg=TEXT, font=self.f_num)


def main():
    if not os.path.isdir(SAVE_DIR):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            '找不到存档目录',
            '未找到:\n%s\n\n请把本工具放在 Hazard Ball 游戏目录里再运行。' % SAVE_DIR)
        return

    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()