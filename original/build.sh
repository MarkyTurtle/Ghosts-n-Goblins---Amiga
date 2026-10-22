#!/bin/sh
# Assemble the sources (both main programs from gng_main.s) and verify they match the original binaries.
# Needs vasmm68k_mot (http://sun.hasenbraten.de/vasm/) on the PATH.
set -e
cd "$(dirname "$0")"
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -o main.bin gng_main.s
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -o boot.bin gng_boot.s
vasmm68k_mot -Fbin -m68000 -no-opt -quiet -DBUILD_1MB=1 -o main_1mb.bin gng_main.s
check() { s=$(sha1sum "$1" | cut -d' ' -f1); [ "$s" = "$2" ] && echo "$1: OK" || { echo "$1: MISMATCH ($s)"; exit 1; }; }
check main.bin 2628a93c164a5a8791272c146053b0afb3ddcf14
check boot.bin 0bf93a4078bf317fa2774b4b973e1c79c0060227
check main_1mb.bin e44347679297d5d864ae7b0da689714970e261ad
