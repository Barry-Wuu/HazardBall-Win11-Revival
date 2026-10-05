"""
永久禁用 Windows 辅助功能按键（StickyKeys / FilterKeys / ToggleKeys / MouseKeys）

起因：Hazard Ball 双人模式需要同时按住两个方向键控制两颗球，Windows 会把它
判成组合键，弹出粘滞键提示框打断操作。

Flags 位含义（Windows ACCESSIBILITY 约定，**反向语义**）：
    StickyKeys  : bit0 为 1 表示"粘滞键已关闭"
    FilterKeys  : bit0 为 1 表示"筛选键已关闭"
    ToggleKeys  : bit0 为 1 表示"切换键已关闭"
    MouseKeys   : bit0 为 1 表示"鼠标键已关闭"

实测本机原值bit0 全是 0，即四项**都处于开启状态**：
    StickyKeys  = 506  (0b...1010)
    FilterKeys  = 126  (0b...1110)
    ToggleKeys  = 62   (0b...1110)
    MouseKeys   = 62   (0b...1110)

所以「关闭」的正确写法是**把 bit0 置 1**，即 `原值 | 1` → 507 / 127 / 63 / 63。
其它位保持不动（它们是"热键/提示音"等细项，无需改）。

回退：把原值写回即可，见 --restore。
"""

import os
import sys
import time
import winreg

BASE = r'Control Panel\Accessibility'

# (注册表子键, 值名, 人类可读名)
ITEMS = [
    (r'\StickyKeys',        'Flags', '粘滞键 StickyKeys'),
    (r'\Keyboard Response', 'Flags', '筛选键 FilterKeys'),
    (r'\ToggleKeys',        'Flags', '切换键 ToggleKeys'),
    (r'\MouseKeys',         'Flags', '鼠标键 MouseKeys'),
]

BACKUP = r'D:\B++\WorkBuddy\hazard_hack\_accessibility_backup.txt'


def _off(v):
    """bit0 == 1 表示已关闭"""
    if v is None:
        return '?'
    return '已关闭' if (int(v) & 1) else '开启'


def read_all():
    out = {}
    for sub, val, _ in ITEMS:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, BASE + sub)
            v, _t = winreg.QueryValueEx(k, val)
            out[sub + '\\' + val] = v
            winreg.CloseKey(k)
        except (FileNotFoundError, OSError):
            out[sub + '\\' + val] = None
    return out


def write_all(values):
    for key, v in values.items():
        if v is None:
            continue
        sub, val = key.rsplit('\\', 1)
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, BASE + sub, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, val, 0, winreg.REG_SZ, str(v))
        winreg.CloseKey(k)


def show():
    print('=== Windows 辅助功能按键状态 ===')
    cur = read_all()
    for sub, val, name in ITEMS:
        v = cur.get(sub + '\\' + val)
        print('  %-22s Flags=%-6s %s' % (name, v, _off(v)))
    return cur


def disable():
    cur = read_all()
    with open(BACKUP, 'w', encoding='utf-8') as f:
        for k, v in cur.items():
            f.write('%s=%s\n' % (k, v))
    print('原值已备份 ->', BACKUP)
    print()

    for sub, val, name in ITEMS:
        old = cur.get(sub + '\\' + val)
        if old is None:
            print('  %-22s (注册表值不存在，跳过)' % name)
            continue
        new = int(old) | 1               # bit0 置 1 = 关闭
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, BASE + sub, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, val, 0, winreg.REG_SZ, str(new))
        winreg.CloseKey(k)
        print('  %-22s %s -> %d  (%s)' % (name, old, new, _off(new)))

    # 说明：这里**不再调SystemParametersInfoW 广播**。
    # 原因：SPI 编号里 GET/SET 交错（如 0x0033 是 SPI_GETSTICKYKEYS 而 SET 是 0x003B），
    # 传错结构体大小会直接 access violation 甚至段错误崩掉 Python 进程。
    # 注册表是这些设置的唯一持久化来源，系统在下次登录 / 切换辅助功能设置时会读取它，
    # 因此写完注册表即已"永久生效"，无需广播。
    print()
    print('已永久关闭 4 项辅助功能按键（写入 HKCU 注册表，重登后完全生效）。')


def restore():
    if not os.path.exists(BACKUP):
        print('找不到备份文件:', BACKUP)
        return
    vals = {}
    with open(BACKUP, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                vals[k] = v
    write_all(vals)
    print('已回退为备份中的原值。')
    show()


if __name__ == '__main__':
    import os
    if '--show' in sys.argv:
        show()
    elif '--restore' in sys.argv:
        restore()
    else:
        show()
        print()
        disable()
        print()
        show()