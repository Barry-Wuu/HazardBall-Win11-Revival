# -*- coding: utf-8 -*-
"""
把 Hazard Ball 窗口钉到屏幕左上角, 使客户区原点 = (0,0)。

诊断用途: 证明"游戏硬编码假设客户区在屏幕原点(0,0)"这一根因。
游戏 CreateWindowExA 传入的 X/Y 本就是 0, 即它期望窗口在 (0,0)。
之前窗口被 dgVookie CenterAppWindow=true 居中到 (401,241), 导致
  - clamp 边界 [25,600]x[25,440] 整体落在窗口左侧 -> 光标被锁在窗口外
  - 菜单命中检测同样用 (0,0) 假设 -> 点哪都偏

用法:
  python pin_window.py          # 常驻, 每 0.3s 纠正一次
  python pin_window.py --once   # 只纠正一次
  python pin_window.py --show   # 只打印当前几何
"""
import ctypes, ctypes.wintypes as wt, time, sys

u = ctypes.windll.user32
k = ctypes.windll.kernel32

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

def find_window():
    """找 Hazard 主窗口: class='winclass' 且客户区约 638x478 (640x480 外框)"""
    EnumWindowsProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    hwnds = []
    u.EnumWindows(EnumWindowsProc(lambda h, l: (hwnds.append(h), True)[1]), 0)
    for hwnd in hwnds:
        if not u.IsWindowVisible(hwnd):
            continue
        cls = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(hwnd, cls, 256)
        if cls.value != 'winclass':
            continue
        cr = wt.RECT()
        u.GetClientRect(hwnd, ctypes.byref(cr))
        # 640x480 窗口, 客户区 638x478
        if 600 <= cr.right <= 660 and 450 <= cr.bottom <= 500:
            return hwnd
        # 兜底: 类名+尺寸都对但上面没匹配时, 打印出来看
    return None

def geometry(hwnd):
    r = wt.RECT(); u.GetWindowRect(hwnd, ctypes.byref(r))
    cr = wt.RECT(); u.GetClientRect(hwnd, ctypes.byref(cr))
    org = POINT(0, 0); u.ClientToScreen(hwnd, ctypes.byref(org))
    return r, cr, org

def pin_once(hwnd):
    r, cr, org = geometry(hwnd)
    dx = -org.x          # 让客户区原点移到 0
    dy = -org.y
    if dx == 0 and dy == 0:
        return False
    # SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED
    u.SetWindowPos(hwnd, None, r.left + dx, r.top + dy, 0, 0,
                   0x0001 | 0x0004 | 0x0010 | 0x0020)
    return True

def show(hwnd):
    r, cr, org = geometry(hwnd)
    p = POINT(); u.GetCursorPos(ctypes.byref(p))
    print('hwnd=0x%x' % hwnd)
    print('  winRect  = (%d,%d)-(%d,%d)  %dx%d' % (r.left, r.top, r.right, r.bottom,
                                                    r.right-r.left, r.bottom-r.top))
    print('  client   = %dx%d  origin=(%d,%d)' % (cr.right, cr.bottom, org.x, org.y))
    print('  clamp 期望区间(窗口内): X[%d,%d] Y[%d,%d]' % (org.x+25, org.x+600, org.y+25, org.y+440))
    print('  OS 光标  = (%d,%d)  %s' % (p.x, p.y,
          '在窗口内' if (org.x <= p.x <= org.x+cr.right and org.y <= p.y <= org.y+cr.bottom) else '*** 在窗口外 ***'))
    print('  屏幕     = %dx%d' % (u.GetSystemMetrics(0), u.GetSystemMetrics(1)))

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    hwnd = find_window()
    if not hwnd:
        print('!! 未找到 Hazard 主窗口 (winclass 640x480) — 游戏是否在运行?')
        sys.exit(1)
    if mode == '--show':
        show(hwnd); sys.exit(0)
    if mode == '--once':
        moved = pin_once(hwnd)
        print('已纠正' if moved else '已在 (0,0), 无需移动')
        show(hwnd); sys.exit(0)
    # 常驻
    print('常驻钉住窗口到 (0,0), 每 0.3s 纠正一次... Ctrl+C 退出')
    n = 0
    while True:
        h = find_window()
        if h:
            if pin_once(h):
                n += 1
                if n <= 3 or n % 20 == 0:
                    print('  [%d] 已纠正 -> 客户区原点 (0,0)' % n)
        time.sleep(0.3)
