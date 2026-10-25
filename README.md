# Ghosts'n Goblins (Elite, 1990) for the Amiga - enhanced, and the original annotated

[![original](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/original.yml/badge.svg)](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/original.yml)
[![enhanced](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/enhanced.yml/badge.svg)](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/enhanced.yml)

This repository holds two things, side by side:

* **[`enhanced/`](enhanced)**: an enhanced version of the game. It is one program for every
  Amiga from an A500 with 512K up, with smooth 50 fps scrolling, music on every machine, and a
  standard disk that boots from any drive.
* **[`original/`](original)**: the original game as a fully annotated disassembly. It
  reassembles byte-identical to the original disk, with tools, rendered graphics, the disk's
  files and notes on how the game works.

## Play it

Download the disk image (ADF) from the **[latest release](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/releases/latest)**.
Run it in an emulator ([WinUAE](https://www.winuae.net/), [FS-UAE](https://fs-uae.net/),
[Amiberry](https://github.com/BlitterStudio/amiberry)) or write it to a floppy. It needs an Amiga
with Kickstart 1.3 or later and 512K or more. With Kickstart 2.0 or later it also boots from
DF1-DF3: hold both mouse buttons at power-on to choose the drive.

## The enhanced game

What it adds, compared with the original (the full list, with how each feature works and how it
is tested: [`enhanced/docs/FEATURES.md`](enhanced/docs/FEATURES.md)):

* **One program for every machine.** The bootblock surveys the memory and leaves a description
  of the machine, and the program picks its features from it:
  * with 1MB of chip RAM, graphics caches and BOBs drawn with one blit;
  * on expanded 512K machines, the program moves into the slow / fast RAM, and a file cache.
* **Incremental scrolling** (a double-buffered corkscrew with a pristine background buffer)
  instead of the original's full redraws: no freezes, and drawing at 50 fps instead of 25.
* **Faster BOBs on 512K**: one-plane masks made when a level loads, and one-blit images as far
  as each level's memory goes.
* **Music on every machine**, including a plain 512K A500: the 1MB tunes are added to the 512K
  effects, with the tunes' samples at 3/4 of their rate on 512K.
* **A standard AmigaDOS-format disk** (880K ADF) with a file table, loaded with the
  [4489_byteloader](https://github.com/MarkyTurtle/4489_byteloader), from whichever drive it
  was booted from.
* **Two-button joysticks**: jump on the second button, or on up as in the original.
* **A title menu**: 1 or 2 players, the input setting, and a test page with:
  * the memory found and the cheat;
  * a sound test;
  * an arcade-style input test;
  * a sprite test;
  * with 1MB of chip RAM, a BOB viewer.
* **Less loading**: only each level's enemy sets are read, and machines with memory to spare
  keep the files they have read.
* **Clean changes of display** between a level and the progress map.
* **An original bug fixed**: `MapTileAt` read the program's own code as map cells for an object
  far below a level.

It is tested by running the enhanced program and the original side by side in a 68000 emulator,
with the same game state every frame, on every stage and machine. Each feature also has its own
tests, and the game was tried in WinUAE on an A500, A500 + 512K, A500+, A600 and A1200.

## Building

[`BUILDING.md`](BUILDING.md) lists what to install (vasm, Python and its packages) on Windows and
Linux, and how to build and test both versions:

* the original game: `python original/build.py`, which assembles the three programs and checks
  them against the originals' SHA-1;
* the enhanced game: `python enhanced/build.py`, which writes the disks
  (`enhanced/build/gng_game.adf` and the timing build) and prints their SHA-1.

They are tested with Python 3.11 to 3.13 and vasm 2.0f. GitHub Actions run both builds on Windows
and Linux whenever their folders change (the badges above):

* [original](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/original.yml): the three programs against the originals, and
  the bug-note checks;
* [enhanced](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/enhanced.yml): the disks, the tests, and the disks to download
  from each run's page;
* [release](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/release.yml): when a release is published, its disks are built
  and attached to it.

## Layout

| Folder | What it holds |
|---|---|
| `original/` | the annotated disassembly (`gng_main.s`, `gng_equates.i`, `gng_boot.s`), the original binaries and the disk's files, the tools that made and check it, rendered graphics, the sound driver and data, and the notes - start with [`original/README.md`](original/README.md) |
| `enhanced/src/` | the enhanced game's sources: `gng_game.s` (the program), `support.s` (its start-up, loading and cache code), `scroller.s` and `scroll.s`, the bootblock, the BOB viewer |
| `enhanced/tools/` | the build (`build_game.py`), the emulator harness and every test |
| `enhanced/disk/files/`, `enhanced/sound/`, `enhanced/data/` | the enhanced game's resources - graphics, sound packages and samples, level data - its own copies, taken from `original/` once (`enhanced/tools/take_resources.py`), so either game's can change without the other's; the build reads nothing from `original/` |
| `enhanced/docs/` | features, memory and disk layouts, file formats, the development log and the plan: [`enhanced/docs/README.md`](enhanced/docs/README.md) |
| `BUILDING.md` | what to install and how to build, on Windows and Linux |

The enhanced game's source started as a copy of the original's: `enhanced/src/gng_game.s` was
made from `original/gng_main.s` by a script. Since then it is edited directly, and `original/`
stays the original game. Each folder has its own `requirements.txt` (the Python packages it needs);
the one at the top installs both.

## Branches

`main` holds both games. New work goes on a branch of its own, is tried in WinUAE, merged here
and the branch deleted.

The enhanced game was developed on `enhanced/scroll` (later `enhanced/main`), with each feature
on a branch of its own (`enhanced/byteloader`, `music512`, `joystick`, `titlemenu`,
`musicquality`, `testmenu`, `memory`, `display`, `bootdrive`), up to release v1.0, and then
brought together with the original on `main`. Those branches are all merged and deleted; their
commits are all in `main`'s history, and the tag `V1.0` marks the release.

---

Ghosts'n Goblins is © Capcom; the Amiga version is by Elite Systems. This is an unofficial fan
project, made for study and preservation.
