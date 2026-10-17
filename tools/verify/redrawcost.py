"""Rough cost of one RedrawScreen: run it in the emulator and count instructions."""
import sys
from emu import Game
from unicorn import UC_HOOK_CODE
G = Game(sys.argv[1] if len(sys.argv) > 1 else None)
G.w32(G.g(0x92), 0x44D6); G.w32(G.g(0x116), 0x60000)        # map, level file
G.w32(G.g(0x42), 0x40000); G.w32(G.g(0x46), 0x50000)       # spare screens
G.w16(G.g(0x82), 5); G.w16(G.g(0x84), 0); G.w16(G.g(0x9A), 0)
counts = {}
def hook(uc, a, size, u):
    counts[a] = counts.get(a, 0) + 1
G.u.hook_add(UC_HOOK_CODE, hook)
G.call(0xBFDE, count=5_000_000)
total = sum(counts.values())
movem = sum(v for a, v in counts.items() if 0xC0DC <= a < 0xC140)
blits = counts.get(0xC098, 0)
print(f'instructions: {total} ({movem} in the 46 KB buffer copy), blits: {blits}')
