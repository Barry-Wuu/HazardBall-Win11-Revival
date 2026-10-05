# -*- coding: utf-8 -*-
"""
Hazard Ball —— 用空格触发 Tilt and Roll 跳跃
原理：在原版「倾斜跳跃」判定入口处注入代码。
  原版跳跃 = 手柄 lZ 轴 > +240 / < -240（猛然抬起），方向取自 lX/lY。
  补丁：检测空格上升沿，用球的当前速度方向合成 lX/lY（自动归一化，与坐标系无关），
        并把 lZ 置 255，从而走原版跳跃流程。
"""
import struct, shutil, os, sys
from keystone import Ks, KS_ARCH_X86, KS_MODE_32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

GAME = r'D:\Hazard Ball\Hazard.exe'
STUB_VA = 0x442f15          # .text 尾部空闲区
HOOK_VA = 0x40759a          # 跳跃判定入口（占用 28 字节）
HOOK_LEN = 0x4075b6 - HOOK_VA      # = 28
JMP_JUMP = 0x4075be         # 起跳流程
JMP_NORM = 0x40780a         # 常规流程
INPUT_OBJ = 0x44bc2c        # 输入对象指针全局
KMAG = 200.0                # 合成倾斜量上限（<255，跳跃强度）

ASM = """
    push edx
    push ebx
    push edi
    push ebp
    mov  edi, dword ptr [0x44bc2c]
    mov  al, byte ptr [edi + 0x39]
    and  al, 0x80
    mov  dl, byte ptr [edi + 0x163]
    mov  byte ptr [edi + 0x163], al
    cmp  al, dl
    je   nojump
    test al, al
    jz   nojump
    push ecx
    mov  eax, dword ptr [esi + 0x10]
    and  eax, 0x7fffffff
    mov  ecx, dword ptr [esi + 0x14]
    and  ecx, 0x7fffffff
    cmp  eax, ecx
    jae  maxok
    mov  eax, ecx
maxok:
    push eax
    test eax, eax
    jnz  have_scale
    add  esp, 4
    mov  dword ptr [edi + 0x110], 128
    mov  dword ptr [edi + 0x114], 0
    jmp  setlz
have_scale:
    fld  dword ptr [esi + 0x10]
    fld  dword ptr [esp]
    fdivp st(1), st(0)
    fmul dword ptr [Kconst]
    fistp dword ptr [edi + 0x110]
    fld  dword ptr [esi + 0x14]
    fld  dword ptr [esp]
    fdivp st(1), st(0)
    fmul dword ptr [Kconst]
    fistp dword ptr [edi + 0x114]
    add  esp, 4
setlz:
    mov  dword ptr [edi + 0x118], 255
    pop  ecx
    pop  ebp
    pop  edi
    pop  ebx
    pop  edx
    mov  ecx, dword ptr [0x44bc2c]
    jmp  jumptarget
nojump:
    pop  ebp
    pop  edi
    pop  ebx
    pop  edx
    jmp  normtarget
jumptarget:
    jmp  0x4075be
normtarget:
    jmp  0x40780a
Kconst:
    .float 200.0
"""

def assemble():
    ks = Ks(KS_ARCH_X86, KS_MODE_32)
    enc, cnt = ks.asm(ASM, addr=STUB_VA)
    if enc is None:
        raise SystemExit('assemble failed')
    return bytes(enc)

def main():
    code = assemble()
    print('stub size = %d bytes (cave = 235)' % len(code))
    assert len(code) <= 235, 'stub too big'
    # 校验反汇编
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.syntax = CS_OPT_SYNTAX_INTEL
    for ins in md.disasm(code, STUB_VA):
        print('  %08x  %s %s' % (ins.address, ins.mnemonic, ins.op_str))

    b = bytearray(open(GAME, 'rb').read())

    # 1) 钩子：0x40759a 处 28 字节 -> jmp stub + nop
    hook_off = 0x40759a - 0x400000
    rel = STUB_VA - (HOOK_VA + 5)
    hook = b'\xE9' + struct.pack('<i', rel) + b'\x90' * (HOOK_LEN - 5)
    assert len(hook) == HOOK_LEN
    b[hook_off:hook_off + HOOK_LEN] = hook
    print('hook: jmp %08x (rel=%d) at %08x' % (STUB_VA, rel, HOOK_VA))

    # 2) stub 写入 .text 尾部
    stub_off = STUB_VA - 0x400000
    assert all(x == 0 for x in b[stub_off:stub_off + len(code) + 8]), 'stub area not zero'
    b[stub_off:stub_off + len(code)] = code

    # 3) 扩大 .text 的 SizeOfRawData 以覆盖该区（0x41f15 -> 0x42000）
    e = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, e + 6)[0]
    opt = e + 24
    magic = struct.unpack_from('<H', b, opt)[0]
    sec_off = opt + (224 if magic == 0x10b else 240)
    # 第 0 个 section = .text；SizeOfRawData 在其头部 +16
    szoff = sec_off + 16
    old = struct.unpack_from('<I', b, szoff)[0]
    assert old == 0x41f15, 'unexpected .text rawsize %x' % old
    struct.pack_into('<I', b, szoff, 0x42000)
    print('.text SizeOfRawData: %x -> %x' % (old, 0x42000))

    bak = GAME + '.orig'
    if not os.path.exists(bak):
        shutil.copy2(GAME, bak)
        print('backup ->', bak)
    else:
        print('backup exists:', bak)
    open(GAME, 'wb').write(bytes(b))
    print('written:', GAME, len(b), 'bytes')

if __name__ == '__main__':
    main()
