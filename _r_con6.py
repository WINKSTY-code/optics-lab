# -*- coding: utf-8 -*-
import re, hashlib
BACK = chr(92); QQ = chr(34); NLF = chr(10)
SRC = '光学交互实验室_AI_v6.4.26.html'
raw = open(SRC, encoding='utf-8', errors='replace').read()
lines = raw.split(NLF)
embeds = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*' + QQ, l)
    if m: embeds[m.group(1)] = lines[i][m.end():l.rfind(QQ + ';')]

def unesc(s):
    out = []; k = 0; n = len(s)
    while k < n:
        c = s[k]
        if c != BACK: out.append(c); k += 1; continue
        k += 1
        if k >= n: break
        e = s[k]
        if e == 'n': out.append(NLF); k += 1
        elif e == 't': out.append(chr(9)); k += 1
        elif e == 'r': out.append(chr(13)); k += 1
        elif e == 'u': out.append(chr(int(s[k+1:k+5], 16))); k += 5
        else: out.append(e); k += 1
    return ''.join(out)

CLOSE = '<' + BACK + '/script>'
def blocks_of_literal(body):
    out = []; pos = 0
    while True:
        s = body.find('<script', pos)
        if s < 0: break
        gt = body.find('>', s)
        if gt < 0: break
        cl = body.find(CLOSE, gt)
        if cl < 0: break
        out.append((s, gt + 1, cl)); pos = gt + 1
    return out

UMD = '!function(t,e){' + QQ + 'object' + BACK + QQ + '==typeof exports'
for name in ['__S3D_REFL__', '__S3D_SHADOW__', '__ECL_HTML__', '__S3D_LENS__', '__S3D_MIRROR__', '__S3D_PINHOLE__']:
    body = embeds[name]
    bl = blocks_of_literal(body)
    s, cs, ce = max(bl, key=lambda b: b[2] - b[1])
    html = unesc(body[cs:ce])
    iu = html.find(UMD)
    ir = html.find('t.REVISION=e')
    print(f'\n#### {name}  block0 {len(html)/1024:.1f}KB md5={hashlib.md5(html.encode("utf-8","ignore")).hexdigest()[:10]} UMD@{iu} REVISION@{ir}')
    print(f'   头180: {html[:180]!r}')
    print(f'   UMD后180: {html[iu:iu+150]!r}')
    print(f'   REVISION后240: {html[ir:ir+240]!r}')
    print(f'   尾200: {html[-200:]!r}')
    if iu >= 0 and ir >= 0:
        core = html[iu:html.find('}))' , ir)] if False else None
        # three.js 结束：UMD 结尾通常是 '}));'  找回退点
        tail = html[ir:]
        k = tail.find('}));')
        endpos = ir + (k + 4 if k >= 0 else 0)
        print(f'   >>> 前导(UMD前)={iu}B  库体={ (endpos-iu)/1024:.1f}KB  后随={(len(html)-endpos)/1024:.1f}KB')
        print(f'   后随头160: {html[endpos:endpos+160]!r}')
