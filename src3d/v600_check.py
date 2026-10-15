# -*- coding: utf-8 -*-
"""V6.0.0 产物自检：拆 <script> 块过 node --check + 校验 3 份 3D 场景源码无损。"""
import json, os, re, subprocess, sys
BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "..", "光学交互实验室_AI_v6.0.0.html")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
SRC3D = [("__S3D_REFL__", "3D_光的反射_可折转纸板.html"),
         ("__S3D_LENS__", "3D_凸透镜成像.html"),
         ("__S3D_MIRROR__", "3D_平面镜成像_棋子.html")]
html = open(DST, encoding="utf-8").read()
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
lit = len(re.findall(r"</script(?=[\s>/])", html))
print("script 块 %d 个 / 收尾标签字面量 %d 处 -> %s" % (len(blocks), lit, "一致" if lit == len(blocks) else "★不一致★"))
fail = 0
tmp = os.path.join(BASE, "_chk600"); os.makedirs(tmp, exist_ok=True)
for i, b in enumerate(blocks):
    if len(b.strip()) < 20: continue
    p = os.path.join(tmp, "blk_%02d.js" % i)
    open(p, "w", encoding="utf-8", newline="").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        fail += 1
        print("FAIL block %02d %8d B  %s" % (i, len(b.encode()), r.stderr.strip()[:200]))
    else:
        print("OK   block %02d %8d B" % (i, len(b.encode())))
for var, fn in SRC3D:
    m = re.search(r"window\.%s = (.*?);\n" % var, html, re.S)
    assert m, "找不到 window.%s" % var
    back = json.loads(m.group(1))
    raw = open(os.path.join(BASE, fn), encoding="utf-8").read()
    ok = back == raw
    print("%s 场景源码 round-trip 无损: %s (%d chars)" % ("OK  " if ok else "FAIL", ok, len(raw)))
    if not ok: fail += 1
checks = [
    ("版本角标 v6.0.0", ">v6.0.0</div>" in html),
    ("BUILD v6.0.0", "var BUILD = 'v6.0.0'" in html),
    ("三处 2D/3D 切换条", html.count('class="s3d-bar"') == 3),
    ("三处 3D 框", html.count('class="s3d-frame"') == 3),
    ("三处 iframe", html.count('class="s3d-ifr"') == 3),
    ("挂载层", "window.S3D = { setMode" in html),
    ("更新日志 V6.0.0", '<span class="log-ver">V6.0.0</span>' in html),
    ("i18n s3d.2d", "'s3d.2d':" in html),
    ("2D 视图未动（11 个 tab）", html.count('class="tab-btn') == 11),
]
for n, ok in checks:
    print(("OK   " if ok else "FAIL ") + n)
    if not ok: fail += 1
print("-" * 60); print("结论:", "全部通过" if fail == 0 else "%d 项失败" % fail)
sys.exit(1 if fail else 0)
