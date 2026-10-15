# -*- coding: utf-8 -*-
"""V6.4.7 产物自检（在 V6.4.6 全部断言上叠加 V6.4.7 的新增项）。

  1. 按浏览器口径拆 <script> 块，逐块 node --check（内联的 3D 场景里有 <\\/script，
     非贪婪 + 前瞻的拆块正则不会被它骗到）
  2. V6.4.6 回归断言：设置下拉 / 小孔物距 / 分组保有量
  3. V6.4.7 断言：3D 场景字面量可解码且含 ly/lz 与三列栅格；版本号四处同步；日志 ≤20 字
"""
import io
import json
import os
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.7.html")
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.6.html")
CHK = os.path.join(BASE, "_chk647")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

s = io.open(DST, encoding="utf-8").read()
os.makedirs(CHK, exist_ok=True)

# ---- 1. 拆块 + node --check
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
print("脚本块数：%d" % len(blocks))
bad = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(CHK, "_chk647_%02d.js" % i)
    io.open(p, "w", encoding="utf-8", newline="\n").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:500]))
    else:
        print("  OK  block %-2d  %8d chars" % (i, len(b)))
assert bad == 0, "%d 个脚本块语法错误" % bad

# ---- 2. 结构断言（V6.4.6 回归 + V6.4.7 新增）
CHECKS = [
    # --- V6.4.6 回归：设置下拉 ---
    ('<div class="set-wrap" id="setWrap">', 1, "设置下拉容器"),
    ('<div class="set-menu" id="setMenu" role="menu" hidden>', 1, "下拉菜单本体（默认收起）"),
    ('id="setBtn" class="theme-btn" data-i18n="btn.settings"', 1, "设置按钮"),
    ("'btn.settings':", 1, "i18n 词条"),
    (".set-menu[hidden]{display:none !important;}", 1, "收起态样式"),
    ('<button id="aiCfgBtn" class="set-item"', 1, "AI 设置按钮保留原 id"),
    ('<button id="zoomOut" class="set-item"', 1, "缩小字号按钮保留原 id"),
    ('<button id="zoomIn" class="set-item"', 1, "放大字号按钮保留原 id"),
    ('<button id="langBtn" class="set-item"', 1, "语言按钮保留原 id"),
    ('<button id="themeBtn" class="set-item"', 1, "背景色按钮保留原 id"),
    ('  </div>\n    <!-- V6.4.6 · 「设置」下拉', 1, "下拉紧跟在 topbar-right 之后"),
    ("$('fsBtn') || $('aiCfgBtn')", 2, "两处注入锚点改到 #fsBtn"),
    ('.set-menu{position:absolute;top:calc(100% + 6px);right:0;', 1, "菜单统一 right:0 定位"),
    ('.set-wrap{margin-left:auto;}', 1, "窄屏把设置推到行尾"),
    # --- V6.4.6 回归：小孔成像物距 ---
    ('<span class="slider-g" data-g="shadow pinhole">', 1, "物距组两模式共用"),
    ('<button id="line-uPlay" class="play-btn" data-i18n="btn.scanU">', 1, "物距扫描按钮仍在"),
    ("var gs = (g.dataset.g || '').split(/\\s+/);", 1, "data-g 空格分隔匹配"),
    ('data-g="shadow pinhole">', 1, "共用组 1 个"),
    ('data-g="shadow">', 1, "影子专属组 1 个"),
    ('data-g="pinhole"', 2, "小孔专属组 2 个"),
    ('<button id="aiCfgBtn" class="theme-btn"', 0, "旧顶栏 AI 设置按钮已移除"),
    ('html[data-mode="mobile"] .set-menu', 0, "窄屏改边规则已移除"),
    # --- V6.4.7 版本号四处 ---
    ("var BUILD = 'v6.4.7'", 1, "BUILD"),
    ("    return 'v6.4.7';", 1, "报告版本兜底"),
    ('title="光学交互实验室 V6.4.7 · ', 1, "角标 title"),
    (">v6.4.7</div>", 1, "角标正文"),
    ('<span class="log-ver">V6.4.7</span>', 1, "更新日志条目"),
    ('<div class="log-item cur">\n        <div class="log-head"><span class="log-ver">V6.4.7</span>', 1, "新条目为 cur"),
    ('<span class="log-ver">V6.4.6</span>', 1, "上一版条目降级保留"),
    ("var BUILD = 'v6.4.6'", 0, "旧 BUILD 已替换"),
]
for t, n, name in CHECKS:
    c = s.count(t)
    assert c == n, "[FAIL] %s：%r 出现 %d 次，应为 %d" % (name, t, c, n)
print("结构断言 %d 项全部命中" % len(CHECKS))

# ---- 3. 内联的 3D 凸透镜场景：解码后核对改动
KEY = 'window.__S3D_LENS__ = "'
lines = s.split("\n")
hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, "场景字面量行定位失败：%s" % hit
lit = lines[hit[0]][len("window.__S3D_LENS__ = "):-1]
scene = json.loads(lit)
print("内联场景 %d 字符 / %d 行" % (len(scene), scene.count("\n") + 1))

SCENE_CHECKS = [
    ("name: 'ly', label: '透镜上下'", 1, "透镜上下滑杆"),
    ("name: 'lz', label: '透镜左右'", 1, "透镜左右滑杆"),
    ("name === 'ly') ly = S.px(v, -4, 4)", 1, "apply 处理 ly"),
    ("name === 'lz') lz = S.px(v, -4, 4)", 1, "apply 处理 lz"),
    ("lens.position.set(0, AY + sLy, sLz);", 1, "透镜随滑块平移"),
    ("axG.position.set(0, AY + sLy, sLz);", 1, "主光轴随透镜平移"),
    ("sLy - m * (yTip - sLy)", 1, "像点横向坐标含光轴偏移"),
    ("sLy - m * (yBase - sLy)", 1, "像底端横向坐标含光轴偏移"),
    ("var dy = yy - sLy, dz = zz - sLz;", 1, "口径判定以透镜中心为圆心"),
    ("#ctlBody{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))", 1, "底栏三列栅格"),
    ("#ctlBody > .tog,#ctlBody > .play{justify-self:center}", 1, "按钮居中"),
    ("@media (max-width:900px){", 1, "窄屏退两列"),
    ("#ctl input[type=range]{order:3;flex:1 1 100%;width:100%}", 1, "手机单元格两行"),
    ("#ctl[hidden]{display:none}", 1, "hidden 兜底（grid 会盖掉 [hidden]）"),
    ("{ type: 'play', name: 'play', label: '▶ 物距扫描', fn: togglePlay }", 1, "扫描按钮仍在最后"),
]
sb = 0
for t, n, name in SCENE_CHECKS:
    c = scene.count(t)
    ok = (c == n)
    print("  %s 场景·%-16s (%d)" % ("OK  " if ok else "FAIL", name, c))
    if not ok:
        sb += 1
assert sb == 0, "场景断言 %d 项未命中" % sb

# 底栏控件应为 9 个（3×3）
nfoot = len(re.findall(r"\{ type: '(?:range|toggle|play)'", scene.split("footer: [")[1].split("],")[0]))
assert nfoot == 9, "底栏控件 %d 个，应为 9" % nfoot
print("底栏控件 %d 个（3×3）" % nfoot)

# 场景里不能再有旧的写法（透镜标签必须走 lb 引用才能跟着平移；口径判定必须以镜心为圆心）
assert scene.count("lb.lens = S.label('凸透镜'") == 1, "透镜标签未改为可移动引用"
for gone in ("\n    S.label('凸透镜'",
             "var inLens = function (yy, zz) { return yy * yy + zz * zz",
             "coneG.add(S.beam(tip, new V(0, 0, 0), 0xff7043, 0.006));"):
    assert scene.count(gone) == 0, "旧写法残留：%r" % gone[:44]
print("旧写法残留检查通过")

# ---- 4. 更新日志字数
m = re.search(r'<span class="log-ver">V6\.4\.7</span>.*?<p>(.*?)</p>', s, re.S)
assert m, "未找到 V6.4.7 日志正文"
txt = m.group(1)
assert len(txt) <= 20, "更新日志 %d 字，超过 20" % len(txt)
print("更新日志：%s（%d 字）" % (txt, len(txt)))

# ---- 5. 脚本收尾标签计数不变量
src = io.open(SRC, encoding="utf-8").read()
a = len(re.findall(r"</script(?=[\s>/])", s))
b = len(re.findall(r"</script(?=[\s>/])", src))
assert a == b, "脚本收尾标签计数变化：%d vs %d" % (a, b)
print("脚本收尾标签计数与源一致：%d" % a)

print("\n全部静态自检通过。")
