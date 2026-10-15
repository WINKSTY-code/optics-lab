# -*- coding: utf-8 -*-
"""拆开 _lens_current.js 内嵌 HTML 的 script 块，找出场景脚本"""
import re, os

P = r"C:\Users\Administrator\Desktop\AI光学参赛\_lens_current.js"
s = open(P, encoding="utf-8").read()

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
print("script 块数:", len(blocks))
for i, b in enumerate(blocks):
    head = b.strip()[:100].replace("\n", " ")
    print(f"[{i}] {len(b)} chars :: {head}")
