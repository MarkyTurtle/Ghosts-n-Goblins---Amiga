# Building

How to install what you need on Windows or Linux, then build and test both versions of the game:

* **`main`**: the original game. Its sources reassemble byte-identical to the original disk.
* **`enhanced/main`**: the enhanced game. Building it makes a playable disk image (ADF).

Ready-made enhanced disks are attached to each
[release](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/releases/latest). You only
need these steps to build from the source.

## What you need

| Tool | Needed for | Notes |
|---|---|---|
| [vasm](http://sun.hasenbraten.de/vasm/) (`vasmm68k_mot`), the 68000 assembler with Motorola syntax | every build | Built from its source: there are no prebuilt binaries for Windows or Linux (steps below). Tested with vasm 2.0f |
| [Python](https://www.python.org/) 3 | the enhanced build, its tests, the tools | Tested with Python 3.13; use 3.12 or later |
| Python packages `unicorn`, `numpy`, `pillow`, `scipy`, `capstone` | see below | Installed with `pip` |
| [Git](https://git-scm.com/) | getting the source | On Windows, Git for Windows also provides Git Bash (`sh`, `sha1sum`) for `build.sh` |
| An Amiga emulator and a Kickstart ROM | playing the disk | [WinUAE](https://www.winuae.net/) (Windows), [FS-UAE](https://fs-uae.net/) or [Amiberry](https://github.com/BlitterStudio/amiberry) (Linux). Kickstart ROMs are copyrighted: [Amiga Forever](https://www.amigaforever.com/) sells them legally. The game needs Kickstart 1.3 or later |

Which Python packages each part needs:

| Package | Used by |
|---|---|
| `scipy`, `numpy` | building the enhanced disk: `sound/tools/make_music_512k.py` resamples the 512K music |
| `unicorn` | the tests: the 68000 emulator that runs the game (`enhanced/tools`, `tools/verify`) |
| `pillow`, `numpy` | the emulator's screenshots, and the pictures in `render/` |
| `capstone` | the disassembly tools (`tools/trace.py`, `tools/compare_builds.py`, `tools/build1mb/`) |

Tested with unicorn 2.1.4, numpy 2.5.3, Pillow 12.3.0, scipy 1.18.1 and capstone 5.0.7.

## Linux

These steps are for Debian or Ubuntu; other distributions have the same tools under similar
package names (on Arch, vasm is in the AUR as `vasm`).

1. Install the compiler, Git and Python:
   ```
   sudo apt install build-essential git python3 python3-venv python3-pip
   ```
2. Build vasm. Download the source from the [vasm page](http://sun.hasenbraten.de/vasm/)
   (*Last release source*: `vasm.tar.gz`), then:
   ```
   tar xzf vasm.tar.gz
   cd vasm
   make CPU=m68k SYNTAX=mot
   sudo cp vasmm68k_mot /usr/local/bin/
   vasmm68k_mot        # prints its version: the check that it is on the PATH
   ```
3. Get the source and the Python packages. A virtual environment keeps the packages to this
   project; newer Debian and Ubuntu require one for `pip`.
   ```
   git clone https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga.git
   cd Ghosts-n-Goblins---Amiga
   python3 -m venv .venv
   . .venv/bin/activate
   pip install unicorn numpy pillow scipy capstone
   ```
   Run `. .venv/bin/activate` again in each new terminal before using the tools.

## Windows

There are two ways. WSL is the simpler one; the native way needs Visual Studio's C compiler
for vasm.

### The simpler way: WSL (Linux on Windows)

In PowerShell as administrator, run `wsl --install`, restart, and open *Ubuntu* from the Start
menu. Then follow the [Linux](#linux) steps inside it. WinUAE runs on Windows and can open the
built disk from the WSL files at `\\wsl$\Ubuntu\home\<you>\...`.

### Native Windows

1. Install:
   * [Python](https://www.python.org/downloads/windows/), ticking *Add python.exe to PATH*;
   * [Git for Windows](https://git-scm.com/download/win);
   * [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/),
     with the *Desktop development with C++* workload (for `cl` and `nmake`).
2. Build vasm. Download the source from the [vasm page](http://sun.hasenbraten.de/vasm/)
   (*Last release source*: `vasm.tar.gz`) and unpack it (`tar xzf vasm.tar.gz`, in PowerShell or
   Git Bash). Then open the *x64 Native Tools Command Prompt for VS*, `cd` into the `vasm`
   folder, and run:
   ```
   nmake /f Makefile.Win32 CPU=m68k SYNTAX=mot
   ```
   This makes `vasmm68k_mot.exe`. Put it in a folder on your PATH (for example `C:\Tools`, added
   under *Settings → System → About → Advanced system settings → Environment Variables*).
   Alternatively, leave it where it is and set `VASM` to its full path before building, in
   PowerShell:
   `$env:VASM = "C:\path\to\vasmm68k_mot.exe"`.
3. Get the source and the Python packages, in PowerShell:
   ```
   git clone https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga.git
   cd Ghosts-n-Goblins---Amiga
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install unicorn numpy pillow scipy capstone
   ```
   If PowerShell refuses to run `Activate.ps1`, run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

In the commands below, Windows uses `py` (or `python` inside the virtual environment) where
Linux uses `python3`.

## Building the original game (`main`)

```
git checkout main
sh build.sh
```
This assembles the 512K program, the 1MB program and the bootblock from `gng_main.s` and
`gng_boot.s`, and checks each against the original's SHA-1. It prints `main.bin: OK`,
`boot.bin: OK` and `main_1mb.bin: OK`. On Windows, run it from Git Bash, or run the same
assembler commands in PowerShell:
```
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -o main.bin gng_main.s
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -o boot.bin gng_boot.s
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -DBUILD_1MB=1 -o main_1mb.bin gng_main.s
Get-FileHash -Algorithm SHA1 main.bin, boot.bin, main_1mb.bin
```
The hashes to expect are in `build.sh`.

Other checks on `main`:
```
python3 tools/verify/checks.py      # the bug notes, run on the real code in the emulator
python3 tools/refdocs.py            # writes docs/GLOBALS.md and docs/XREF.md
```

## Building the enhanced game (`enhanced/main`)

```
git checkout enhanced/main
cd enhanced/tools
python3 make_game.py         # src/gng_game.s from the original source (only after changing it or the tools)
python3 build_game.py        # -> enhanced/build/gng_game.adf
```
`build_game.py` assembles the program, the bootblock and the BOB viewer, makes the 512K music
package and writes the disk, then reads every file back from it. It finishes with
`gng_game.adf: 30 files, ... the files read back exactly`. It takes a few seconds.

Options: `--raster` makes the timing build (`gng_game_raster.adf`), and `--music-rate N/D` sets
another quality for the 512K music. The other options are listed in
`enhanced/docs/FEATURES.md`, *Builds*. After a build, `python3 make_docs.py` brings
`enhanced/docs/DISK.md` and `MEMORY.md` up to date.

### Testing the enhanced game

The tests run the game in a 68000 emulator (Unicorn), side by side with the original. Build the
originals' reference programs once first:
```
python3 build_enh.py
```
Then, from `enhanced/tools`:
```
python3 compare_game.py 2500 2 --machine 512k --level 1 --teleport 150   # against the original
python3 test_menu.py
python3 test_jump.py
python3 test_cache.py
python3 test_display.py
python3 test_drive.py
python3 test_boot4489.py
python3 test_bootinfo.py
```
`compare_game.py` takes the number of frames, a seed for the random input and a machine (`512k`,
`1mb`, `ks13`, `slow`, `fast`); `--disk` reads the disk image through the loader instead of
loading files directly. Each test prints `all as expected` (or `ok` per check). The longer ones
take a few minutes. `enhanced/docs/FEATURES.md`, *Testing*, says what each one checks.

## Playing the disk

Open `enhanced/build/gng_game.adf` (or a release's ADF) in DF0 of WinUAE, FS-UAE or Amiberry,
with any Amiga from an A500 with 512K up. With Kickstart 2.0 or later it also boots from
DF1-DF3, using the early startup menu (hold both mouse buttons at power-on). The disk is a
standard 880K ADF, so it can also be written to a real floppy.
