# -*- coding: utf-8 -*-
"""产物 JS 拆块语法自检（脚本收尾标签用浏览器口径）"""
import re, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.5.2.html")
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.5.1.html")

# 浏览器口径：</script 后接 空白 / / / > 即闭合
PAT = re.compile(r"<script[^>]*>(.*?)</script(?=[\s>/])", re.S)

NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
out = os.path.join(BASE, "_chk652")
os.makedirs(out, exist_ok=True)

def blocks(p):
    return PAT.findall(open(p, encoding="utf-8", newline="").read())

for name, p in [("SRC", SRC), ("DST", DST)]:
    bs = blocks(p)
    n = 0
    for i, b in enumerate(bs):
        if len(b.strip()) < 20:
            continue
        fp = os.path.join(out, "%s_%d.js" % (name, i))
        open(fp, "w", encoding="utf-8").write(b)
        r = subprocess.run([NODE, "--check", fp], capture_output=True, text=True)
        assert r.returncode == 0, "[JS FAIL] %s block %d: %s" % (name, i, r.stderr[:400])
        n += 1
    print("%s: %d 个非空 script 块全部通过 node --check" % (name, n))

# 字节级差异审计：只应有 5 处改动
a = open(SRC, encoding="utf-8", newline="").read()
b = open(DST, encoding="utf-8", newline="").read()
import difflib
diff = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
        if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
print("\n行级差异（- 旧 / + 新），共 %d 行:" % len(diff))
for l in diff:
    print("   " + l[:150])
print("\nCRLF: src=%d dst=%d" % (a.count("\r\n"), b.count("\r\n")))
