# -*- coding: utf-8 -*-
import re, hashlib, json
from collections import defaultdict
BS=chr(92); NL=chr(10); Q=chr(34)
raw=open('光学交互实验室_AI_v6.4.26.html',encoding='utf-8',errors='replace').read()
lines=raw.split(NL)
embeds=[]
for i,l in enumerate(lines):
    m=re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*'+Q, l)
    if m: embeds.append({'name':m.group(1),'line':i+1,'start':m.end(),'end':l.rfind(Q+';')})

def blocks_of(body):
    out=[];pos=0
    while True:
        s=body.find('<script',pos)
        if s<0: break
        gt=body.find('>',s)
        if gt<0: break
        cl=body.find('<'+BS+'/script>',gt)
        if cl<0: break
        out.append((body[s:gt+1],gt+1,cl))
        pos=gt+1
    return out

print('=== 逐内嵌页：three.js 块的"逻辑行"分布 ===')
info={}
for e in embeds:
    body=lines[e['line']-1][e['start']:e['end']]
    bs=blocks_of(body)
    bs.sort(key=lambda b: b[2]-b[1], reverse=True)
    tag,cs,ce=bs[0]
    content=body[cs:ce]
    parts=content.split(BS+NL)
    lens=sorted((len(p) for p in parts), reverse=True)
    print(f"{e['name']:<18} 块 {len(content)/1024:7.1f}KB  逻辑行数={len(parts):<5} 前5大 {[f'{x/1024:.1f}K' for x in lens[:5]]}")
    info[e['name']]={'tag':tag,'content':content,'cs':cs,'ce':ce,'parts':len(parts)}

print()
print('=== 归一化后比对（剥掉头部空白与 banner 注释，取最大逻辑块）===')
norm={}
for n,d in info.items():
    parts=d['content'].split(BS+NL)
    big=max(parts,key=len)
    # 再剥掉 big 开头的空白
    core=big.strip()
    h=hashlib.md5(core.encode('utf-8','ignore')).hexdigest()
    norm.setdefault(h,[]).append((n,len(core)))
    print(f"  {n:<18} 最大逻辑块 {len(big)/1024:8.1f}KB  md5={h[:10]}  头50={big[:50]!r}")
print()
g=defaultdict(list)
for n,d in info.items():
    parts=d['content'].split(BS+NL)
    big=max(parts,key=len)
    g[hashlib.md5(big.strip().encode('utf-8','ignore')).hexdigest()].append(n)
print('=== 分组 ===')
for h,v in g.items():
    print(f"  {h[:10]}  {len(v)} 份 -> {v}")
