"""Derive gen1m.py (1MB source generator) from the 512K generator ../gen.py, so that
improvements to the generator carry over. Run before gen1m.py."""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'gen.py')
s = open(src).read()
rep = [
("A=importlib.import_module('anno_db') if os.path.exists('anno_db.py') else None", "import anno_db1m as A"),
("""try:
    import anno_auto; AUTO=anno_auto.AUTO_COMMENTS
    for _k,_v in getattr(anno_auto,'AUTO_NAMES',{}).items():
        NAMES.setdefault(_k,_v)
except Exception: AUTO={}""", """AUTO=A.AUTO_COMMENTS
for _k,_v in A.AUTO_NAMES.items(): NAMES.setdefault(_k,_v)
NAMES.setdefault(0,'HunkHeader')
_df=json.load(open('diff.json'))
DIFF={int(k,16):v for k,v in _df['notes'].items()}; ONLY1M=set(_df['only1m']); SYMOK=set(_df['symok'])"""),
("BASE=0x80\nD=open('main.bin','rb').read()", "BASE=0\nD=open(MAIN1M,'rb').read()"),
("open('trace.json')", "open('trace1m.json')"),
("open('seeds.json')", "open('seeds1m.json')"),
("open('prelude.s')", "open('prelude1m.s')"),
("open('gng_main.s','w')", "open('gng_main_1mb.s','w')"),
("""        if v in MEM and sz=='.l': return f'({MEM[v]}).l'
        if v in MEM and sz=='.w': return f'({MEM[v]}).w'
        if sz=='.l':
            s=symaddr(v)
            if s: return f'({s}).l'""", """        if sz=='.l' and CUR[0] in SYMOK and v>=0x20:
            s=symaddr(v)
            if s: return f'({s}).l'
        if v in MEM and sz=='.l': return f'({MEM[v]}).l'
        if v in MEM and sz=='.w': return f'({MEM[v]}).w'"""),
("def convert(a,m,op,state):", "CUR=[0]\ndef convert(a,m,op,state):\n    CUR[0]=a"),
("""        c=CMT.get(a) or AUTO.get(a)""", """        c=CMT.get(a) or (AUTO.get(a) if a not in DROP else None)
        if a in DROP and a not in A.MANUAL_C and a in CMT and a not in ONLY1M: c=None
        if a in ONLY1M: c='[1MB] '+(c or '')
        if a in DIFF: c=(c+'  ' if c else '')+'<< '+DIFF[a]+' >>'"""),
("bounds=sorted(", "_st=sorted(ins); DROP={y for x,y in zip(_st,_st[1:]) if x in ONLY1M}\nbounds=sorted("),
("    for mm in re.finditer(r'(?<![#\\w])\\$([0-9a-f]+)\\.l',op): addref(int(mm.group(1),16),'dat')",
 "    for mm in re.finditer(r'(?<![#\\w])\\$([0-9a-f]+)\\.l',op):\n        if a in SYMOK: addref(int(mm.group(1),16),'dat')"),
]
for a, b in rep:
    if a not in s: sys.exit('make_gen1m: pattern not found:\n' + a)
    s = s.replace(a, b, 1)
s = s.replace("import json,re,sys,os", "import json,re,sys,os\nMAIN1M=os.environ.get('MAIN1M','../../bin/main_1mb.bin')", 1)
open(os.path.join(here, 'gen1m.py'), 'w').write(s)
print('gen1m.py written')
