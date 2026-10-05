# -*- coding: utf-8 -*-
"""
Hazard Ball - mouse clamp window-relative fix (v1, verified-assembling)

Root cause (confirmed by static analysis + live window probe):
  clamp at 0x41c0d0 compares the SCREEN cursor (GetCursorPos -> [0x44bc40]/
  [0x44bc44]) against HARDCODED window-internal bounds 25 / 600 / 440 (the
  640x480 client logical box) and, when out of range, calls SetCursorPos with
  those raw values. With dgVoodoo CenterAppWindow=true the client origin is
  ~(401,241), so the box [25,600]x[25,440] lies up-left of the window: the
  real cursor gets slammed to x=25 (outside the window) -> ghost cursor +
  clicks land outside + cursor visibly jumps. That is the "left-top ghost".

Fix: make the clamp window-relative. Read the client-area screen origin once
via ClientToScreen(hwnd,[0x46ffbc], {0,0}), then clamp into
[orgX+25, orgX+600] x [orgY+25, orgY+440]. SetCursorPos is only issued when
the value actually changed (mirrors the original "only on overflow" intent),
so no extra cursor-jitter source is added. One extra ClientToScreen per frame.

Verified: [0x44bc58]/[0x44bc5c] are never written (stay 0) => the per-frame
recenter at 0x40eb10 is a no-op; clamp is the only real cursor mover.
"""
import struct, sys, os
sys.path.insert(0, r'D:\B++\WorkBuddy\hazard_hack')
from keystone import Ks, KS_ARCH_X86, KS_MODE_32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SYNTAX_INTEL

P = r'D:\Hazard Ball\Hazard.exe'
BAK = r'D:\Hazard Ball\Hazard.exe.preclamp'
b = bytearray(open(P, 'rb').read())
IMG = 0x400000
SECS = [(0x1000, 0x1000, 0x42000), (0x43000, 0x43000, 0x2000), (0x45000, 0x45000, 0x2d000),
        (0x72000, 0x72000, 0x13000), (0x9c000, 0x74000, 0x1000)]
def va2off(va):
    rva = va - IMG
    for sva, sraw, ssz in SECS:
        if sva <= rva < sva + ssz:
            return sraw + (rva - sva)
    return None

OLD_VA, OLD_SZ = 0x41c0d0, 0x112
HWND = 0x46ffbc
IAT_GetCursorPos = 0x443168
IAT_SetCursorPos = 0x44316c
IAT_ClientToScreen = 0x443184

# No forward references: every branch target label is defined before use.
asm = f"""
    push ebp
    mov  ebp, esp
    sub  esp, 0x10
    push ebx
    push esi
    push edi
    mov  dword ptr [0x44bd4c], 0x2d
    mov  dword ptr [0x44bd38], 0
    mov  dword ptr [0x44bd34], 0
    mov  dword ptr [0x44bd3c], 0
    mov  dword ptr [0x44bd40], 0
    mov  dword ptr [ebp - 0x10], 0
    mov  dword ptr [ebp - 0x0c], 0
    mov  eax, dword ptr [{HWND:#x}]
    push eax
    lea  eax, [ebp - 0x10]
    push eax
    call dword ptr [{IAT_ClientToScreen:#x}]
    mov  esi, dword ptr [ebp - 0x10]
    mov  edi, dword ptr [ebp - 0x0c]
    lea  eax, [ebp - 0x10]
    push eax
    call dword ptr [{IAT_GetCursorPos:#x}]
    mov  ebx, dword ptr [ebp - 0x10]
    mov  eax, dword ptr [ebp - 0x0c]
    mov  [ebp - 8], ebx
    mov  [ebp - 4], eax
    lea  ecx, [esi + 25]
    cmp  ebx, ecx
    jge  xok1
    mov  ebx, ecx
xok1:
    lea  ecx, [esi + 600]
    cmp  ebx, ecx
    jle  xok2
    mov  ebx, ecx
xok2:
    lea  ecx, [edi + 25]
    cmp  eax, ecx
    jge  yok1
    mov  eax, ecx
yok1:
    lea  ecx, [edi + 440]
    cmp  eax, ecx
    jle  yok2
    mov  eax, ecx
yok2:
    cmp  ebx, [ebp - 8]
    jne  moved
    cmp  eax, [ebp - 4]
    je   done
moved:
    push ebx
    fild dword ptr [esp]
    add  esp, 4
    fst  dword ptr [0x44bc40]
    push eax
    fild dword ptr [esp]
    add  esp, 4
    fst  dword ptr [0x44bc44]
    push eax
    push ebx
    call dword ptr [{IAT_SetCursorPos:#x}]
    add  esp, 8
done:
    pop  edi
    pop  esi
    pop  ebx
    mov  esp, ebp
    pop  ebp
    ret
"""

ks = Ks(KS_ARCH_X86, KS_MODE_32)
encoding, count = ks.asm(asm, addr=OLD_VA)
code = bytes(encoding)
print('assembled %d bytes (%d stmts), space %d' % (len(code), count, OLD_SZ))
assert len(code) <= OLD_SZ, 'exceeds original space!'

if not os.path.exists(BAK):
    open(BAK, 'wb').write(bytes(b))
    print('backup ->', BAK)

off = va2off(OLD_VA)
for i in range(OLD_SZ):
    b[off + i] = 0x90
b[off:off + len(code)] = code
open(P, 'wb').write(bytes(b))
print('patched %08x (off %06x)' % (OLD_VA, off))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.syntax = CS_OPT_SYNTAX_INTEL
print('\n=== verify ===')
nb = bytes(b)
for ins in md.disasm(nb[off:off + len(code) + 4], OLD_VA):
    print('  %08x  %-22s %s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str))
