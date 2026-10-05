# -*- coding: utf-8 -*-
"""生成 Hazard Ball 空格跳跃补丁的机器码并反汇编验证"""
import sys
from keystone import Ks, KS_ARCH_X86, KS_MODE_32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

STUB_VA = 0x442f15
HOOK_VA = 0x4075b0

ASM = """
    push edx
    push ebx
    push edi
    push ebp
    sub  esp, 8
    mov  edi, ecx
    mov  al, byte ptr [edi + 0x39]
    and  al, 0x80
    mov  dl, byte ptr [esp + 4]
    mov  byte ptr [esp + 4], al
    xor  bl, bl
    cmp  al, dl
    je   done
    test al, al
    jz   done
    mov  eax, dword ptr [esi + 0x10]
    and  eax, 0x7fffffff
    mov  ecx, dword ptr [esi + 0x14]
    and  ecx, 0x7fffffff
    cmp  eax, ecx
    jae  maxok
    mov  eax, ecx
maxok:
    mov  dword ptr [esp], eax
    test eax, eax
    jz   bothzero
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
    jmp  setlz
bothzero:
    mov  dword ptr [edi + 0x110], 128
    mov  dword ptr [edi + 0x114], 0
setlz:
    mov  dword ptr [edi + 0x118], 255
    mov  bl, 1
done:
    mov  ecx, edi
    mov  al, bl
    add  esp, 8
    pop  ebp
    pop  edi
    pop  ebx
    pop  edx
    ret
Kconst:
    .float 200.0
"""

# 先汇编占位，算出 Kconst 的实际地址（用了绝对寻址，需要两遍）
ks = Ks(KS_ARCH_X86, KS_MODE_32)
try:
    enc, cnt = ks.asm(ASM, addr=STUB_VA)
except Exception as e:
    print('ASM ERROR:', e)
    sys.exit(1)
code = bytes(enc)
print('stub size =', len(code), 'bytes   (可用 235)')
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.syntax = CS_OPT_SYNTAX_INTEL
for ins in md.disasm(code, STUB_VA):
    print('  %08x  %-22s %s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str))
