# The enhanced game: documentation

| Document | |
|---|---|
| [FEATURES.md](FEATURES.md) | every feature of the enhanced game, how to play and build it, how it is tested - **start here** |
| [MEMORY.md](MEMORY.md) | the memory layout on each kind of machine (generated from the build by `tools/make_docs.py`) |
| [DISK.md](DISK.md) | the disk: bootblock, file table, every file with its offset, size and load address; booting (generated) |
| [FORMATS.md](FORMATS.md) | the format of every file and of the data the game builds from them |
| [SCROLLER.md](SCROLLER.md) | the development log: how each feature was made, measured and tested, in order (older sections describe earlier builds) |

Elsewhere: `../../docs/TODO.md` (what is done, what is left, with measurements),
`../../README.md` (the original game's disassembly, its formats and findings),
`../../docs/GLOBALS.md` and `XREF.md` (every global and who uses it),
`../../sound/SOUND.md` (the sound driver and its data).

Build and check (needs [vasm](http://sun.hasenbraten.de/vasm/) as `vasmm68k_mot`, Python 3 with
`unicorn`, `numpy`, `Pillow`, and `scipy` for the music package; installing them on Windows and
Linux: [`../../docs/BUILDING.md`](../../docs/BUILDING.md)):

```
cd enhanced/tools
python3 make_game.py            # src/gng_game.s from ../../gng_main.s (after changing either)
python3 build_game.py           # ../build/gng_game.adf  (--raster, --nasty-wait, --music-rate N/D)
python3 make_docs.py            # ../docs/DISK.md, MEMORY.md
python3 compare_game.py 2500 2 --machine 512k --level 1 --teleport 150   # against the original
python3 test_menu.py; python3 test_jump.py; python3 test_cache.py; python3 test_boot4489.py
```
