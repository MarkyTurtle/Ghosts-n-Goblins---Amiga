"""Build the enhanced game's disks in one command - the same as original/build.py, for the
enhanced game, on any system (Windows included):

  python3 build.py              (python or py on Windows; run from anywhere)

It runs tools/build_game.py twice: the game (build/gng_game.adf) and the timing build
(--raster: build/gng_game_raster.adf), and prints each disk's SHA-1. With --check SHA1, it also
checks the game disk against that SHA-1 (the build workflow uses it). The assembler is
vasmm68k_mot on the PATH, or the program the VASM environment variable names.

The program's source is src/gng_game.s with the other files in src/; tools/build_game.py
describes the build (the sound packages, the level files, the disk)."""
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, 'tools')
DISKS = [('the game', [], 'gng_game.adf'), ('the timing build', ['--raster'], 'gng_game_raster.adf')]


def main(args):
    expect = args[args.index('--check') + 1].lower() if '--check' in args else None
    shas = {}
    for what, opts, adf in DISKS:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, 'build_game.py')] + opts, cwd=TOOLS,
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f'{what}: the build failed\n{r.stdout}{r.stderr}')
        path = os.path.join(HERE, 'build', adf)
        shas[adf] = hashlib.sha1(open(path, 'rb').read()).hexdigest()
        print(f'{r.stdout.strip().splitlines()[-1]}')
        print(f'  {os.path.relpath(path, os.path.join(HERE, ".."))}  SHA-1 {shas[adf]}')
    if expect:
        if shas['gng_game.adf'] != expect:
            print(f'gng_game.adf: MISMATCH (expected {expect})')
            return 1
        print('gng_game.adf: OK (the expected SHA-1)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
