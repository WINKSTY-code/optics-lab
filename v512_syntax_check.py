# -*- coding: utf-8 -*-
"""提取 V5.1.2 的 <script> 块并逐个 node --check（语法自检）"""
import re, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v5.1.2.html")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

html = open(SRC, "r", encoding="utf-8").read()
blocks = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, re.S)
print("script 块数：", len(blocks))

fail = 0
for i, b in enumerate(blocks):
    p = os.path.join(BASE, "_v512_chk_%d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode == 0:
        print("  [OK]   _v512_chk_%d.js  (%d chars)" % (i, len(b)))
    else:
        fail += 1
        print("  [FAIL] _v512_chk_%d.js\n%s" % (i, r.stderr.strip()[:600]))
    os.remove(p)

print("语法自检：%s" % ("全部通过" if fail == 0 else "%d 块失败" % fail))
sys.exit(1 if fail else 0)
