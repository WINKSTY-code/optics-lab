# -*- coding: utf-8 -*-
"""V5.2.0 产物自检：拆 <script> 块过 node --check + 校验内嵌演示源码无损。"""
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v5.2.0.html")
DEMO = r"C:\Users\Administrator\Desktop\日食与月食 3D演示.html"
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

html = open(DST, encoding="utf-8").read()
demo = open(DEMO, encoding="utf-8").read()

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
print("script 块数量:", len(blocks), "（用浏览器口径：</script + 空白 / / / > 均算闭合）")
# 交叉校验：整个 HTML 里该字面量出现次数应等于块数
lit = len(re.findall(r"</script(?=[\s>/])", html))
print("脚本收尾标签字面量:", lit, "->", "一致" if lit == len(blocks) else "★不一致，有未闭合/提前闭合★")

tmp = os.path.join(BASE, "_chk520")
os.makedirs(tmp, exist_ok=True)
fail = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(tmp, "blk_%02d.js" % i)
    open(p, "w", encoding="utf-8", newline="").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    tag = "OK  " if r.returncode == 0 else "FAIL"
    if r.returncode != 0:
        fail += 1
    print("%s block %02d  %8d B  %s" % (tag, i, len(b.encode()), r.stderr.strip()[:160]))

# --- 内嵌演示源码无损校验 ---
m = re.search(r"window\.__ECL_HTML__ = (.*?);\n", html, re.S)
assert m, "找不到 window.__ECL_HTML__ 赋值"
lit = m.group(1)
back = json.loads(lit)
same = (back == demo)
print("内嵌演示源码 round-trip 无损:", same, "| %d chars vs %d" % (len(back), len(demo)))
if not same:
    fail += 1

# --- 关键结构存在性 ---
checks = [
    ('版本角标 v5.2.0', '>v5.2.0</div>' in html),
    ("BUILD v5.2.0", "var BUILD = 'v5.2.0'" in html),
    ("模式按钮 3 个", html.count('data-g="') >= 2 and html.count('data-m="eclipse"') == 1),
    ("内嵌 iframe", 'id="line-eclIfr"' in html),
    ("全屏按钮", 'id="line-eclFs"' in html),
    ("退出全屏按钮", 'id="line-eclExit"' in html),
    ("数据面板提示", 'id="line-eclNote"' in html),
    ("ECL 接口", "window.ECL = {" in html),
    ("更新日志 V5.2.0", '<span class="log-ver">V5.2.0</span>' in html),
    ("i18n v.line.eclipse", "'v.line.eclipse': {" in html),
]
for name, ok in checks:
    print(("OK   " if ok else "FAIL ") + name)
    if not ok:
        fail += 1

print("-" * 60)
print("结论:", "全部通过" if fail == 0 else ("%d 项失败" % fail))
sys.exit(1 if fail else 0)
