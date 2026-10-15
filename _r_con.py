# -*- coding: utf-8 -*-
import re, hashlib, json
BS=chr(92); NL=chr(10); Q=chr(34)
SRC='光学交互实验室_AI_v6.4.26.html'
raw=open(SRC,encoding='utf-8',errors='replace').read()
lines=raw.split(NL)
def ln(i): return raw.count(NL,0,i)+1

# 1. 定位 6 个 window.__X__ = "..." 单行
embeds=[]
for i,l in enumerate(lines):
    m=re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*'+Q, l)
    if m:
        embeds.append({'name':m.group(1),'line':i+1,'start':m.end(),'end':l.rfind(Q+';')})
print('=== 内嵌页清单 ===')
for e in embeds:
    print(f"  {e['name']:<18} L{e['line']:<6} 值长 {(e['end']-e['start'])/1024:8.1f}KB")
json.dump(embeds, open('_r_embeds.json','w'), ensure_ascii=False)

# 2. 每个内嵌页里找 <script> ... <\/script> 对，取最长者为 three.js
print()
print('=== 各内嵌页的 script 块（原文层）===')
report={}
for e in embeds:
    body=lines[e['line']-1][e['start']:e['end']]
    blocks=[]
    pos=0
    while True:
        s=body.find('<script', pos)
        if s<0: break
        gt=body.find('>', s)
        if gt<0: break
        close=body.find('<'+BS+'/script>', gt)
        if close<0:
            close2=body.find('</script>', gt)
            print(f"    !! {e['name']} 发现裸 </script>，需人工确认")
            close = close2 if close2>0 else -1
        if close<0: break
        blocks.append({'tag':body[s:gt+1],'s':s,'e':close+len('<'+BS+'/script>'),'content_s':gt+1,'content_e':close})
        pos=gt+1
    blocks.sort(key=lambda b: b['content_e']-b['content_s'], reverse=True)
    print(f"  {e['name']:<18} script块={len(blocks)}")
    for b in blocks[:4]:
        n=b['content_e']-b['content_s']
        print(f"      tag={b['tag']:<20} 内容 {n/1024:8.1f}KB  头60={body[b['content_s']:b['content_s']+60]!r}")
    if blocks:
        top=blocks[0]
        report[e['name']]={'tag':top['tag'],'content_s':top['content_s'],'content_e':top['content_e'],
                           'len':top['content_e']-top['content_s'],
                           'md5':hashlib.md5(body[top['content_s']:top['content_e']].encode('utf-8','ignore')).hexdigest()}
json.dump(report, open('_r_three.json','w'), ensure_ascii=False)
print()
print('=== three.js 主体分组（原文层 md5）===')
from collections import defaultdict
g=defaultdict(list)
for k,v in report.items(): g[v['md5']].append((k,v['len']))
for h,v in g.items():
    print(f"  {h[:10]}  {len(v)} 份  {v[0][1]/1024:.1f}KB/份  合计 {sum(x for _,x in v)/1024:.1f}KB  -> {[n for n,_ in v]}")
