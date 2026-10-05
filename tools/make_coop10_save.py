# -*- coding: utf-8 -*-
"""
生成"直接进 coop10"的 2UP GAME.sav。

=== 格式 (由两次实测通关对比确定) ===
24 字节, 6 个 int32:
  +0   关号 (已完成关数+1)      打完第1关->2, 打完第2关->3
  +4   固定 4 (未知, 保持原值)
  +8   累计成绩                 39478 -> 68830 (+29352, 随关卡而异)
  +12  校验位 A                -990800 -> -990799 (每关 +1)
  +16  校验位 B                -948794 -> -948793 (每关 +1)
  +20  固定 2 (未知, 保持原值)

关键: +12/+16 是随关号线性递增的校验位, 必须与 +0 同步, 否则游戏判定
存档无效并回退到第 1 关 (这是之前改 +0=10 失败的原因)。

目标: +0 = 10  =>  相对第2关存档(+0=3) 需 +7
      => +12 += 7, +16 += 7
"""
import os, struct, shutil, time

SAVE = r'D:\Hazard Ball\DATA\SAVE'
SRC = os.path.join(SAVE, '2UP GAME.sav')
ALT = os.path.join(SAVE, '2UP GAME.sav.coop10')
TARGET = 10


def fields(d):
    return list(struct.unpack_from('<6i', d, 0))


def show(tag, d):
    f = fields(d)
    print('  %-10s %s' % (tag, d.hex(' ')))
    print('  %-10s 关号=%d  ?=%d  成绩=%d  校验A=%d  校验B=%d  ?=%d'
          % ('', f[0], f[1], f[2], f[3], f[4], f[5]))


if __name__ == '__main__':
    if not os.path.exists(SRC):
        print('!! 找不到存档:', SRC)
        raise SystemExit(1)

    d = bytearray(open(SRC, 'rb').read())
    print('当前存档 (刚打完第2关):')
    show('raw', d)

    f = fields(d)
    cur = f[0]
    if cur >= TARGET:
        print()
        print('当前关号已 >= %d, 无需修改。' % TARGET)
        raise SystemExit(0)

    delta = TARGET - cur
    print()
    print('目标关号 %d, 需前进 %d 关 (校验位同步 +%d)' % (TARGET, delta, delta))

    # 备份
    bak = SRC + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
    shutil.copy2(SRC, bak)
    print('已备份 ->', os.path.basename(bak))

    # 同步修改: +0 关号, +12/+16 校验位各 +delta
    struct.pack_into('<i', d, 0, TARGET)
    struct.pack_into('<i', d, 12, f[3] + delta)
    struct.pack_into('<i', d, 16, f[4] + delta)
    # +8 成绩: 按前两关的平均增量 (29352) 估算
    est_score = f[2] + 29352 * delta
    struct.pack_into('<i', d, 8, est_score)
    print('  +0  关号   %d -> %d' % (f[0], TARGET))
    print('  +8  成绩   %d -> %d (按每关 +29352 估算)' % (f[2], est_score))
    print('  +12 校验A  %d -> %d' % (f[3], f[3] + delta))
    print('  +16 校验B  %d -> %d' % (f[4], f[4] + delta))

    print()
    print('修改后:')
    show('new', d)

    open(SRC, 'wb').write(bytes(d))
    open(ALT, 'wb').write(bytes(d))
    print()
    print('已写入 %s (及备选 %s)' % (os.path.basename(SRC), os.path.basename(ALT)))
    print()
    print('验证: 启动 -> 2UP GAME -> RESUME GAME, 预期直接进 coop10。')
    print('回退: 用 bak_ 时间戳文件覆盖即可。')
