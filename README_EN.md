# Hazard Ball Win11 Revival (English)

Bringing **Hazard Ball** (2004) back to life on modern Windows 11.

> Hazard Ball (aka **Hazard: Chris' Golf Ball Puzzle**) is a marble-physics puzzle game by
> British developer **Chris Eastwood**, released in 2004. You roll a ball through mechanical
> mazes;multiplayer mode supports same-screen versus play.

**中文版 README 见 [`README.md`](README.md)（内容更全，含 3 篇逆向文档的中文原文）。**

```
Double-click Hazard.exe        # just play
Double-click 选关器.exe       # level selector (Adventure 20 levels / Co-op 10 levels)
```

> The level selector is a tkinter GUI: **green card = current level in your save file**;
> click any number to jump there. The previous save is backed up as `*.sav.bak` first.
> Requires the save-validation bypass patch (issue 4 below) to be effective.

---

## What Was Fixed

| # | Problem | Fix | Status |
|---|---|---|---|
| 1 | **coop10 "TEMPLE OF DOOM" two-player start blocks are incomplete** — each start tile is missing its top-left corner, with lava in the gap, so players get stuck on spawn | Patched the two missing terrain cells | ✅ |
| 2 | **Tilt and Roll mode requires a PS3 SIXAXIS tilt controller to jump** | Bound to the spacebar instead of "lift the sensor" | ✅ |
| 3 | **Windowed mode: mouse coordinates are wrong** — cursor ghost on screen, clicks land outside the window, flicker at the edges | Root-caused; documented the correct fix | ✅ |
| 4 | **No level select in Adventure / Co-op modes** — progress is only saved by completing levels one by one | Built a level selector (GUI) + save-validation bypass patch | ✅ |

---

## Issue 1 — coop10 start blocks

### Symptom
In the last co-op level, **coop10 "TEMPLE OF DOOM"**, each ball's starting block is missing one
corner tile. Lava sits in the notch, so the ball is trapped the instant it spawns.

### Root cause
In the `.map` format (reverse-engineered, see `tools/hz.py`), spawn points are identified by
terrain index, each occupying a 2×2 arrangement of 4 cells:

| Player | 2×2 layout |
|---|---|
| Player 1 | `6 7` / `8 9` |
| Player 2 | `2 3` / `4 5` |

A scan of all 127 maps (`tools/scan_ck.py`) shows **only coop10's two start blocks are incomplete**.
Both are missing exactly the **top-left cell**:

| Start | Missing cell | Actual value |
|---|---|---|
| Player 1 (terrain 6-9) | `(55,17)` should be `6` | plain floor `50` |
| Player 2 (terrain 2-5) | `(58,17)` should be `2` | plain floor `50` |

The two start blocks are separated by a lava column at index 57 — precisely the death trap the
incompleteness creates.

### Fix
`tools/fix_coop10.py` writes exactly two terrain cells (file offsets 2093 / 2096).
The original is preserved as `DATA/coop10.map.orig`.

Verification: after the fix, `scan_ck.py` reports all co-op spawn blocks as complete 2×2.

---

## Issue 2 — Spacebar jump for Tilt and Roll

### Symptom
Tilt and Roll mode (game state 25) only jumps if you own a **PS3 SIXAXIS six-axis controller**.
The game matches gamepads by a "3 axes, 0 buttons" DirectInput fingerprint, which no ordinary
keyboard or gamepad satisfies.

### Root cause (capstone disassembly of `Hazard.exe`)
- Input object `[0x44BC2C]`: `+0x000` 256-byte keyboard state (standard DIK scancodes,
  space = `0x39`), `+0x10C` gamepad, `+0x110/+0x114/+0x118` = gamepad lX / lY / **lZ**.
- Jumping has **two gates** that must both hold:
  1. flag `[obj+0x161]`, set by the gamepad poll loop (`0x408720`, threshold |axis| > 50)
  2. **|lZ| > 240** — this is the actual "flick the tilt sensor up" action
- Direction comes from lX / lY (via `+0x110/+0x114`).
- Hidden catch: `0x40759A` also checks "is a direction key currently held", and holding one
  **bypasses the entire jump check** → keyboard players can never jump even with the flag set.

Strings that confirm the semantics:
- `TIP: LIFT THE TILT SENSOR FIRMLY TO JUMP (WHILST MOVING)`
- `USB TILT SENSOR NOT DETECTED` / `WITH A 3-AXIS TILT SENSOR`
- `PERFECT JUMP!!!`

### Fix
**Leaves gamepad detection untouched** — only the "lift the sensor" action is re-triggered by the
spacebar. Patch built by `tools/build_patch.py`:

- Hook at `0x40759A` (28 bytes) → `JMP 0x442F15`
- 175-byte stub placed in free `.text` tail space, with `.text` `SizeOfRawData` raised from
  `0x41F15` to `0x42000` (exactly abutting `.rdata`) so the stub is mapped and executable
- Stub logic: **spacebar rising edge** → synthesize lX/lY from the ball's current velocity
  direction (divide by the larger component, multiply by 200, so the direction automatically
  follows the movement direction with no world-coordinate sign assumptions) → `lZ = 255` →
  run the original jump code path
- Bonus: also fixes "jump while holding a direction key", which the original never allowed

The logic sits at a coordinate-independent point, so it does not depend on level geometry.

### Known trade-offs
- The spacebar jump **replaces** the original gamepad path — plugging in a real SIXAXIS controller
  will no longer trigger jumping. (Keeping both would need an extra branch.)
- Edge-triggered: holding the key jumps once; release and press again for another jump.

---

## Issue 3 — Windowed-mode mouse coordinate offset (ghost cursor / clicks outside)

### Symptom
With the game window **centered on screen**:
- a **mouse ghost remains in the screen's top-left corner** (the real cursor is dragged outside
  the game window)
- **clicks on any menu item land outside the window**
- the cursor **flickers** (constantly yanked back at the boundary)

### Root cause
The game's entire coordinate model **hard-assumes "client area is at screen origin (0,0)"**:

1. `CreateWindowExA` (`0x423AF3`) is called with window X/Y **literally 0**
   (`0x423AE1/0x423AE2: push ebx`, with ebx=0) — the game itself requests a window at the origin
2. The per-frame clamp (`0x41C0D0`) compares `GetCursorPos`'s **absolute screen coordinates**
   against hard-coded bounds: `.rdata` `0x4433A4 = 25.0` / `0x4433A0 = 600.0` /
   `0x44339C = 440.0` — that is the **window-local logical box of a 640×480 client area**
   (600 = 640−40, 440 = 480−40), **with no window screen origin involved**
3. Out-of-bounds → `SetCursorPos` yanks the cursor back

When the window is centered, `clientOrigin = (401,241)`, so the clamp range `X[25,600]` lies
entirely **to the left of the window**. Measured at runtime: the OS cursor gets pinned at
`(247,392)` while the window's left edge is `401` — 154 pixels outside the window.

**This assumption holds naturally in fullscreen** (client area == screen, origin 0,0), which makes
it a textbook case of "written for fullscreen, no window-mode coordinate conversion".

### Resolution (zero exe changes)

**Keep the window at (0,0)** — the game's native requirement.

`dgVoodoo.conf` can stay at its default `CenterAppWindow = true`: measured behaviour is that
dgVoodoo does **not** force-override the initial position the game requests in this title, so the
window reliably stays at (0,0). Verified across 3 consecutive restarts: window pinned top-left,
menus clickable.

> **Why can't the window be centered?**
> Centering requires converting **every** hard-coded coordinate — the clamp *and* the menu hit
> testing — to window-relative form (`org + 25`, `org + 600`, …). Three window-relativization
> patches were attempted here and none worked, because menu hit testing is a *separate* (0,0)
> assumption: fixing clamp alone is not enough. If a centered window is genuinely required, the
> way forward is a coordinate-conversion layer (hook `GetCursorPos`/`SetCursorPos` for
> ±clientOrigin). The toolchain is ready (`tools/hdis.py` / `refs.py` / `relcall.py`), and
> `.theta` section has ~1.8 KB of RWX free space at `0x4748D9` for a trampoline.

### Three wrong conclusions I corrected along the way (recorded so they are not repeated)

1. **Matching windows by title**: `GetWindowText` matched an unrelated `CabinetWClass`
   "Hazard Ball" **file-open dialog** (1455×927, pid ≠ the game), leading to a wrong read of the
   window position. **Filter by `class='winclass'` + client size (638×478) instead.**
2. **Blaming recenter**: measured `[0x44BC58]/[0x44BC5C]` have **no write sites anywhere in the
   file** and stay 0, so the per-frame recenter (`0x40EB10`) target is `X + 0.03×155×0 = X` — a
   **no-op**. The "flicker" is clamp firing repeatedly on a centered window, inherent behaviour
   unrelated to any patch.
3. **Assuming fixing clamp was enough**: menu hit testing is an independent (0,0) assumption.

> Lesson: for window/coordinate problems, **enumerate live windows and read runtime globals**
> (`ReadProcessMemory`) before touching anything. Static disassembly tells you what the code says,
> not what actually happens.

---

## Issue 4 — Level selector for Adventure / Co-op modes

### Background
The original game has **no level-select menu**. Adventure mode (20 levels) and Co-operative mode
(10 levels) only offer `RESUME GAME`; progress is recorded as "next level number" inside the save
file, so you must **clear every level in order** to advance.

### Save format (measured from `BARRY.sav` / `2UP GAME.sav` — both identical in layout)
```
24 bytes = 6 × int32
  +0   next level number      clear level 1 → 2
  +4   fixed 4
  +8   cumulative score
  +12  checksum slot A     ┐ baselines are read from RUNTIME memory,
  +16  checksum slot B     ┘ so a valid save cannot be computed offline (see below)
  +20  mode marker         Adventure = 1, Co-op = 2
```

### The obstacle: checksums are computed against runtime state
The load routine at `0x411990` performs a double check:

```
0x411A4A  ecx ^= 0xE0301
0x411A5F  eax ^= 0xE0301
0x411A59  ecx = [0x44DC30]        ; ← runtime baseline, NOT a save field
0x411A64  edx = 0xFFFEE2B3 - ecx
0x411A69  cmp eax, edx
0x411A6F  je  success
          mov [0x44DC30], 1        ; failure: mark save invalid → level zeroed → back to level 1
```

The baselines `[0x44DC30]` / `[0x44B5A8]` are written by the game at runtime on the **previous
successful save**, so **a valid save cannot be forged offline** — editing `+0` by hand is always
rejected and drops you back to level 1.

### Fix: bypass the check (`tools/patch_skip_savecheck.py`)
Turn the three `je` instructions ("if equal, skip the failure block") into `jmp`, making the check
always pass:

| Address | Original | Patched |
|---|---|---|
| `0x411A6F` | `74 11` (je) | `EB 11` (jmp) |
| `0x411A94` | `74 0C` (je) | `EB 0C` (jmp) |
| `0x411ACB` | `c7 05 30 dc 44 00 01 00 00 00` | `90`×10 (nop) |

14 bytes total. `Hazard.exe.orig` is the unpatched original (save validation restored).

### The level selector (tkinter)

`选关器.exe` / `选关器.py` — a native Windows GUI, replacing an earlier `.bat` version.

The window holds two grids of numbered cards:

```
ADVENTURE   Adventure · 20 levels      CO-OPERATIVE  Co-op · 10 levels
 1  2  3  4  5                         1  2  3  4  5
 6  7  8  9 10                         6  7  8  9 10
11 12 13 14 15
16 17 18 19 20
```

- **Green card** = current level in the save file, read on startup
- Click any number to switch; the status bar refreshes after confirmation
- The previous save is backed up to `*.sav.bak` before writing
- Refuses to switch while the game is running (the save file may be locked)
- Choose `1` to start over from the first level

**Why not a .bat**: cmd scripting here fights GBK encoding, `cp936` tokenization, and the conflict
between single-keystroke input and two-digit numbers. `choice`'s errorlevel values are very easy
to misalign — pressing `M` once ended up resetting to level 1. tkinter has no encoding ambiguity and
reads/writes files directly, which is the right tool for this job.

The save library stays in the repo as reference data (`DATA/SAVE/saves_adv/`,
`DATA/SAVE/saves/`), but the selector **no longer reads it** — it constructs the 24-byte save on
demand.

### Appendix: `times.dat` (960 bytes = 60 × 16 bytes)
A **leaderboard**, unrelated to unlocking. Each entry: timestamp + player name (8B) + score (float);
`EMPTY` means unranked.

### Adventure level names
| # | Name | # | Name |
|---|---|---|---|
| 1 | MEMORIES | 11 | AVALANCHE |
| 2 | BACKLASH | 12 | PERILOUS SKI SLOPE |
| 3 | DESERT TOWER | 13 | BOMB CHASE |
| 4 | HEAT WAVE | 14 | METALLIC FORTRESS |
| 5 | SWAMP OUTPOST | 15 | ACID LEAK |
| 6 | ELEMENTAL RACE | 16 | CLOSED DOORS |
| 7 | FLOODED CITADEL | 17 | LAVA NIGHT |
| 8 | ABANDONED STONGHOLD | 18 | MARBLE ISLANDS |
| 9 | ICE BERG DILEMMA | 19 | OBLIVIOUS SPEEDWAY |
| 10 | SNOW BALL CAPER | 20 | WARPED TEMPLE OF DOOM |

---

## Repository Layout

```
├── Hazard.exe                 # ★spacebar-jump patch applied (175 bytes differ)
├── Hazard.exe.orig            # original exe (for rollback)
├── dgVoodoo.conf              # Win11 runtime config (windowed mode)
├── D3D8.dll D3D9.dll DDraw.dll D3DImm.dll   # dgVoodoo2 2.87 translation layer
├── dgVoodooCpl.exe            # dgVoodoo control panel
├── HazEd.exe                  # level editor
├── DATA/                      # 127 .map files + all WAV sounds
│   └── coop10.map(.orig)      # ★fixed spawn blocks + original backup
├── CUSTOM_MAPS/               # 11 community levels
├── 选关器.exe                 # ★level selector (Adventure 20 / Co-op 10)
├── 选关器.py                  # same, as source (run with python if no exe)
├── DATA/SAVE/                 # current progress + 30 level-select saves
├── tools/                     # reproducible toolchain (26 scripts)
└── docs/                      # reverse-engineering notes (3 documents)
```

## Documentation

| Document | Contents |
|---|---|
| [`docs/001-map格式.md`](docs/001-map格式.md) | `.map` level format: header fields, terrain/cells layers, spawn-point index convention |
| [`docs/002-倾斜传感器与跳跃机制.md`](docs/002-倾斜传感器与跳跃机制.md) | `Hazard.exe` RE notes: section table, import table, input object layout, the three gates of the jump check, patch design |
| [`docs/003-窗口鼠标坐标错位.md`](docs/003-窗口鼠标坐标错位.md) | Mouse coordinate offset root cause, runtime measurements, three corrected wrong conclusions, runtime global reference table |

## Toolchain

| Script | Purpose |
|---|---|
| `hz.py` | Parse `.map` format (tileset / size / level id / terrain / cells) |
| `scan_ck.py` | Scan all co-op maps for two-player spawn block completeness |
| `fix_coop10.py` | Fill in coop10's two incomplete spawn blocks (idempotent + backup + verify) |
| `build_patch.py` / `build_stub.py` | Generate the Tilt-and-Roll spacebar jump patch |
| `hdis.py` | capstone disassembly wrapper (`python hdis.py <start> <end>`) |
| `refs.py` | Find every reference to a given address |
| `relcall.py` | Brute-force scan for relative `E8`/`E9` calls (**more reliable than linear disassembly**) |
| `callfind.py` | Find callers of a function |
| `peek.py` / `pe_info.py` / `import2.py` | PE section table / import table (IAT addresses) parsing |
| `strings_hz.py` | Keyword string extraction + xref |
| `vtcall.py` | Count indirect COM vtable calls |
| `fix_clamp.py` | Window-relative clamp (**experimental, not enabled** — see issue 3) |
| `pin_window.py` | Pin the window to (0,0) (`--show` / `--once` / resident) |
| `revert.py` / `revert_clamp.py` | One-shot rollback (all patches / clamp patch only) |
| `patch_skip_savecheck.py` | **Save-validation bypass patch** (prerequisite for the selector, 14 bytes) |
| `make_coop_saves.py` | Generate / switch / list the 10 Co-op saves |
| `make_adventure_saves.py` | Generate / switch / list the 20 Adventure saves |
| `analyze_2up.py` | Parse the `2UP GAME.sav` field layout |

Requirements: Python 3.11+; `pip install capstone keystone-engine` (only needed for building patches).

### Reproduce

```bash
# 1. Verify coop10 spawn completeness (should report all green now)
python tools/scan_ck.py

# 2. Restore from the original coop10.map.orig and re-apply the fix
python tools/fix_coop10.py

# 3. Regenerate the jump patch from Hazard.exe.orig
python tools/build_patch.py

# 4. Regenerate the level-select save library
python tools/make_coop_saves.py gen
python tools/make_adventure_saves.py gen

# 5. Roll back every patch (including save validation)
python tools/revert.py
```

## Roadmap

- [x] `.map` format fully reverse-engineered + all 127 maps verified
- [x] coop10 two-player spawn blocks completed
- [x] Tilt and Roll spacebar jump (including "jump while holding a direction key")
- [x] Windowed-mode mouse coordinate offset root-caused (ghost cursor / stray clicks / flicker)
- [x] Playable Win11 build (dgVoodoo2 2.87, windowed 640×480)
- [x] **Adventure / Co-op level selector** (GUI + save-validation bypass patch)
- [ ] Centered-window solution (coordinate-conversion layer via `GetCursorPos`/`SetCursorPos` hook)
- [ ] Tilt sensor mode: keep the gamepad path alongside spacebar
- [ ] Integrity survey of the remaining 126 maps

## Legal

This project is for **technical research and digital preservation**. Hazard Ball and all of its
assets are the property of the original author **Chris Eastwood**. This repository preserves
hard-to-find legacy platform assets and documents the complete reverse-engineering findings.