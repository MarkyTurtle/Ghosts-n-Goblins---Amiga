# Ghosts'n Goblins (Elite, 1990) – sound driver and data

| File | Tracks | Load address | Size | Contents |
|---|---|---|---|---|
| `bin/sfx_512k.hunk` | 126-131 | `$28E54` | 32,100 bytes | driver + 30 sound effects (512K build) |
| `bin/music_1mb.hunk` | 64-81 | `$3604C` | 111,508 bytes | driver + 15 tunes + 30 sound effects (1MB build) |

Both are AmigaDOS hunk files (one code hunk, no `HUNK_END`) loaded raw by the game. The driver
starts at file offset `$20` and the game calls it through vector `$60`.

The sound is **Richard Frankish's music player** (Frankish is also credited as the game's
programmer) with music and effects by **Mark Cooksey**. It's a proprietary format, though the Wanted
Team's EaglePlayer "MarkCooksey" replayer supports variants of it.

## Sources

`gng_music_1mb.s` and `gng_sfx_512k.s` reassemble **byte-identical** to the files above:

```
vasmm68k_mot -Fbin -m68000 -no-opt -o music.bin gng_music_1mb.s
```

The music data is written with macros (`NOTE`, `REST`, `VOLUME`, `CALL`, `CALLN`, `RETURN`,
`ENDTRACK`, `JUMP`, `PORTA_ON`, `PORTA_OFF`). Every pointer is symbolic, and every sample is included
from `samples/*.raw`, so tunes can be edited and reassembled.

## Driver interface

`d0.l = (argument << 16) | command`, then `JSR file+$20`:

| Command | Routine | Effect |
|---|---|---|
| 0 | `CmdTick` | advance all voices one frame (the game calls it from its VBL interrupt) |
| 1 | `CmdPlayTune` | start tune *argument* on the 4 music voices |
| 2 | `CmdPlaySfx` | start effect *argument* on the 4 sound-effect voices |
| 3 | `CmdSetUserValue` | store *argument* in `DRV_UserValue`, which is never read |

There are **8 voices**: 4 music and 4 sound effect, and voice *n* uses Paula channel *n & 3*. The sfx
voices run first each tick and claim their channel (`DRV_SfxChans`). A music voice keeps advancing
through its data while its channel is claimed, but does not write to Paula. The music therefore stays
in time and comes back when the effect ends.

## Data layout (in file order)

1. `MusicTable` – 16 bytes per tune: 4 self-relative longs (one per channel; 0 = unused)
2. `SfxTable` – same format (in the 512K file it is at the same address as the empty `MusicTable`)
3. `InstrumentTable` – self-relative words to the instrument records
4. Instrument records (28 bytes, below), then the envelopes and the voice data (sequences and patterns)
5. `PatternTable` – **signed** self-relative words (patterns lie before the table)
6. `PitchTable` – 384 words, 8 octaves × 48 steps (4 per semitone), then a 0 word
7. `DriverVars` – 846 bytes of workspace (zero on disk): 4 bytes of flags, 8 voices × `$68`, the silent-sample pointer
8. `SampleBase` – a 64-byte silent sample, then a chain of samples: each has a 6-byte header
   (length.L in bytes, rate.W in Hz, not used by the driver) followed by signed 8-bit data

### Voice bytecode

| Byte(s) | Macro | Meaning |
|---|---|---|
| `$00-$5F` n, ins, dur, 0 | `NOTE` | note n (pitch index = (n + transpose) × 4), instrument, duration in ticks |
| `$60` hi, lo, 0 | `REST` | silence for a 16-bit duration |
| `$63` v | `VOLUME` | channel volume 0-255 |
| `$64` p, t | `CALL` | play pattern p transposed by t semitones |
| `$65` p, t, n | `CALLN` | play it n + 1 times |
| `$66` | `RETURN` | end of pattern (repeat or return) |
| `$67` | `ENDTRACK` | voice stops (channel gets the silent sample) |
| `$68` hi, lo | `JUMP` | signed offset from the `$68` byte; used to loop tunes |
| `$69` t | `PORTA_ON` | following notes glide from the previous pitch over t ticks |
| `$6B` | `PORTA_OFF` | glide off |
| `$61 $62 $6A $6C-$7F` | – | no-op (never used) |

Patterns nest up to 4 deep: each voice has a 40-byte call stack of 10-byte frames.

### Instrument record (28 bytes)

| Offset | Size | Field |
|---|---|---|
| +0 | L | attack sample, offset from `SampleBase` (0 = none: only retune) |
| +4 | L | loop sample, offset from `SampleBase` (0 = silence after the attack) |
| +8 | L | volume envelope, self-relative (0 = none) |
| +12 | L | pitch envelope, self-relative (0 = none) |
| +16 | W | attack length in words (AUDxLEN) |
| +18 | W | loop length in words |
| +20 | W | attack period multiplier |
| +22 | W | loop period multiplier |
| +24 | B | volume envelope speed (ticks per step) |
| +25 | B | pitch envelope speed |
| +26 | W | instrument volume (0-256) |

* **Period** = `PitchTable[pitch] × multiplier >> 16`.
* **Volume** = `instrument volume × channel volume >> 8` (0-255), written to AUDxVOL as `/4`.
* **Volume envelope**: each byte n sets the volume to `(n+1) × channel vol × instrument vol >> 16`; 0 ends it.
* **Pitch envelope**: signed bytes subtracted from the pitch, in quarter-semitones; `$80` ends it.
* **Starting a note**: interrupts off, channel DMA off, wait until Paula is idle, load the attack, DMA on,
  wait for Paula to latch it, then load the loop part so it follows the attack.

## Tunes (1MB build)

| # | Use in the game | Length |
|---|---|---|
| 0 | start-of-game fanfare (after the intro) | 4.4 s |
| 1 | high-score name entry – new top score | loops, 30.7 s |
| 2 | level music, levels 0-1 | loops, 28.2 s |
| 3 | high-score name entry | loops, 20.5 s |
| 4 | "hurry up" – 0:15 left on the timer | loops, 0.8 s |
| 5 | boss beaten, key appears | 4.2 s |
| 6 | name entered - new top score | 8.3 s |
| 7 | game over (also Esc abort) | 2.5 s |
| 8 | life lost | 4.5 s |
| 9 | final boss (Astaroth) beaten - a tail call (`BRA PlayMusic`) in its dying state | 25.6 s |
| 10 | **not referenced by the game code** | 6.0 s |
| 11 | name entered | 5.8 s |
| 12 | level music, levels 5-6 | loops, 15.4 s |
| 13 | level music, levels 2-4 | loops, 15.4 s |
| 14 | intro cut-scene | 4.4 s |

The level tunes come from `LevelMusic` (`$6C06` in the 512K source: 2, 2, 13, 13, 13, 12, 12).

## Sound effects

Both builds have the same 30 effect sequences, and the game uses the same numbers in both. The 512K game
triggers 1, 4, 5, 6, 10, 12, 17, 20 and 28; the 1MB game also uses 9, 11, 14, 18, 19, 22, 23, 24 and 27.
Known uses: 1 Arthur hit, 4 jump, 5 land, 6 throw, 10 shot deflected (immune enemy), 12 enemy hit / boss destroyed, 11 torch flame (1MB),
17/20 enemy events, 28 key or item collected. The extra 1MB calls: 9 heavy footstep or landing (Unicorn,
Big Man, Astaroth), 11 the torch bursting into flame, 14 extra life, 18 Woody Pig flying, 19 an enemy hit
(Red Arremer, Big Man; also the 1MB replacement for 12 when a shot hurts an enemy), 22 Skeleton hop,
23 fire pillar flare, 24 Unicorn step and dragon attack, 27 a perched crow every 64 frames.

## Findings

* **512K build has no music.** Its file holds only the effects, and the game's PlayMusic calls were
  removed (their set-up code is still there).
* **Sample overruns (data bugs).** Several instruments declare a length longer than their sample, so
  Paula plays on into the next sample in memory: 9 cases in the 1MB file (worst: instrument 11 plays
  6,770 bytes of a 1,950-byte sample) and 10 in the 512K file (instrument 26: 8,880 of 2,972). The two
  builds store their samples in a different order, so the overrun tail sounds different in each.
  With some 512K samples also being shorter versions, this is why 17 of the 30 effects sound
  different between the builds.
* **Stale ownership flag.** `DRV_Owns` is only updated when a voice reads a new event. The per-tick
  envelope code uses whatever the last voice left there, so a music voice can briefly write volume or
  period to a channel an effect is using.
* **Leftovers**: command 3 stores a value nothing reads; `DebugWaitMouse` (flash `COLOR00` until the
  mouse is clicked) is never called; unreachable `END` bytes follow some `JUMP`s; pattern 12 and
  instruments 0 and 7 are unused in the 1MB file; the 512K file keeps 9 dummy music instruments.

## Verification

* Both sources reassemble byte-identical.
* `tools/sndemu.py` runs the **original driver code** in a 68000 emulator (Unicorn) and feeds its Paula
  register writes into a Paula model, so every render in `audio/` comes from the real code.
* The first tune's note changes land exactly on its encoded durations, and its periods step by exact
  semitone ratios. Looping tunes repeat after exactly the length calculated from their data.

## Files

* `gng_music_1mb.s`, `gng_sfx_512k.s`, `samples/*.raw` – sources
* The music for 512K machines (the enhanced game) is in `../../enhanced/sound/`:
  `gng_music_512k.s`, made by `tools/make_music_512k.py` there from the two sources here (the
  512K effects with the 1MB tunes), and checked against both by `tools/check_music_512k.py`.
  The tunes' sampled instruments (samples 5-9) are at 3/4 of their rate (`samples/r3_4/` there), their
  period multipliers divided by 3/4 so every note keeps its pitch; `--rate N/D` makes other rates
  (`--rate 1`: full quality), written elsewhere with `--out` (the game's `build_game.py --music-rate`)
* `audio/tunes/`, `audio/sfx_1mb/`, `audio/sfx_512k/` – MP3 renders (looping tunes: two passes)
* `audio/samples_1mb/`, `audio/samples_512k/` – every sample as an 8-bit WAV at its recorded rate
* `tools/` – `sndparse.py` (data parser), `gen_snd.py` + `snd_anno.py` (source generator), `sndemu.py`
  (emulator and renderer), `songlen.py`, `trace_snd.py`
