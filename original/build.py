"""Assemble the original game's three programs and check them against the originals' SHA-1 -
the same as build.sh, for any system (Windows included: no shell needed).

  python3 build.py        (python or py on Windows; run from anywhere)

The assembler is vasmm68k_mot on the PATH, or the program the VASM environment variable names
(for example VASM=C:\\Tools\\vasmm68k_mot.exe)."""
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VASM = os.environ.get('VASM', 'vasmm68k_mot')
PROGRAMS = [  # output, source, extra options, SHA-1 of the original
    ('main.bin', 'gng_main.s', [], '2628a93c164a5a8791272c146053b0afb3ddcf14'),
    ('boot.bin', 'gng_boot.s', [], '0bf93a4078bf317fa2774b4b973e1c79c0060227'),
    ('main_1mb.bin', 'gng_main.s', ['-DBUILD_1MB=1'], 'e44347679297d5d864ae7b0da689714970e261ad'),
]


def main():
    ok = True
    for out, src, opts, sha in PROGRAMS:
        cmd = [VASM, '-Fbin', '-m68000', '-no-opt', '-quiet'] + opts + ['-o', out, src]
        try:
            r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        except FileNotFoundError:
            sys.exit(f'{VASM} not found: put vasmm68k_mot on the PATH, or set VASM to its full path')
        if r.returncode:
            sys.exit(f'{out}: vasm failed\n{r.stdout}{r.stderr}')
        got = hashlib.sha1(open(os.path.join(HERE, out), 'rb').read()).hexdigest()
        print(f'{out}: OK' if got == sha else f'{out}: MISMATCH ({got})')
        ok &= got == sha
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
