# -*- coding: utf-8 -*-
import re
BACK=chr(92); NLF=chr(10)
raw=open('光学交互实验室_AI_v6.4.26.html',encoding='utf-8',errors='replace').read()
lines=raw.split(NLF)
def ln(i): return raw.count(NLF,0,i)+1
print('=== runE2E 定义 ===')
i=raw.find('function runE2E')
print('行号', ln(i))
seg=raw[i-400:i+2600]
for j,seg_l in enumerate(seg.split(NLF)):
    print(f'  {seg_l[:150]}')
