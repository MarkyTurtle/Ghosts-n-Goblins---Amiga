# Disk files

Every file the game loads, extracted from the decoded tracks (`bin/tracks/`) into `disk/files/`.
Files are listed in the 512K build's file table at `FileTable` (`$7F9C`), except the bootblock loads,
the 1MB-only music file and the main programs. A custom track holds 6,312 bytes of data.

| Tracks | File | Bytes | Load (512K) | Load (1MB) | Loaded by | Contents | See | SHA-1 |
|---|---|---:|---|---|---|---|---|---|
| 0 | `t000_bootblock.bin` | 1,024 | Kickstart → loader at `$7FC00` | same | Kickstart | AmigaDOS bootblock containing the whole trackloader; rest of track 0 is filler | gng_boot.s | 0bf93a4078bf |
| 1-16 | `t001-016_loading_screen.bin` | 99,072 | $60000 | $60000 | bootblock | Loading screen: 256-px-wide HAM6 interlaced picture (interleaved planes) + palette | gng_boot.s, render/out/loadscreen.png | ed2af9b76028 |
| 17-32 | `t017-032_main_1mb.hunk` | 100,992 | - | ExecBase&$FFF80000 or $80000 | bootblock (expanded memory) | Main program, 1MB build (base-relative), hunk header left in place | bin/main_1mb.bin, tools/compare_builds.py | e44347679297 |
| 33-36 | `t033-036_arthur_sprites.bin` | 21,504 | $37468 | $80 (staging) | Start (FileTable+0) | Arthur's hardware-sprite frames: 42 x 32x32, 4 planes; mirrored copies built at start-up | gng_main.s Start, render/out/arthur.png | 937299d96d6f |
| 37 | `t037_small_bob_sets.bin` | 3,360 | $311E8 (BOB_GFX_A) | $80 (staging) | LoadLevel (512K: every level) | 10 single-image item/scenery BOBs (coin, money bag, stone block, grass raft, rock, 3 gravestones, boulder and ice platforms); per-level subset selected by LevelSmallBobMask | gng_main.s LoadLevel | 279286ff5e3a |
| 38-56 | `t038-056_enemy_bobs.bin` | 118,850 | $37468 | $80 (staging) | LoadLevel (512K: every level) | 21 enemy BOB sets (BobSetOffsets/BobSetSizes); LoadLevel copies the sets each level needs | README Data formats, render/out/bobs.png | 7a56ff471016 |
| 57 | `t057_item_gfx_part2.bin` | 3,750 | $1CF8E | $80 (staging) | Start | Tail of the weapon / pickup / effect BOB block (continues track 59) | render/out/item_gfx.png | d148e91e5509 |
| 58 | `t058_enemy_shot_gfx.bin` | 4,660 | $1A298 | $80 (staging) | Start | Enemy projectile BOBs (fireballs, eyeballs, sparks, orbs); frame table $9002 | render/out/enemy_shot_gfx.png | a7dddfa96cca |
| 59-60 | `t059-060_item_gfx.bin` | 6,850 | $1B4CC | $80 (staging) | Start | Weapon, pickup and effect BOBs (lance, dagger, axe, torch, cross, armour, treasure, key, explosions); frame table $908E | render/out/item_gfx.png | e75163677284 |
| 61 | `t061_font.bin` | 6,208 | $37468 -> MASK_BUF $28234 | $80 (staging) | Start | Font: every other byte is used (16 bytes per character) | gng_main.s PrintChar | f7fdd712f7eb |
| 62-63 | `t062-063_progress_map.rle` | 7,516 | $311E8 | $80 (staging) | ProgressMap | Between-level map picture, ByteRun1-style RLE: 80 rows x 5 planes x (4+44) bytes | render/out/progress_map.png | 215a4f93cf44 |
| 64-81 | `t064-081_music_1mb.hunk` | 111,508 | - | $3604C | Start (1MB build only) | Sound driver + 15 tunes + 30 sound effects | sound/gng_music_1mb.s, sound/SOUND.md | 7c0f4fd2ad51 |
| 82-83 | `t082-083_copyright_screen.rle` | 9,726 | $4DC68 | $16880 | Start | FAST "Copyright Notice / Warning!" anti-piracy screen, RLE: 224 rows x 5 planes x (4+32) bytes; shown 10 s at boot | render/out/copyright_screen.png | e0975ea4579b |
| 84-88 | `t084-088_level0_tiles.bin` | 29,760 | $65548 | $573E0 | LoadLevel | Level 0 tiles (186 x 16x16, 5 planes, line-interleaved) | render/out/level0.png | f1c915e76abf |
| 89-96 | `t089-096_level1_tiles.bin` | 49,440 | $65548 | $573E0 | LoadLevel | Level 1 tiles (309, second bank for cells $1D/$1F) | render/out/level1.png | 19b5288ab3af |
| 97-100 | `t097-100_level2_tiles.bin` | 21,600 | $65548 | $573E0 | LoadLevel | Level 2 tiles (135) | render/out/level2.png | 3b0ab743ad47 |
| 101-103 | `t101-103_level3_tiles.bin` | 18,560 | $65548 | $573E0 | LoadLevel | Level 3 tiles (116) | render/out/level3.png | 7b20faba470a |
| 104-105 | `t104-105_level4_tiles.bin` | 10,080 | $65548 | $573E0 | LoadLevel | Level 4 tiles (63) | render/out/level4.png | 034ac877c557 |
| 106-107 | `t106-107_level5_tiles.bin` | 10,720 | $65548 | $573E0 | LoadLevel | Level 5 tiles (67) | render/out/level5.png | a92e8d6d22c9 |
| 108-109 | `t108-109_level6_tiles.bin` | 6,560 | $65548 | $573E0 | LoadLevel | Level 6 tiles (41) | render/out/level6.png | e7baa8e24ad3 |
| 110-125 | `t110-125_main_512k.hunk` | 100,992 | $80 | - | bootblock (512K) | Main program, 512K build, pre-relocated for $80, hunk header left in place | gng_main.s (byte-identical source) | 2628a93c164a |
| 126-131 | `t126-131_sfx_512k.hunk` | 32,100 | $28E54 | - | Start (512K build only) | Sound driver + 30 sound effects (no music) | sound/gng_sfx_512k.s, sound/SOUND.md | c6b9289691f4 |

## Notes

* The 1MB build loads the common graphics files once at start-up through a staging area at `$80`
  and keeps them; the 512K build reloads tracks 37-56 at every level start.
* The per-level tile file is reloaded at every level start in both builds.
* Tracks 64-81 (1MB) and 126-131 (512K) hold the two versions of the sound driver; each build loads only its own.
* Tracks 17-32 and 110-125 are the two builds of the main program; the bootblock loads one of them.
