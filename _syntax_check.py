# -*- coding: utf-8 -*-
"""通用：提取指定 HTML 的 <script> 块并逐个 node --check
用法：python _syntax_check.py <html 文件名>
"""
import re, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
SRC = os.path.join(BASE, sys.argv[1] if len(sys.argv) > 1 else "光学交互实验室_AI_v5.1.3.html")

html = open(SRC, "r", encoding="utf-8").read()
blocks = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, re.S)
print("%s → script 块数：%d" % (os.path.basename(SRC), len(blocks)))

fail = 0
for i, b in enumerate(blocks):
    p = os.path.join(BASE, "_chk_%d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode == 0:
        print("  [OK]   block %d  (%d chars)" % (i, len(b)))
    else:
        fail += 1
        print("  [FAIL] block %d\n%s" % (i, r.stderr.strip()[:600]))
    os.remove(p)

print("语法自检：%s" % ("全部通过" if fail == 0 else "%d 块失败" % fail))
sys.exit(1 if fail else 0)
