# Disk map

Ghosts'n Goblins (Elite, 1990, v3) - 84 cylinders x 2 heads = tracks 0-167 (track = cylinder*2 + head).

* **Track 0**: standard AmigaDOS track (11 sectors). Sectors 0-1 = bootblock/loader, 2-10 = filler.
* **Tracks 1-131**: custom long-track format, one block per track: DSKSYNC `$A245` (after a `$4489`),
  track number word, `$62A` longs (6,312 bytes) of odd/even MFM data, checksum long = NOT(sum).
  The tracks are ~105,550 bits long (a standard track is ~100,000), which is the copy protection.
* **Tracks 132-167**: unformatted.

| Track | Cyl | Head | Contents | Part | Unused bytes at end (non-zero) |
|---:|---:|---:|---|---|---|
| 0 | 0 | 0 | `t000_bootblock.bin` (AmigaDOS bootblock) + filler | - | - |
| 1 | 0 | 1 | `t001-016_loading_screen.bin` | 1/16 |  |
| 2 | 1 | 0 | `t001-016_loading_screen.bin` | 2/16 |  |
| 3 | 1 | 1 | `t001-016_loading_screen.bin` | 3/16 |  |
| 4 | 2 | 0 | `t001-016_loading_screen.bin` | 4/16 |  |
| 5 | 2 | 1 | `t001-016_loading_screen.bin` | 5/16 |  |
| 6 | 3 | 0 | `t001-016_loading_screen.bin` | 6/16 |  |
| 7 | 3 | 1 | `t001-016_loading_screen.bin` | 7/16 |  |
| 8 | 4 | 0 | `t001-016_loading_screen.bin` | 8/16 |  |
| 9 | 4 | 1 | `t001-016_loading_screen.bin` | 9/16 |  |
| 10 | 5 | 0 | `t001-016_loading_screen.bin` | 10/16 |  |
| 11 | 5 | 1 | `t001-016_loading_screen.bin` | 11/16 |  |
| 12 | 6 | 0 | `t001-016_loading_screen.bin` | 12/16 |  |
| 13 | 6 | 1 | `t001-016_loading_screen.bin` | 13/16 |  |
| 14 | 7 | 0 | `t001-016_loading_screen.bin` | 14/16 |  |
| 15 | 7 | 1 | `t001-016_loading_screen.bin` | 15/16 |  |
| 16 | 8 | 0 | `t001-016_loading_screen.bin` | 16/16 | 1920 (1069) |
| 17 | 8 | 1 | `t017-032_main_1mb.hunk` | 1/16 |  |
| 18 | 9 | 0 | `t017-032_main_1mb.hunk` | 2/16 |  |
| 19 | 9 | 1 | `t017-032_main_1mb.hunk` | 3/16 |  |
| 20 | 10 | 0 | `t017-032_main_1mb.hunk` | 4/16 |  |
| 21 | 10 | 1 | `t017-032_main_1mb.hunk` | 5/16 |  |
| 22 | 11 | 0 | `t017-032_main_1mb.hunk` | 6/16 |  |
| 23 | 11 | 1 | `t017-032_main_1mb.hunk` | 7/16 |  |
| 24 | 12 | 0 | `t017-032_main_1mb.hunk` | 8/16 |  |
| 25 | 12 | 1 | `t017-032_main_1mb.hunk` | 9/16 |  |
| 26 | 13 | 0 | `t017-032_main_1mb.hunk` | 10/16 |  |
| 27 | 13 | 1 | `t017-032_main_1mb.hunk` | 11/16 |  |
| 28 | 14 | 0 | `t017-032_main_1mb.hunk` | 12/16 |  |
| 29 | 14 | 1 | `t017-032_main_1mb.hunk` | 13/16 |  |
| 30 | 15 | 0 | `t017-032_main_1mb.hunk` | 14/16 |  |
| 31 | 15 | 1 | `t017-032_main_1mb.hunk` | 15/16 |  |
| 32 | 16 | 0 | `t017-032_main_1mb.hunk` | 16/16 |  |
| 33 | 16 | 1 | `t033-036_arthur_sprites.bin` | 1/4 |  |
| 34 | 17 | 0 | `t033-036_arthur_sprites.bin` | 2/4 |  |
| 35 | 17 | 1 | `t033-036_arthur_sprites.bin` | 3/4 |  |
| 36 | 18 | 0 | `t033-036_arthur_sprites.bin` | 4/4 | 3744 (1694) |
| 37 | 18 | 1 | `t037_small_bob_sets.bin` | 1/1 | 2952 (2555) |
| 38 | 19 | 0 | `t038-056_enemy_bobs.bin` | 1/19 |  |
| 39 | 19 | 1 | `t038-056_enemy_bobs.bin` | 2/19 |  |
| 40 | 20 | 0 | `t038-056_enemy_bobs.bin` | 3/19 |  |
| 41 | 20 | 1 | `t038-056_enemy_bobs.bin` | 4/19 |  |
| 42 | 21 | 0 | `t038-056_enemy_bobs.bin` | 5/19 |  |
| 43 | 21 | 1 | `t038-056_enemy_bobs.bin` | 6/19 |  |
| 44 | 22 | 0 | `t038-056_enemy_bobs.bin` | 7/19 |  |
| 45 | 22 | 1 | `t038-056_enemy_bobs.bin` | 8/19 |  |
| 46 | 23 | 0 | `t038-056_enemy_bobs.bin` | 9/19 |  |
| 47 | 23 | 1 | `t038-056_enemy_bobs.bin` | 10/19 |  |
| 48 | 24 | 0 | `t038-056_enemy_bobs.bin` | 11/19 |  |
| 49 | 24 | 1 | `t038-056_enemy_bobs.bin` | 12/19 |  |
| 50 | 25 | 0 | `t038-056_enemy_bobs.bin` | 13/19 |  |
| 51 | 25 | 1 | `t038-056_enemy_bobs.bin` | 14/19 |  |
| 52 | 26 | 0 | `t038-056_enemy_bobs.bin` | 15/19 |  |
| 53 | 26 | 1 | `t038-056_enemy_bobs.bin` | 16/19 |  |
| 54 | 27 | 0 | `t038-056_enemy_bobs.bin` | 17/19 |  |
| 55 | 27 | 1 | `t038-056_enemy_bobs.bin` | 18/19 |  |
| 56 | 28 | 0 | `t038-056_enemy_bobs.bin` | 19/19 | 1078 (1007) |
| 57 | 28 | 1 | `t057_item_gfx_part2.bin` | 1/1 | 2562 (2197) |
| 58 | 29 | 0 | `t058_enemy_shot_gfx.bin` | 1/1 | 1652 (675) |
| 59 | 29 | 1 | `t059-060_item_gfx.bin` | 1/2 |  |
| 60 | 30 | 0 | `t059-060_item_gfx.bin` | 2/2 | 5774 (2222) |
| 61 | 30 | 1 | `t061_font.bin` | 1/1 | 104 (45) |
| 62 | 31 | 0 | `t062-063_progress_map.rle` | 1/2 |  |
| 63 | 31 | 1 | `t062-063_progress_map.rle` | 2/2 | 5108 (1993) |
| 64 | 32 | 0 | `t064-081_music_1mb.hunk` | 1/18 |  |
| 65 | 32 | 1 | `t064-081_music_1mb.hunk` | 2/18 |  |
| 66 | 33 | 0 | `t064-081_music_1mb.hunk` | 3/18 |  |
| 67 | 33 | 1 | `t064-081_music_1mb.hunk` | 4/18 |  |
| 68 | 34 | 0 | `t064-081_music_1mb.hunk` | 5/18 |  |
| 69 | 34 | 1 | `t064-081_music_1mb.hunk` | 6/18 |  |
| 70 | 35 | 0 | `t064-081_music_1mb.hunk` | 7/18 |  |
| 71 | 35 | 1 | `t064-081_music_1mb.hunk` | 8/18 |  |
| 72 | 36 | 0 | `t064-081_music_1mb.hunk` | 9/18 |  |
| 73 | 36 | 1 | `t064-081_music_1mb.hunk` | 10/18 |  |
| 74 | 37 | 0 | `t064-081_music_1mb.hunk` | 11/18 |  |
| 75 | 37 | 1 | `t064-081_music_1mb.hunk` | 12/18 |  |
| 76 | 38 | 0 | `t064-081_music_1mb.hunk` | 13/18 |  |
| 77 | 38 | 1 | `t064-081_music_1mb.hunk` | 14/18 |  |
| 78 | 39 | 0 | `t064-081_music_1mb.hunk` | 15/18 |  |
| 79 | 39 | 1 | `t064-081_music_1mb.hunk` | 16/18 |  |
| 80 | 40 | 0 | `t064-081_music_1mb.hunk` | 17/18 |  |
| 81 | 40 | 1 | `t064-081_music_1mb.hunk` | 18/18 | 2108 (1764) |
| 82 | 41 | 0 | `t082-083_copyright_screen.rle` | 1/2 |  |
| 83 | 41 | 1 | `t082-083_copyright_screen.rle` | 2/2 | 2898 (1182) |
| 84 | 42 | 0 | `t084-088_level0_tiles.bin` | 1/5 |  |
| 85 | 42 | 1 | `t084-088_level0_tiles.bin` | 2/5 |  |
| 86 | 43 | 0 | `t084-088_level0_tiles.bin` | 3/5 |  |
| 87 | 43 | 1 | `t084-088_level0_tiles.bin` | 4/5 |  |
| 88 | 44 | 0 | `t084-088_level0_tiles.bin` | 5/5 | 1800 (1785) |
| 89 | 44 | 1 | `t089-096_level1_tiles.bin` | 1/8 |  |
| 90 | 45 | 0 | `t089-096_level1_tiles.bin` | 2/8 |  |
| 91 | 45 | 1 | `t089-096_level1_tiles.bin` | 3/8 |  |
| 92 | 46 | 0 | `t089-096_level1_tiles.bin` | 4/8 |  |
| 93 | 46 | 1 | `t089-096_level1_tiles.bin` | 5/8 |  |
| 94 | 47 | 0 | `t089-096_level1_tiles.bin` | 6/8 |  |
| 95 | 47 | 1 | `t089-096_level1_tiles.bin` | 7/8 |  |
| 96 | 48 | 0 | `t089-096_level1_tiles.bin` | 8/8 | 1056 (1028) |
| 97 | 48 | 1 | `t097-100_level2_tiles.bin` | 1/4 |  |
| 98 | 49 | 0 | `t097-100_level2_tiles.bin` | 2/4 |  |
| 99 | 49 | 1 | `t097-100_level2_tiles.bin` | 3/4 |  |
| 100 | 50 | 0 | `t097-100_level2_tiles.bin` | 4/4 | 3648 (1599) |
| 101 | 50 | 1 | `t101-103_level3_tiles.bin` | 1/3 |  |
| 102 | 51 | 0 | `t101-103_level3_tiles.bin` | 2/3 |  |
| 103 | 51 | 1 | `t101-103_level3_tiles.bin` | 3/3 | 376 (288) |
| 104 | 52 | 0 | `t104-105_level4_tiles.bin` | 1/2 |  |
| 105 | 52 | 1 | `t104-105_level4_tiles.bin` | 2/2 | 2544 (1687) |
| 106 | 53 | 0 | `t106-107_level5_tiles.bin` | 1/2 |  |
| 107 | 53 | 1 | `t106-107_level5_tiles.bin` | 2/2 | 1904 (1195) |
| 108 | 54 | 0 | `t108-109_level6_tiles.bin` | 1/2 |  |
| 109 | 54 | 1 | `t108-109_level6_tiles.bin` | 2/2 | 6064 (4165) |
| 110 | 55 | 0 | `t110-125_main_512k.hunk` | 1/16 |  |
| 111 | 55 | 1 | `t110-125_main_512k.hunk` | 2/16 |  |
| 112 | 56 | 0 | `t110-125_main_512k.hunk` | 3/16 |  |
| 113 | 56 | 1 | `t110-125_main_512k.hunk` | 4/16 |  |
| 114 | 57 | 0 | `t110-125_main_512k.hunk` | 5/16 |  |
| 115 | 57 | 1 | `t110-125_main_512k.hunk` | 6/16 |  |
| 116 | 58 | 0 | `t110-125_main_512k.hunk` | 7/16 |  |
| 117 | 58 | 1 | `t110-125_main_512k.hunk` | 8/16 |  |
| 118 | 59 | 0 | `t110-125_main_512k.hunk` | 9/16 |  |
| 119 | 59 | 1 | `t110-125_main_512k.hunk` | 10/16 |  |
| 120 | 60 | 0 | `t110-125_main_512k.hunk` | 11/16 |  |
| 121 | 60 | 1 | `t110-125_main_512k.hunk` | 12/16 |  |
| 122 | 61 | 0 | `t110-125_main_512k.hunk` | 13/16 |  |
| 123 | 61 | 1 | `t110-125_main_512k.hunk` | 14/16 |  |
| 124 | 62 | 0 | `t110-125_main_512k.hunk` | 15/16 |  |
| 125 | 62 | 1 | `t110-125_main_512k.hunk` | 16/16 |  |
| 126 | 63 | 0 | `t126-131_sfx_512k.hunk` | 1/6 |  |
| 127 | 63 | 1 | `t126-131_sfx_512k.hunk` | 2/6 |  |
| 128 | 64 | 0 | `t126-131_sfx_512k.hunk` | 3/6 |  |
| 129 | 64 | 1 | `t126-131_sfx_512k.hunk` | 4/6 |  |
| 130 | 65 | 0 | `t126-131_sfx_512k.hunk` | 5/6 |  |
| 131 | 65 | 1 | `t126-131_sfx_512k.hunk` | 6/6 | 5772 (4601) |
| 132 | 66 | 0 | unformatted | | |
| 133 | 66 | 1 | unformatted | | |
| 134 | 67 | 0 | unformatted | | |
| 135 | 67 | 1 | unformatted | | |
| 136 | 68 | 0 | unformatted | | |
| 137 | 68 | 1 | unformatted | | |
| 138 | 69 | 0 | unformatted | | |
| 139 | 69 | 1 | unformatted | | |
| 140 | 70 | 0 | unformatted | | |
| 141 | 70 | 1 | unformatted | | |
| 142 | 71 | 0 | unformatted | | |
| 143 | 71 | 1 | unformatted | | |
| 144 | 72 | 0 | unformatted | | |
| 145 | 72 | 1 | unformatted | | |
| 146 | 73 | 0 | unformatted | | |
| 147 | 73 | 1 | unformatted | | |
| 148 | 74 | 0 | unformatted | | |
| 149 | 74 | 1 | unformatted | | |
| 150 | 75 | 0 | unformatted | | |
| 151 | 75 | 1 | unformatted | | |
| 152 | 76 | 0 | unformatted | | |
| 153 | 76 | 1 | unformatted | | |
| 154 | 77 | 0 | unformatted | | |
| 155 | 77 | 1 | unformatted | | |
| 156 | 78 | 0 | unformatted | | |
| 157 | 78 | 1 | unformatted | | |
| 158 | 79 | 0 | unformatted | | |
| 159 | 79 | 1 | unformatted | | |
| 160 | 80 | 0 | unformatted | | |
| 161 | 80 | 1 | unformatted | | |
| 162 | 81 | 0 | unformatted | | |
| 163 | 81 | 1 | unformatted | | |
| 164 | 82 | 0 | unformatted | | |
| 165 | 82 | 1 | unformatted | | |
| 166 | 83 | 0 | unformatted | | |
| 167 | 83 | 1 | unformatted | | |
