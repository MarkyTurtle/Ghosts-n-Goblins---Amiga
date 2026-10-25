# Building

How to install what you need on Windows or Linux, then build and test both versions of the game:

* **`original/`**: the original game. Its sources reassemble byte-identical to the original disk.
* **`enhanced/`**: the enhanced game. Building it makes a playable disk image (ADF).

Ready-made enhanced disks are attached to each
[release](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/releases/latest). You only
need these steps to build from the source.

These steps are run automatically on Windows and Linux by the repository's GitHub Actions:
[original](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/original.yml) and [enhanced](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/enhanced.yml)
(`.github/workflows/`; vasm is built by `.github/actions/vasm`). If something here doesn't work
for you, their runs are a working example to compare with.

## What you need

| Tool | Needed for | Versions |
|---|---|---|
| vasm (`vasmm68k_mot`): the 68000 assembler with Motorola syntax | every build | 2.0f. Built from its source, because there are no prebuilt binaries for Windows or Linux (steps below) |
| A C compiler, to build vasm | building vasm | Linux: gcc (`build-essential`). Windows: Visual Studio 2022 Build Tools (`cl`, `nmake`) |
| [Python](https://www.python.org/) | the enhanced build, the tests, the tools | **3.11, 3.12 or 3.13**, 64-bit. Tested with 3.11.17, 3.12.3 and 3.13.16 |
| Python packages: `requirements.txt` | see below | unicorn 2.1.4; numpy 2.4.6-2.5.4; scipy 1.17.1-1.18.1; Pillow 12.3.0-13.0.0; capstone 5.0.7 (the versions tested) |
| [Git](https://git-scm.com/) | getting the source (and vasm's, the easy way) | any recent version |
| An Amiga emulator and a Kickstart ROM | playing the disk | [WinUAE](https://www.winuae.net/) (Windows), [FS-UAE](https://fs-uae.net/) or [Amiberry](https://github.com/BlitterStudio/amiberry) (Linux). Kickstart ROMs are copyrighted: [Amiga Forever](https://www.amigaforever.com/) sells them legally. The game needs Kickstart 1.3 or later |

Which Python package each part needs (`pip install -r requirements.txt` installs them all):

| Package | Used by |
|---|---|
| `scipy`, `numpy` | building the enhanced disk: `enhanced/sound/tools/make_music_512k.py` resamples the 512K music |
| `unicorn` | the tests: the 68000 emulator that runs the game (`enhanced/tools`, `original/tools/verify`) |
| `pillow`, `numpy` | the emulator's screenshots, and the pictures in `original/render/` |
| `capstone` | the disassembly tools (`original/tools/trace.py`, `original/tools/compare_builds.py`, `original/tools/build1mb/`) |

Building only the original game needs just vasm and Python (no packages).

### Getting vasm's source

Either of these gives the vasm source; the steps below build it.

* **Its official site**, by Volker Barthelmann and Frank Wille:
  [sun.hasenbraten.de/vasm](http://sun.hasenbraten.de/vasm/), also at
  [compilers.de](http://www.compilers.de/vasm.html). Download *Last release source*
  (`vasm.tar.gz`) and unpack it (`tar xzf vasm.tar.gz`, which works in Linux, PowerShell and Git
  Bash). This gives a folder `vasm`.
* **A copy on GitHub**: a mirror of the official source, which the workflows use:
  ```
  git clone https://github.com/StarWolf3000/vasm-mirror.git vasm
  ```

## Linux

These steps are for Debian or Ubuntu. Other distributions have the same tools under similar
package names; on Arch, vasm is also in the AUR as `vasm`.

1. Install the compiler, Git and Python:
   ```
   sudo apt install build-essential git python3 python3-venv python3-pip
   ```
2. Build vasm, in the folder with its source (see *Getting vasm's source*):
   ```
   cd vasm
   make CPU=m68k SYNTAX=mot
   sudo cp vasmm68k_mot /usr/local/bin/
   ```
   `which vasmm68k_mot` should now print its path.
3. Get the source and the Python packages. The virtual environment keeps the packages to this
   project; newer Debian and Ubuntu releases require one for `pip`.
   ```
   git clone https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga.git
   cd Ghosts-n-Goblins---Amiga
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
   Run `. .venv/bin/activate` again in each new terminal before using the tools.

## Windows

There are two ways. WSL is the simpler one. The native way needs Visual Studio's C compiler to
build vasm.

### The simpler way: WSL (Linux on Windows)

In PowerShell as administrator, run `wsl --install`, restart, and open *Ubuntu* from the Start
menu. Then follow the [Linux](#linux) steps inside it. WinUAE runs on Windows and can open the
built disk from the WSL files at `\\wsl$\Ubuntu\home\<you>\...`.

### Native Windows

1. Install:
   * [Python](https://www.python.org/downloads/windows/) 3.11, 3.12 or 3.13 (64-bit), ticking
     *Add python.exe to PATH* in the installer;
   * [Git for Windows](https://git-scm.com/download/win);
   * [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022),
     with the *Desktop development with C++* workload. That workload includes the Windows SDK,
     which vasm's build needs.
2. Build vasm. Open **x64 Native Tools Command Prompt for VS 2022** from the Start menu (an
   ordinary prompt has no `cl` or `nmake`), go to the folder with vasm's source (see *Getting
   vasm's source*) and run:
   ```
   nmake /f Makefile.Win32 CPU=m68k SYNTAX=mot
   ```
   This makes `vasmm68k_mot.exe` in that folder. Then either:
   * copy it to a folder on your PATH, for example `C:\Tools` (added under *Start → "Edit the
     system environment variables" → Environment Variables → Path*); or
   * set `VASM` to its full path in each PowerShell session before building:
     `$env:VASM = "C:\path\to\vasm\vasmm68k_mot.exe"`.

   In a new PowerShell window, `vasmm68k_mot` should now print vasm's version and copyright,
   then wait for input: press Ctrl+C.
3. Get the source and the Python packages, in PowerShell:
   ```
   git clone https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga.git
   cd Ghosts-n-Goblins---Amiga
   py -3.13 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   Use whichever of 3.11, 3.12 or 3.13 you installed (`py --list` shows them). If PowerShell
   refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
   Run `.venv\Scripts\Activate.ps1` again in each new PowerShell window.

With the virtual environment active, `python` is the same command on Windows and Linux; the
commands below use it.

## Building the original game (`original/`)

```
cd original
python build.py
```
This assembles the 512K program, the 1MB program and the bootblock from `gng_main.s` and
`gng_boot.s`, and checks each against the original's SHA-1. It prints `main.bin: OK`,
`boot.bin: OK` and `main_1mb.bin: OK`. On Linux, `sh build.sh` does the same.

Another check, in `original`:
```
python tools/verify/checks.py      # the bug notes, run on the real code in the emulator
```
`original/README.md` describes the rest of the tools (the disassembly generator, the disk
tools, the renderers).

## Building the enhanced game (`enhanced/`)

```
python enhanced/build.py     # -> enhanced/build/gng_game.adf and gng_game_raster.adf
```
`enhanced/build.py` builds the game disk and the timing build's, and prints each one's SHA-1.
`--check SHA1` also checks the game disk against a SHA-1. It runs
`enhanced/tools/build_game.py`, which builds one disk; run that directly, in `enhanced/tools`,
for its options (below). Each `build_game.py` run does the following, in a few seconds:

* assembles the program, the bootblock and the BOB viewer;
* makes the 512K music package;
* writes the disk, then reads every file back from it.

It finishes with `gng_game.adf: 30 files, ... the files read back exactly`.

The program's source is `enhanced/src/gng_game.s`, with `support.s`, `scroller.s` and the other
files in `enhanced/src`: edit those, then build.

Options:

* `--raster` makes the timing build (`gng_game_raster.adf`);
* `--music-rate N/D` sets another quality for the 512K music;
* the others are listed in `enhanced/docs/FEATURES.md`, *Builds*.

After a build, `python make_docs.py` brings `enhanced/docs/DISK.md` and `MEMORY.md` up to date.

### Testing the enhanced game

The tests run the game in a 68000 emulator (Unicorn), side by side with the original. Build the
originals' reference programs once first:
```
python build_enh.py
```
Then, from `enhanced/tools`:
```
python compare_game.py 2500 2 --machine 512k --level 1 --teleport 150   # against the original
python test_menu.py
python test_jump.py
python test_cache.py
python test_display.py
python test_drive.py
python test_boot4489.py
python test_bootinfo.py
```
`compare_game.py` takes:

* the number of frames;
* a seed for the random input;
* a machine: `512k`, `1mb`, `ks13`, `slow` or `fast`;
* `--disk`, to read the disk image through the loader instead of loading files directly.

Each test prints `all as expected` (or `ok` per check). The longer ones take a few minutes.
`enhanced/docs/FEATURES.md`, *Testing*, says what each one checks.

## Troubleshooting

| What you see | What to do |
|---|---|
| `vasmm68k_mot not found: put vasmm68k_mot on the PATH, or set VASM to its full path` | vasm isn't on the PATH of this window. Open a new window after changing the PATH, or set `VASM` (Windows step 2). |
| `'nmake' is not recognized` or `'cl' is not recognized` | vasm must be built in the **x64 Native Tools Command Prompt for VS 2022**, not an ordinary prompt or PowerShell. |
| `Cannot open include file: 'windows.h'` (building vasm) | Add the Windows SDK in the Visual Studio Installer, under *Modify → Desktop development with C++*. |
| `python` opens the Microsoft Store, or isn't found | Use `py` until the virtual environment is active, or turn off the `python.exe` alias under *Settings → Apps → Advanced app settings → App execution aliases*. |
| `pip install` fails building `unicorn`, `numpy` or `scipy` from source | Your Python has no ready-made packages: use 64-bit Python 3.11, 3.12 or 3.13. |
| `ModuleNotFoundError: No module named 'unicorn'` (or `numpy`, `scipy`) | Activate the virtual environment first (`.venv\Scripts\Activate.ps1`, or `. .venv/bin/activate`). |
| `main.bin: MISMATCH` | vasm older than 2.0 may assemble differently, so check its version. Also check that `-no-opt` is used (it is in `build.py` and `build.sh`). |
| `git status` shows `enhanced/sound/gng_music_512k.s` (or another generated file) as changed after a build, but `git diff` shows nothing | The checkout has Windows line endings. That happens with a clone made before `.gitattributes` was added; the repository now keeps Linux line endings on every system. Check out the files again: `git rm -r --cached -q .` then `git reset --hard` (this discards uncommitted changes), or make a fresh clone. |

If you are stuck, compare with the runs of the [original](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/original.yml) and
[enhanced](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/enhanced.yml) workflows. They show every step on a clean Windows
and Linux machine, with its output.

## Making a release

1. If the game has changed since the last release, update `ADF_SHA1` at the top of
   `.github/workflows/enhanced.yml` to the new disk's SHA-1 (`python enhanced/build.py` prints
   it), so the enhanced workflow checks against the new disk.
2. On GitHub, under *Releases → Draft a new release*:
   * type a new tag (for example `V1.1`) and choose *Create new tag on publish*;
   * set the target to `main`;
   * write the notes, then *Publish release*.
3. The [release workflow](https://github.com/MarkyTurtle/Ghosts-n-Goblins---Amiga/actions/workflows/release.yml) then builds the disks from that tag
   and attaches them to the release, as `GhostsNGoblins_Enhanced_<tag>.adf` and
   `..._raster.adf`, after a few minutes. If it fails, run it again from the Actions tab
   (*release → Run workflow*, giving the tag); it replaces any disks it attached before.

## Playing the disk

Open `enhanced/build/gng_game.adf` (or a release's ADF) in DF0 of WinUAE, FS-UAE or Amiberry,
with any Amiga from an A500 with 512K up. With Kickstart 2.0 or later it also boots from
DF1-DF3, using the early startup menu (hold both mouse buttons at power-on). The disk is a
standard 880K ADF, so it can also be written to a real floppy.
