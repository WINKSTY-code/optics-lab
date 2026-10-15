# -*- coding: utf-8 -*-
# 在 RAW 文件文本上定位每个内嵌页的 three.js 库边界（未反转义口径）
import re, hashlib
B = chr(92); QQ = chr(34); NLF = chr(10)
BQ = B + QQ        # \"
BN = B + 'n'       # \n
ESC_CLOSE = '<' + B + '/script>'
SRC = '光学交互实验室_AI_v6.4.26.html'
raw = open(SRC, encoding='utf-8', errors='replace').read()
lines = raw.split(NLF)
emb = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*' + QQ, l)
    if m: emb[m.group(1)] = (i + 1, m.end(), l.rfind(QQ + ';'), l)

LIC = '/**' + BN + ' * @license' + BN + ' * Copyright 2010-2022 Three.js Authors'
LIC_REL = '/**' + BN + ' * @license'   # SHADOW 可能不同
UMD = '!function(t,e){' + BQ + 'object' + BQ + '==typeof exports'
print('=== RAW 口径：库起止 ===')
recs = {}
for name, (ln, st, en, l) in emb.items():
    body = l[st:en]
    i_lic = body.find(LIC)
    if i_lic < 0: i_lic = body.find(LIC_REL)
    i_umd = body.find(UMD)
    i_rev = body.find('t.REVISION=e')
    # 库前的 <script> 开标签：从 UMD 往前找最近的 '<script>'
    sc = body.rfind('<script>', 0, i_umd if i_umd > 0 else i_lic)
    # 库尾：从 t.REVISION 往后找 '}));' 再找最近的 <\/script>
    k = body.find('}));', i_rev)
    cl = body.find(ESC_CLOSE, k)
    lib_raw = body[sc:cl]
    md5 = hashlib.md5(lib_raw.encode('utf-8', 'ignore')).hexdigest()[:12]
    recs[name] = (sc, cl, lib_raw, md5, i_lic, i_umd, i_rev)
    print(f'{name:<18} 行{ln}  body={len(body)}  库[{sc}..{cl}]={len(lib_raw)}B  md5={md5}')
    print(f'     lic@{i_lic} umd@{i_umd} rev@{i_rev}  库前12={body[max(0,sc-12):sc]!r}  库后12={body[cl:cl+12]!r}')
print()
from collections import defaultdict
g = defaultdict(list)
for n, (sc, cl, lib, md5, *_ ) in recs.items(): g[md5].append(n)
for md5, v in g.items(): print(f'  {md5}  {len(v)}份 -> {v}')
# 库体（去掉 <script> 与 <\/script> 外壳）比对
print()
g2 = defaultdict(list)
for n, (sc, cl, lib, md5, *_ ) in recs.items():
    inner = lib[len('<script>'):-len(ESC_CLOSE)]
    g2[hashlib.md5(inner.encode('utf-8','ignore')).hexdigest()[:12]].append(n)
for md5, v in g2.items(): print(f'  内体 {md5}  {len(v)}份 -> {v}')
