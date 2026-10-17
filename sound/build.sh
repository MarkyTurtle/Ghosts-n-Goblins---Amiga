#!/bin/sh
# Reassemble both sound files and compare with the originals (needs vasmm68k_mot).
set -e
cd "$(dirname "$0")"
for n in gng_sfx_512k:sfx_512k gng_music_1mb:music_1mb; do
  src=${n%%:*}; ref=${n##*:}
  vasmm68k_mot -Fbin -m68000 -no-opt -quiet -o $src.bin $src.s
  cmp $src.bin bin/$ref.hunk && echo "$src: identical to bin/$ref.hunk"
  rm -f $src.bin
done
