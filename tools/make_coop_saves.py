# -*- coding: utf-8 -*-
"""
Hazard Ball — coop 关卡存档生成器 (2UP GAME)

背景
----
双人模式 (2UP GAME) 没有选关菜单, 只有 RESUME GAME 读档;
coop 关卡进度记录在 DATA\\SAVE\\2UP GAME.sav 的 +0 字段(已完成关数+1)。
原版 exe 对该存档做双重校验(0x411990), 基准取自运行时内存, 离线无法算出
合法存档 -> 手改必被判定无效并回退到第 1 关。
已用 patch_skip_savecheck.py 跳过校验, 因此可直接生成任意关号的存档。

本工具生成 coop1 ~ coop10 共 10 份存档, 并提供切换脚本。

用法
----
  python make_coop_saves.py gen      # 生成 10 份到 saves/ 目录
  python make_coop_saves.py use 7    # 切换到 coop7
  python make_coop_saves.py list     # 列出可用存档
"""
import os, struct, shutil, sys, time

GAME = r'D:\Hazard Ball'
SAVE = os.path.join(GAME, 'DATA', 'SAVE')
CUR = os.path.join(SAVE, '2UP GAME.sav')
BANK = os.path.join(SAVE, 'saves')
TOTAL_LEVELS = 10

# 基准模板 (来自实测: 打完第2关后的真实存档, 仅关号字段有效)
# +0 关号 | +4 ? | +8 成绩 | +12 校验A | +16 校验B | +20 ?
# 校验位已无关紧要(校验被跳过), 保留真实值以维持文件形态一致
TEMPLATE = struct.pack('<6i', 3, 4, 68830, -990799, -948793, 2)


def name(level):
    return 'coop%02d.sav' % level


def gen():
    os.makedirs(BANK, exist_ok=True)
    print('生成 coop1 ~ coop%d 存档 -> %s' % (TOTAL_LEVELS, BANK))
    print()
    print('  %-14s %-6s %s' % ('文件', '关号', '说明'))
    for lv in range(1, TOTAL_LEVELS + 1):
        d = bytearray(TEMPLATE)
        struct.pack_into('<i', d, 0, lv)          # +0 关号
        struct.pack_into('<i', d, 20, 2)           # +20 保持原值
        p = os.path.join(BANK, name(lv))
        open(p, 'wb').write(bytes(d))
        print('  %-14s %-6d %s' % (name(lv), lv,
              '下一关 = coop%d' % lv if lv < TOTAL_LEVELS else 'coop10 (TEMPLE OF DOOM)'))
    print()
    print('共 %d 份。切换: python make_coop_saves.py use <关号 1-10>' % TOTAL_LEVELS)


def use(level):
    if not (1 <= level <= TOTAL_LEVELS):
        print('关号须在 1..%d' % TOTAL_LEVELS)
        return
    src = os.path.join(BANK, name(level))
    if not os.path.exists(src):
        print('找不到存档:', src)
        print('请先运行: python make_coop_saves.py gen')
        return
    if os.path.exists(CUR):
        bak = CUR + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
        shutil.copy2(CUR, bak)
        print('当前存档已备份 ->', os.path.basename(bak))
    shutil.copy2(src, CUR)
    d = open(CUR, 'rb').read()
    print()
    print('已切换: 当前存档关号 = %d (下一关 = coop%d)'
          % (struct.unpack_from('<i', d, 0)[0], struct.unpack_from('<i', d, 0)[0]))


def list_saves():
    if not os.path.isdir(BANK):
        print('尚未生成。请先运行: python make_coop_saves.py gen')
        return
    cur = None
    if os.path.exists(CUR):
        cur = struct.unpack_from('<i', open(CUR, 'rb').read(), 0)[0]
    print('存档目录:', BANK)
    print()
    print('  %-14s %-6s %s' % ('文件', '关号', '状态'))
    for lv in range(1, TOTAL_LEVELS + 1):
        p = os.path.join(BANK, name(lv))
        if not os.path.exists(p):
            print('  %-14s %-6d (缺失)' % (name(lv), lv))
            continue
        d = struct.unpack_from('<i', open(p, 'rb').read(), 0)[0]
        mark = '  <== 当前生效' if cur == d else ''
        print('  %-14s %-6d%s' % (name(lv), d, mark))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
    elif sys.argv[1] == 'gen':
        gen()
    elif sys.argv[1] == 'use':
        use(int(sys.argv[2]))
    elif sys.argv[1] == 'list':
        list_saves()
    else:
        print(__doc__)
