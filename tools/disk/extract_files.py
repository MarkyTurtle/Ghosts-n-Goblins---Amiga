"""Extract every file the game loads from the decoded tracks and write disk/FILES.md and disk/DISKMAP.md.
Run from the archive root:  python3 tools/disk/extract_files.py"""
import os, hashlib
TRK = 'bin/tracks'; OUT = 'disk/files'; TB = 6312          # bytes of data per custom track
# tracks, length, file name, 512K load, 1MB load, loaded by, contents, documented in
FILES = [
 (1, 0x18300, 't001-016_loading_screen.bin', '$60000', '$60000', 'bootblock',
  'Loading screen: 256-px-wide HAM6 interlaced picture (interleaved planes) + palette', 'gng_boot.s, render/out/loadscreen.png'),
 (17, 0x18A80, 't017-032_main_1mb.hunk', '-', 'ExecBase&$FFF80000 or $80000', 'bootblock (expanded memory)',
  'Main program, 1MB build (base-relative), hunk header left in place', 'bin/main_1mb.bin, tools/compare_builds.py'),
 (33, 0x5400, 't033-036_arthur_sprites.bin', '$37468', '$80 (staging)', 'Start (FileTable+0)',
  "Arthur's hardware-sprite frames: 42 x 32x32, 4 planes; mirrored copies built at start-up", 'gng_main.s Start, render/out/arthur.png'),
 (37, 0x0D20, 't037_small_bob_sets.bin', '$311E8 (BOB_GFX_A)', '$80 (staging)', 'LoadLevel (512K: every level)',
  '10 single-image item/scenery BOBs (coin, money bag, stone block, grass raft, rock, 3 gravestones, boulder and ice platforms); per-level subset selected by LevelSmallBobMask', 'gng_main.s LoadLevel'),
 (38, 0x1D042, 't038-056_enemy_bobs.bin', '$37468', '$80 (staging)', 'LoadLevel (512K: every level)',
  '21 enemy BOB sets (BobSetOffsets/BobSetSizes); LoadLevel copies the sets each level needs', 'README Data formats, render/out/bobs.png'),
 (57, 0x0EA6, 't057_item_gfx_part2.bin', '$1CF8E', '$80 (staging)', 'Start',
  'Tail of the weapon / pickup / effect BOB block (continues track 59)', 'render/out/item_gfx.png'),
 (58, 0x1234, 't058_enemy_shot_gfx.bin', '$1A298', '$80 (staging)', 'Start',
  'Enemy projectile BOBs (fireballs, eyeballs, sparks, orbs); frame table $9002', 'render/out/enemy_shot_gfx.png'),
 (59, 0x1AC2, 't059-060_item_gfx.bin', '$1B4CC', '$80 (staging)', 'Start',
  'Weapon, pickup and effect BOBs (lance, dagger, axe, torch, cross, armour, treasure, key, explosions); frame table $908E', 'render/out/item_gfx.png'),
 (61, 0x1840, 't061_font.bin', '$37468 -> MASK_BUF $28234', '$80 (staging)', 'Start',
  'Font: every other byte is used (16 bytes per character)', 'gng_main.s PrintChar'),
 (62, 0x1D5C, 't062-063_progress_map.rle', '$311E8', '$80 (staging)', 'ProgressMap',
  'Between-level map picture, ByteRun1-style RLE: 80 rows x 5 planes x (4+44) bytes', 'render/out/progress_map.png'),
 (64, 0x1B394, 't064-081_music_1mb.hunk', '-', '$3604C', 'Start (1MB build only)',
  'Sound driver + 15 tunes + 30 sound effects', 'sound/gng_music_1mb.s, sound/SOUND.md'),
 (82, 0x25FE, 't082-083_copyright_screen.rle', '$4DC68', '$16880', 'Start',
  'FAST "Copyright Notice / Warning!" anti-piracy screen, RLE: 224 rows x 5 planes x (4+32) bytes; shown 10 s at boot', 'render/out/copyright_screen.png'),
 (84, 0x7440, 't084-088_level0_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 0 tiles (186 x 16x16, 5 planes, line-interleaved)', 'render/out/level0.png'),
 (89, 0xC120, 't089-096_level1_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 1 tiles (309, second bank for cells $1D/$1F)', 'render/out/level1.png'),
 (97, 0x5460, 't097-100_level2_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 2 tiles (135)', 'render/out/level2.png'),
 (101, 0x4880, 't101-103_level3_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 3 tiles (116)', 'render/out/level3.png'),
 (104, 0x2760, 't104-105_level4_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 4 tiles (63)', 'render/out/level4.png'),
 (106, 0x29E0, 't106-107_level5_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 5 tiles (67)', 'render/out/level5.png'),
 (108, 0x19A0, 't108-109_level6_tiles.bin', '$65548', '$573E0', 'LoadLevel', 'Level 6 tiles (41)', 'render/out/level6.png'),
 (110, 0x18A80, 't110-125_main_512k.hunk', '$80', '-', 'bootblock (512K)',
  'Main program, 512K build, pre-relocated for $80, hunk header left in place', 'gng_main.s (byte-identical source)'),
 (126, 0x7D64, 't126-131_sfx_512k.hunk', '$28E54', '-', 'Start (512K build only)',
  'Sound driver + 30 sound effects (no music)', 'sound/gng_sfx_512k.s, sound/SOUND.md'),
]
def ntracks(n): return (n + TB - 1) // TB
os.makedirs(OUT, exist_ok=True)
rows = []
owner = {}
for t0, ln, name, l5, l1, by, what, doc in FILES:
    data = b''; t = t0
    while len(data) < ln: data += open(f'{TRK}/t{t:03d}.bin', 'rb').read(); t += 1
    full = data; data = data[:ln]
    open(f'{OUT}/{name}', 'wb').write(data)
    nt = ntracks(ln); slack = nt * TB - ln
    tail = full[ln:nt * TB]
    rows.append((t0, t0 + nt - 1, name, ln, l5, l1, by, what, doc, hashlib.sha1(data).hexdigest()[:12]))
    for k in range(nt): owner[t0 + k] = (name, k, nt, slack if k == nt - 1 else 0, (sum(1 for b in tail if b) if k == nt - 1 else 0))
# bootblock / track 0
boot = open('bin/bootblock.bin', 'rb').read()
open(f'{OUT}/t000_bootblock.bin', 'wb').write(boot)

L = ['# Disk files', '',
 "Every file the game loads, extracted from the decoded tracks (`bin/tracks/`) into `disk/files/`.",
 'Files are listed in the 512K build\'s file table at `FileTable` (`$7F9C`), except the bootblock loads,',
 'the 1MB-only music file and the main programs. A custom track holds 6,312 bytes of data.', '',
 '| Tracks | File | Bytes | Load (512K) | Load (1MB) | Loaded by | Contents | See | SHA-1 |',
 '|---|---|---:|---|---|---|---|---|---|',
 f'| 0 | `t000_bootblock.bin` | 1,024 | Kickstart → loader at `$7FC00` | same | Kickstart | AmigaDOS bootblock containing the whole trackloader; rest of track 0 is filler | gng_boot.s | {hashlib.sha1(boot).hexdigest()[:12]} |']
for t0, t1, name, ln, l5, l1, by, what, doc, h in sorted(rows):
    tr = f'{t0}' if t0 == t1 else f'{t0}-{t1}'
    L.append(f'| {tr} | `{name}` | {ln:,} | {l5} | {l1} | {by} | {what} | {doc} | {h} |')
L += ['', '## Notes', '',
 '* The 1MB build loads the common graphics files once at start-up through a staging area at `$80`',
 '  and keeps them; the 512K build reloads tracks 37-56 at every level start.',
 '* The per-level tile file is reloaded at every level start in both builds.',
 '* Tracks 64-81 (1MB) and 126-131 (512K) hold the two versions of the sound driver; each build loads only its own.',
 '* Tracks 17-32 and 110-125 are the two builds of the main program; the bootblock loads one of them.']
open('disk/FILES.md', 'w').write('\n'.join(L) + '\n')

M = ['# Disk map', '',
 'Ghosts\'n Goblins (Elite, 1990, v3) - 84 cylinders x 2 heads = tracks 0-167 (track = cylinder*2 + head).', '',
 '* **Track 0**: standard AmigaDOS track (11 sectors). Sectors 0-1 = bootblock/loader, 2-10 = filler.',
 '* **Tracks 1-131**: custom long-track format, one block per track: DSKSYNC `$A245` (after a `$4489`),',
 '  track number word, `$62A` longs (6,312 bytes) of odd/even MFM data, checksum long = NOT(sum).',
 '  The tracks are ~105,550 bits long (a standard track is ~100,000), which is the copy protection.',
 '* **Tracks 132-167**: unformatted.', '',
 '| Track | Cyl | Head | Contents | Part | Unused bytes at end (non-zero) |', '|---:|---:|---:|---|---|---|',
 '| 0 | 0 | 0 | `t000_bootblock.bin` (AmigaDOS bootblock) + filler | - | - |']
for tr in range(1, 168):
    if tr in owner:
        name, k, nt, slack, nz = owner[tr]
        sl = f'{slack} ({nz})' if slack else ''
        M.append(f'| {tr} | {tr // 2} | {tr % 2} | `{name}` | {k + 1}/{nt} | {sl} |')
    else:
        M.append(f'| {tr} | {tr // 2} | {tr % 2} | {"unformatted" if tr >= 132 else "?"} | | |')
open('disk/DISKMAP.md', 'w').write('\n'.join(M) + '\n')
print('files', len(rows) + 1, 'tracks mapped', len(owner) + 1)
