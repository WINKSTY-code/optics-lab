# -*- coding: utf-8 -*-
# 反转义取出内嵌页真实 HTML，枚举其 <script> 块，定位 three.js 本体
import re, hashlib
BACK = chr(92); QQ = chr(34); NLF = chr(10)
SRC = '光学交互实验室_AI_v6.4.26.html'
raw = open(SRC, encoding='utf-8', errors='replace').read()
lines = raw.split(NLF)

# 1) 抓 window.__X__ = "....." 的字面量内容（含 JS 转义）
embeds = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*' + QQ, l)
    if m:
        embeds[m.group(1)] = (i + 1, lines[i][m.end():l.rfind(QQ + ';')])

def unesc(s):
    out = []; k = 0; n = len(s)
    while k < n:
        c = s[k]
        if c != BACK:
            out.append(c); k += 1; continue
        k += 1
        if k >= n: break
        e = s[k]
        if e == 'n': out.append(NLF); k += 1
        elif e == 't': out.append(chr(9)); k += 1
        elif e == 'r': out.append(chr(13)); k += 1
        elif e == 'u':
            out.append(chr(int(s[k+1:k+5], 16))); k += 5
        else:
            out.append(e); k += 1
    return ''.join(out)

CLOSE = '<' + BACK + '/script>'  # 未反转义口径
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

print('=== 各内嵌页 <script> 块清单（反转义后真实 HTML 口径）===')
for name in ['__S3D_REFL__', '__S3D_SHADOW__', '__ECL_HTML__']:
    ln, body = embeds[name]
    bl = blocks_of_literal(body)
    print(f'\n#### {name}  行{ln}  <script>块数={len(bl)} ####')
    recs = []
    for i, (s, cs, ce) in enumerate(bl):
        html = unesc(body[cs:ce])
        attr = unesc(body[s:cs])
        md5 = hashlib.md5(html.encode('utf-8', 'ignore')).hexdigest()[:10]
        recs.append((i, len(html), md5, attr, html))
        print(f'  [{i}] {len(html)/1024:8.1f}KB md5={md5} attr={attr[:70]!r}')
    # 找到 three.js 主库：含 THREE.REVISION 或 UMD 头
    for i, n, md5, attr, html in recs:
        for probe in ['REVISION', 'Object.defineProperty(t,"__esModule"', 'globalThis']:
            if probe in html:
                j = html.find(probe)
                print(f'     [i={i}] 命中 {probe!r} @{j}  上下文={html[max(0,j-60):j+80]!r}')
                break
