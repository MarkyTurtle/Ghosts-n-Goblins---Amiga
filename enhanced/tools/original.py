"""Drive the ORIGINAL game's display code in the emulator: set up a level as the game does,
redraw at a tile origin and return what the display shows. This is the reference the enhanced
scroller is compared against."""
import struct
from amiga import Amiga, equates, GLOBALS, LEVEL_FILE

EQ = equates()
G_ = {k: v for k, v in EQ.items() if k.startswith('g_')}
FILE_LEVEL0, LEVELMAPTABLE = 0x8000, 0x44BA
REDRAW, CAMERAJUMP, SETBPL, SHOWBACK = 0xBFDE, 0x8046, 0x789A, 0x80DC


class Original(Amiga):
    def __init__(self, level):
        super().__init__()
        self.stub_loadfile()
        self.w16(0xDFF108, 0x92); self.w16(0xDFF10A, 0x92)   # BPL1MOD / BPL2MOD as InitHardware
        self.run(0x5D3A, 0x5DD2)                       # Start: copper lists, screens, restore lists
        self.w32(GLOBALS+G_['g_LevelFileAddr'], LEVEL_FILE)
        self.w16(GLOBALS+G_['g_Level'], level)
        self.call(0xC476, a1=FILE_LEVEL0+10*level)     # LoadFile (stubbed) the level's tiles
        off = struct.unpack('>h', bytes(self.u.mem_read(LEVELMAPTABLE+2*level, 2)))[0]
        self.w32(GLOBALS+G_['g_MapPtr'], LEVELMAPTABLE+off)   # as SetupLevel
        self.level = level

    def show(self, tile_x, tile_y, fine_x=0, fine_y=0):
        """Redraw at tile origin (tile_x, tile_y) and display it with the fine scroll."""
        g = lambda n: GLOBALS+G_[n]
        self.w16(g('g_NewTileX'), tile_x); self.w16(g('g_NewTileY'), tile_y)
        self.call(REDRAW)
        self.w16(g('g_PendFineX'), fine_x); self.w16(g('g_PendFineY'), fine_y)
        self.call(CAMERAJUMP)
        self.call(SETBPL)
        self.call(SHOWBACK)
        return self.render()


if __name__ == '__main__':
    import sys, time
    lv = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    o = Original(lv)
    t = time.time()
    img = o.show(int(sys.argv[2]) if len(sys.argv) > 2 else 0, int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    print(f'{o.blits} blits, {o.blit_words} words, {time.time()-t:.1f}s')
    o.save_png(img, f'orig_l{lv}.png')                 # (in the current folder)
