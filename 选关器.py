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
#
# 24 字节 = 6 × int32，实测字段布局（由 Hazard.exe 读档函数 0x4118C8 确认）：
#   +0   下一关关号        打通第 1 关 → 2
#   +4   lives（剩余生命）   0x4119FA 处 push 0x44B5A8 + fread 4 字节，
#                          运行时 lives 变量就是 [0x44B5A8]；满值实测为 4
#   +8   累计成绩           运行时 [0x44BC8C]（41 处引用，参与分数动画运算）
#   +12  校验位 A       ┐ 基准取自运行时内存，离线算不出合法值
#   +16  校验位 B       ┘ (需配合 exe 的跳过校验补丁)
#   +20  模式标识         冒险 = 1，双人 = 2
#
# 末位(模式标识)与两个校验位是定值；关号与 lives 可调。
ADV_TAIL = (4, 47573, -990800, -948794, 1)     # 末位 1 = 冒险模式
COOP_TAIL = (4, 68830, -990799, -948793, 2)    # 末位 2 = 双人模式

DEFAULT_LIVES = 4
LIVES_MIN, LIVES_MAX = 1, 99


def build_save(level, tail, lives=None):
    """构造存档。lives 为 None 时沿用 tail 里自带的值"""
    f = list(tail)
    if lives is not None:
        f[0] = int(lives)                    # +4 就是 lives
    return struct.pack('<i', level) + struct.pack('<5i', *f)


def read_ints(path):
    """读存档全部 6 个 int32; 读不到返回 None"""
    try:
        with open(path, 'rb') as f:
            data = f.read(24)
        if len(data) < 24:
            return None
        return struct.unpack_from('<6i', data, 0)
    except OSError:
        return None


def read_level(path):
    """读取存档里的关号; 读不到返回 None"""
    v = read_ints(path)
    return None if v is None else v[0]


def read_lives(path):
    """读取存档里的 lives（+4）; 读不到返回 None"""
    v = read_ints(path)
    return None if v is None else v[1]


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


def apply_save(mode, level, lives=None):
    """把指定模式切到指定关，可选同时改 lives。返回 (成功, 提示)"""
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
            f.write(build_save(level, tail, lives))
    except OSError as e:
        return False, '写入失败:\n%s' % e

    msg = '%s 已切到 level %d' % (label, level)
    if lives is not None:
        msg += '，lives = %d' % int(lives)
    return True, msg


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
        tk.Label(top, text='关卡选择 · 生命数', bg=BG, fg=SUB,
                 font=self.f_small).pack(anchor='w')

        self.status = tk.Label(root, text='', bg=PANEL, fg=NOW,
                               font=self.f_sec, anchor='w', padx=16, pady=10)
        self.status.pack(fill='x', padx=20, pady=(12, 4))

        # lives 设置行
        bar = tk.Frame(root, bg=PANEL)
        bar.pack(fill='x', padx=20, pady=(4, 0))
        tk.Label(bar, text='LIVES', bg=PANEL, fg=SUB,
                 font=self.f_small).pack(side='left', padx=(16, 8))
        self.lv_adv = self._lives_box(bar, 'adv')
        tk.Label(bar, text='双人', bg=PANEL, fg=SUB,
                 font=self.f_small).pack(side='left', padx=(20, 8))
        self.lv_coop = self._lives_box(bar, 'coop')

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

    def _lives_box(self, parent, mode):
        """一组 lives 微调按钮 + 数值显示"""
        frm = tk.Frame(parent, bg=PANEL)
        frm.pack(side='left')
        var = {'v': DEFAULT_LIVES}
        lbl = tk.Label(frm, text=str(DEFAULT_LIVES), bg=CARD, fg=TEXT,
                       font=self.f_sec, width=4, pady=1)

        def setv(d):
            v = max(LIVES_MIN, min(LIVES_MAX, var['v'] + d))
            var['v'] = v
            lbl.configure(text=str(v), bg=CARD_HI, fg='#ffffff')
            self.root.after(700, lambda: lbl.configure(bg=CARD, fg=TEXT))

        for d, txt in ((-1, '−'), (1, '+')):
            b = tk.Label(frm, text=txt, bg=CARD, fg=TEXT, font=self.f_sec,
                         width=2, cursor='hand2', pady=1)
            b.pack(side='left', padx=2)
            b.bind('<Button-1>', lambda e, dd=d: setv(dd))
        lbl.pack(side='left', padx=(4, 0))
        return var

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
        lives = (self.lv_adv if mode == 'adv' else self.lv_coop)['v']
        ok, msg = apply_save(mode, level, lives)
        if not ok:
            messagebox.showwarning('无法切换', msg, parent=self.root)
            return
        self.refresh()
        label = '冒险模式' if mode == 'adv' else '双人模式'
        messagebox.showinfo(
            '已切换',
            '%s  →  level %d　lives %d\n\n现在启动游戏, 主菜单选该模式 → RESUME GAME'
            % (label, level, lives),
            parent=self.root)

    def refresh(self):
        adv = read_ints(SAV_BARRY)
        coop = read_ints(SAV_2UP)
        self.status.configure(
            text='当前进度　冒险 %s (lives %s)　　双人 %s (lives %s)'
            % (self._fmt(None if adv is None else adv[0], ADV_COUNT),
               '-' if adv is None else adv[1],
               self._fmt(None if coop is None else coop[0], COOP_COUNT),
               '-' if coop is None else coop[1]))
        self._mark(self.adv_cards, None if adv is None else adv[0])
        self._mark(self.coop_cards, None if coop is None else coop[0])

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