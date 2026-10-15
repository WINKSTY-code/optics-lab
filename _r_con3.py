# -*- coding: utf-8 -*-
import re, hashlib
from collections import defaultdict
BACK=chr(92); NN=chr(110); QQ=chr(34); NLF=chr(10)
ESC_NL=BACK+NN                      # 文件里的两字符 \n
raw=open('光学交互实验室_AI_v6.4.26.html',encoding='utf-8',errors='replace').read()
lines=raw.split(NLF)
embeds=[]
for i,l in enumerate(lines):
    m=re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*'+QQ, l)
    if m: embeds.append({'name':m.group(1),'line':i+1,'start':m.end(),'end':l.rfind(QQ+';')})

ESC_CLOSE='<'+BACK+'/script>'
def blocks_of(body):
    out=[];pos=0
    while True:
        s=body.find('<script',pos)
        if s<0: break
        gt=body.find('>',s)
        if gt<0: break
        cl=body.find(ESC_CLOSE,gt)
        if cl<0: break
        out.append((gt+1,cl)); pos=gt+1
    return out

print('=== 每个内嵌页的 script 块（逻辑行口径）===')
keep={}
for e in embeds:
    body=lines[e['line']-1][e['start']:e['end']]
    bl=blocks_of(body)
    bl.sort(key=lambda b:b[1]-b[0],reverse=True)
    top=bl[0]
    content=body[top[0]:top[1]]
    parts=content.split(ESC_NL)
    L=sorted((len(p) for p in parts),reverse=True)
    print(f"{e['name']:<18} 总块 {len(content)/1024:7.1f}KB  逻辑行 {len(parts):<5} 前6大 {[f'{x/1024:.1f}K' for x in L[:6]]}")
    keep[e['name']]={'content':content,'lens':L,'nlines':len(parts)}

print()
print('=== 各家最大逻辑行（=压缩库本体）比对 ===')
g=defaultdict(list); sizes={}
for n,d in keep.items():
    parts=d['content'].split(ESC_NL)
    mx=max(parts,key=len)
    core=mx.strip()
    h=hashlib.md5(core.encode('utf-8','ignore')).hexdigest()
    g[h].append(n); sizes[n]=(len(mx),len(d['content']))
    print(f"  {n:<18} 最大逻辑行 {len(mx)/1024:8.1f}KB  md5={h[:10]}  头46={mx[:46]!r}")
print()
for h,v in g.items():
    print(f"  {h[:10]}  {len(v)} 份 -> {v}   单份 {sizes[v[0]][0]/1024:.1f}KB  合计 {sum(sizes[n][0] for n in v)/1024:.1f}KB")

total_dup=sum(sizes[n][0] for n in sizes)
uniq=sum(sizes[v[0]][0] for v in g.values())
print()
print(f'  压缩库字符总量 {total_dup/1024:.1f}KB；去重后 {uniq/1024:.1f}KB；可省 {(total_dup-uniq)/1024:.1f}KB')
