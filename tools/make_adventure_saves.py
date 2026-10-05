# -*- coding: utf-8 -*-
"""
Hazard Ball — 冒险模式 (ADVENTURE) 关卡存档生成器

存档结构 (实测 BARRY.sav, 与 2UP GAME.sav 同格式)
    24 字节 = 6 x int32
    +0   下一关关号 (打通第1关 -> 2)
    +4   固定 4
    +8   累计成绩
    +12  校验位 A     ┐ 校验被 patch_skip_savecheck.py 跳过,
    +16  校验位 B     ┘ 离线无法算出合法值, 故原样保留
    +20  模式标识 (冒险=1, 2UP=2)

关卡: DATA\\level1.map .. level20.map 共 20 关

用法
----
  python make_adventure_saves.py gen     # 生成 20 份到 saves_adv/
  python make_adventure_saves.py use 15  # 切到第 15 关
  python make_adventure_saves.py list    # 列出全部
"""
import os, struct, shutil, sys, time

GAME = r'D:\Hazard Ball'
SAVE = os.path.join(GAME, 'DATA', 'SAVE')
CUR = os.path.join(SAVE, 'BARRY.sav')
BANK = os.path.join(SAVE, 'saves_adv')
TOTAL = 20
MODE_ADV = 1

LEVELS = {
    1: 'MEMORIES', 2: 'BACKLASH', 3: 'DESERT TOWER', 4: 'HEAT WAVE',
    5: 'SWAMP OUTPOST', 6: 'ELEMENTAL RACE', 7: 'FLOODED CITADEL',
    8: 'ABANDONED STONGHOLD', 9: 'ICE BERG DILEMMA', 10: 'SNOW BALL CAPER',
    11: 'AVALANCHE', 12: 'PERILOUS SKI SLOPE', 13: 'BOMB CHASE',
    14: 'METALLIC FORTRESS', 15: 'ACID LEAK', 16: 'CLOSED DOORS',
    17: 'LAVA NIGHT', 18: 'MARBLE ISLANDS', 19: 'OBLIVIOUS SPEEDWAY',
    20: 'WARPED TEMPLE OF DOOM',
}

# 基准模板 = 实测 BARRY.sav (打通第1关后)
TEMPLATE = struct.pack('<6i', 2, 4, 47573, -990800, -948794, MODE_ADV)


def fname(level):
    return 'adv%d.sav' % level


def gen():
    os.makedirs(BANK, exist_ok=True)
    print('生成冒险模式 level1 ~ level%d 存档 -> %s' % (TOTAL, BANK))
    print()
    print('  %-14s %-6s %s' % ('文件', '关号', '关卡名'))
    for lv in range(1, TOTAL + 1):
        d = bytearray(TEMPLATE)
        struct.pack_into('<i', d, 0, lv)       # +0 关号
        struct.pack_into('<i', d, 20, MODE_ADV)  # +20 模式标识
        open(os.path.join(BANK, fname(lv)), 'wb').write(bytes(d))
        print('  %-14s %-6d %s' % (fname(lv), lv, LEVELS.get(lv, '')))
    print()
    print('共 %d 份。切换: python make_adventure_saves.py use <1-20>' % TOTAL)


def use(level):
    if not (1 <= level <= TOTAL):
        print('关号须在 1..%d' % TOTAL); return
    src = os.path.join(BANK, fname(level))
    if not os.path.exists(src):
        print('找不到存档:', src)
        print('请先运行: python make_adventure_saves.py gen')
        return
    if os.path.exists(CUR):
        bak = CUR + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
        shutil.copy2(CUR, bak)
        print('当前存档已备份 ->', os.path.basename(bak))
    shutil.copy2(src, CUR)
    lv = struct.unpack_from('<i', open(CUR, 'rb').read(), 0)[0]
    print()
    print('已切换: 下一关 = level%d  %s' % (lv, LEVELS.get(lv, '')))


def list_saves():
    if not os.path.isdir(BANK):
        print('尚未生成。请先运行 gen'); return
    cur = None
    if os.path.exists(CUR):
        cur = struct.unpack_from('<i', open(CUR, 'rb').read(), 0)[0]
    print('存档目录:', BANK)
    print()
    print('  %-14s %-6s %s' % ('文件', '关号', '状态'))
    for lv in range(1, TOTAL + 1):
        p = os.path.join(BANK, fname(lv))
        if not os.path.exists(p):
            print('  %-14s %-6d (缺失)' % (fname(lv), lv)); continue
        mark = '  <== 当前生效' if cur == lv else ''
        print('  %-14s %-6d%s' % (fname(lv), lv, mark))


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
