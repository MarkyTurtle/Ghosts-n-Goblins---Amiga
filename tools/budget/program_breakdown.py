"""Code and data in the 512K main program, by kind. Code = every instruction the control-flow
trace found (tools/trace.json, including routines nothing calls); data is grouped by the name of
the label it sits under.     cd tools && python3 budget/program_breakdown.py"""
import json, re
import sys; sys.path.insert(0, '.'); from anno_db import NAMES
t = json.load(open('trace.json'))
D = open('main.bin', 'rb').read(); B = 0x80; END = B+len(D)
code = bytearray(END)
for a, v in t['insn'].items():
    for i in range(v[0]): code[int(a, 16)+i] = 1
RULES = [('map & tile tables', r'^(CellTiles|TileAttr|BlockTiles|MapBlockIndex|WorldMap|FloorProfile|WallProfile|LevelMapTable|MapZoneTable)'),
         ('spawn & placement tables', r'^(ZoneSpawners|SpawnScripts|ZoneList|Spawn_|Level\dItems|Level\dEnemies|LevelItemLists|LevelEnemyLists)'),
         ('level / score tables', r'^(Level|ScoreValues|EnemyPoints|BonusKinds|WeaponOdds)'),
         ('BOB frame and size tables', r'^(BobFrame|BobFrames|EnemyShotFrames|EffectFrames|BobSet|SmallBob|CacheSizes|ItemImage|ItemBoxSizes|BoxSize|EnemyBoxClass)'),
         ('animation & movement scripts', r'(Anim|Move|Script|Path|Table$|Times|Jump|Swoop|Walk|Dive|Fly|Turn|Climb|Descend|Steps|Speeds)'),
         ('HUD / icon graphics, palette', r'^(Hud|WeaponIcons|GamePalette|Sprite|Font)'),
         ('text', r'^Txt|^DefaultHiNames'),
         ('copper, file table, hunk', r'^(Copper|File|LevelFileIndex|Hunk)'),
         ('box / hit tables', r'(Box|Hitbox|Vulnerab)')]
cats = {}
labs = sorted((a, n) for a, n in NAMES.items() if B <= a < END)
for (a, n), (b, _) in zip(labs, labs[1:]+[(END, None)]):
    c = next((c for c, r in RULES if re.search(r, n)), 'other data')
    cats[c] = cats.get(c, 0) + sum(1 for x in range(a, b) if not code[x])
print(f'{"main program (512K)":32s}{len(D):8,d}')
print(f'{"  code":32s}{sum(code[B:END]):8,d}')
for k, v in sorted(cats.items(), key=lambda x: -x[1]): print(f'  {k:30s}{v:8,d}')
