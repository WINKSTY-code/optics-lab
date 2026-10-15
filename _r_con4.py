# -*- coding: utf-8 -*-
import re
BACK=chr(92); NN=chr(110); QQ=chr(34); NLF=chr(10)
ESC_NL=BACK+NN; ESC_CLOSE='<'+BACK+'/script>'
raw=open('光学交互实验室_AI_v6.4.26.html',encoding='utf-8',errors='replace').read()
lines=raw.split(NLF)
embeds={}
for i,l in enumerate(lines):
    m=re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*'+QQ, l)
    if m: embeds[m.group(1)]=lines[i][m.end():l.rfind(QQ+';')]

def blocks_of(body):
    out=[];pos=0
    while True:
        s=body.find('<script',pos)
        if s<0: break
        gt=body.find('>',s)
        if gt<0: break
        cl=body.find(ESC_CLOSE,gt)
        if cl<0: break
        out.append((s,gt+1,cl)); pos=gt+1
    return out

for name in ['__S3D_REFL__','__S3D_SHADOW__','__ECL_HTML__']:
    body=embeds[name]
    bl=blocks_of(body)
    bl.sort(key=lambda b:b[2]-b[1],reverse=True)
    s,cs,ce=bl[0]
    content=body[cs:ce]
    parts=content.split(ESC_NL)
    print(f'######## {name}  最大 script 块 {len(content)/1024:.1f}KB, {len(parts)} 逻辑行 ########')
    # 按出现顺序，打印长度 >2KB 的段
    idx=0
    for pi,p in enumerate(parts):
        if len(p)>2000:
            print(f'  [逻辑行{pi:>5}] {len(p)/1024:7.1f}KB 头110: {p[:110]!r}')
    print(f'  ...尾部120: {content[-120:]!r}')
    print()
