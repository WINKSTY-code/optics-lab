# -*- coding: utf-8 -*-
import re, hashlib, difflib
B = chr(92); QQ = chr(34); NLF = chr(10)
BQ = B + QQ; BN = B + 'n'
ESC_CLOSE = '<' + B + '/script>'
SRC = '光学交互实验室_AI_v6.4.26.html'
raw = open(SRC, encoding='utf-8', errors='replace').read()
lines = raw.split(NLF)
emb = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*' + QQ, l)
    if m: emb[m.group(1)] = l[m.end():l.rfind(QQ + ';')]

def unesc(s):
    out = []; k = 0; n = len(s)
    while k < n:
        c = s[k]
        if c != B: out.append(c); k += 1; continue
        k += 1
        if k >= n: break
        e = s[k]
        if e == 'n': out.append(NLF); k += 1
        elif e == 't': out.append(chr(9)); k += 1
        elif e == 'r': out.append(chr(13)); k += 1
        elif e == 'u': out.append(chr(int(s[k+1:k+5], 16))); k += 5
        else: out.append(e); k += 1
    return ''.join(out)

LIB = {}
for name, body in emb.items():
    i_umd = body.find('!function(t,e){' + BQ + 'object')
    sc = body.rfind('<script>', 0, i_umd)
    i_rev = body.find('t.REVISION=e')
    k = body.find('}));', i_rev)
    cl = body.find(ESC_CLOSE, k)
    inner = body[sc + len('<script>'):cl]
    LIB[name] = unesc(inner)

groups = {'A(REFL)': '__S3D_REFL__', 'ECL': '__ECL_HTML__', 'PINHOLE': '__S3D_PINHOLE__', 'SHADOW': '__S3D_SHADOW__'}
base = LIB['__S3D_REFL__']
print(f'基准 REFL 长度={len(base)}  md5={hashlib.md5(base.encode()).hexdigest()[:12]}')
for gname, nm in groups.items():
    if nm == '__S3D_REFL__': continue
    t = LIB[nm]
    # 第一个不同点
    i = 0; m = min(len(base), len(t))
    while i < m and base[i] == t[i]: i += 1
    print(f'\n--- {gname} ({nm})  长度={len(t)}  首个差异@{i} ---')
    print(f'  REFL 段: {base[max(0,i-70):i+90]!r}')
    print(f'  {gname} 段: {t[max(0,i-70):i+90]!r}')
    # 去空白后比对
    nw_base = re.sub(r'\s+', '', base); nw_t = re.sub(r'\s+', '', t)
    print(f'  去空白后 REFL={len(nw_base)}  {gname}={len(nw_t)}  相同={nw_base==nw_t}')
    if nw_base != nw_t:
        j = 0; mm = min(len(nw_base), len(nw_t))
        while j < mm and nw_base[j] == nw_t[j]: j += 1
        print(f'    去空白首差@{j}: REFL={nw_base[max(0,j-60):j+90]!r}')
        print(f'                    {gname}={nw_t[max(0,j-60):j+90]!r}')
        # 差异计数
        d = sum(1 for a, b in zip(nw_base, nw_t) if a != b)
        print(f'    去空白差异字符数={d}  长度差={len(nw_t)-len(nw_base)}')
