# -*- coding: utf-8 -*-
"""V6.4.5 产物自检：
   1. 按浏览器口径拆 <script> 块，逐块喂 node --check（大文件「注入成功但语法坏了」是高频事故）
   2. 反解 window.__S3D_SHADOW__，与 src3d/shadow/shadow3d.html 逐字符比对
   3. 版本号四处同步 + 更新日志条目
"""
import json
import os
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.5.html")
SCENE = os.path.join(BASE, "src3d", "shadow", "shadow3d.html")
CHK = os.path.join(BASE, "_chk645")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

s = open(DST, encoding="utf-8").read()
os.makedirs(CHK, exist_ok=True)

# ---- 1. 拆块 + node --check（正则用浏览器口径：</script 后跟 空白 / / / > 都算收尾）
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
print("脚本块数：%d" % len(blocks))
bad = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(CHK, "_chk645_%02d.js" % i)
    open(p, "w", encoding="utf-8", newline="\n").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:400]))
    else:
        print("  OK  block %-2d  %8d chars" % (i, len(b)))
assert bad == 0, "%d 个脚本块语法错误" % bad

# ---- 2. 场景源码反解
m = re.search(r'window\.__S3D_SHADOW__ = (".*?");\n</script>', s, re.S)
assert m, "产物中未找到 __S3D_SHADOW__"
back = json.loads(m.group(1))
scene = open(SCENE, encoding="utf-8").read()
assert back == scene, "产物里的场景源码与磁盘文件不一致"
assert back.count("<script") == 2 and len(re.findall(r"</script(?=[\s>/])", back)) == 2
print("场景源码反解逐字符一致：%d B（three.js + 场景脚本）" % len(back))

# 内嵌改造点必须都在
for t in ['<body class="embed">', "body.embed #btnFull", "body.embed #dock{left:10px;right:178px",
          "function setRunning(on)", "post({ t:'s3d:ready', key:S3D_KEY })", "var S3D_KEY = 'shadow'"]:
    assert t in back, "内嵌改造点缺失：%s" % t
print("内嵌改造点齐全（embed 样式 / 暂停开关 / 消息协议）")

# ---- 3. 版本号与联动
for t, n in [("var BUILD = 'v6.4.5'", 1), ("return 'v6.4.5';", 1),
             (">v6.4.5</div>", 1), ("V6.4.5 · 影子形成新增路灯影子间距3D案例", 1),
             ("shadow: window.__S3D_SHADOW__", 1), ("shadow: { panel:'tab-line'", 1),
             ('data-s3d="shadow"', 3), ('id="line-s3dNote"', 1),
             ('announce(k, on);', 1), ('announce(k, true);', 1), ("function setDisp1(node, hide)", 1)]:
    c = s.count(t)
    assert c == n, "[FAIL] %r 出现 %d 次，应为 %d" % (t, c, n)
    print("  OK  %-52s x%d" % (t[:52], c))
assert "小孔成像新增心形小孔阵3D案例。" in s, "旧日志条目丢失"
assert s.count('<div class="log-item cur">') == 1, "cur 日志条目应只有 1 条"
# 每条切换条 = 切换条 + 3D 框 + JS 里的选择器，各 3 处；五套 3D 场景并存
assert s.count('data-s3d="shadow"') == 3 and s.count('data-s3d="pinhole"') == 3
assert s.count('class="s3d-frame"') == 5, "3D 框应为 5 个，实际 %d" % s.count('class="s3d-frame"')
print("\n全部自检通过")
