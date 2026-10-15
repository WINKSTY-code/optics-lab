# -*- coding: utf-8 -*-
import re, hashlib
B = chr(92); QQ = chr(34); NLF = chr(10)
BQ = B + QQ; BN = B + 'n'
ESC_CLOSE = '<' + B + '/script>'
SRC = '光学交互实验室_AI_v6.4.26.html'
raw = open(SRC, encoding='utf-8', errors='replace').read()
lines = raw.split(NLF)
emb = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*' + QQ, l)
    if m: emb[m.group(1)] = (i + 1, l, m.end(), l.rfind(QQ + ';'))

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

print('=== 库体内危险序列检查（未反转义口径，即真实入库文本）===')
for name, (ln, l, st, en) in emb.items():
    body = l[st:en]
    i_umd = body.find('!function(t,e){' + BQ + 'object')
    sc = body.rfind('<script>', 0, i_umd)
    i_rev = body.find('t.REVISION=e')
    k = body.find('}));', i_rev); cl = body.find(ESC_CLOSE, k)
    inner = body[sc + 8:cl]
    html = unesc(inner)
    print(f'{name:<18} 库体 {len(html):>7} 字符  "</script"={html.count("</script")}  "</"={html.count("</")}  "<!--"={html.count("<!--")}  "<script"={html.count("<script")}')

print()
print('=== RAW body 内 <!-- 出现情况（判断可否用 HTML 注释占位）===')
for name, (ln, l, st, en) in emb.items():
    body = l[st:en]
    print(f'{name:<18} "<!--"={body.count("<!--")}  "-->"={body.count("-->")}')
print()
print('=== 新标记/常量名唯一性（RAW 全文）===')
for tok in ['__S3D_THREE_LIB__', '__THREE_LIB__', 'window.__THREE__', '__THREE_SHADOW__', 'THREE_BUILD']:
    print(f'  {tok!r}: {raw.count(tok)} 次')
print()
print('=== 同时列出现有 window.__ 赋值数 ===')
print('  window.__ 赋值 =', len(emb), '个 ->', list(emb.keys()))
