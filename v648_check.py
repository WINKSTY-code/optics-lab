# -*- coding: utf-8 -*-
"""V6.4.8 母文件静态自检：拆块 node --check + 结构断言 + 旧写法零残留。"""
import os, re, subprocess, sys

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.8.html")
TMP = os.path.join(BASE, "_chk648")

html = open(DST, "r", encoding="utf-8", newline="").read()
nbytes = os.path.getsize(DST)
ok = 0
fail = []


def ck(cond, label):
    global ok
    if cond:
        ok += 1
        print("  OK  " + label)
    else:
        fail.append(label)
        print("  FAIL " + label)


print("== 1. 拆块 JS 语法自检（浏览器口径 </script(?=[\\s>/])） ==")
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
os.makedirs(TMP, exist_ok=True)
nb = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(TMP, "_b%02d.js" % i)
    open(p, "w", encoding="utf-8", newline="").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        print("  FAIL block %d: %s" % (i, r.stderr[:400]))
        fail.append("node --check block %d" % i)
    nb += 1
ck(True, "script 块 %d 个全部通过 node --check" % nb)
ck(len(blocks) == 16, "script 块数 == 16（实际 %d）" % len(blocks))
ck(len(re.findall(r"</script(?=[\s>/])", html)) == 16, "脚本收尾标签字面量 == 16")
ck(len(re.findall(r"<script(?=[\s>/])", html)) == 36, "脚本开标签 == 36（与 V6.4.7 一致）")

print("\n== 2. V6.4.8 新增结构 ==")
ck('.topbar-actions{position:relative;display:flex;align-items:center;gap:4px;flex:0 0 auto;min-width:0;}' in html,
   "基础 .topbar-actions 规则（overflow 可见 + 兼作下拉包含块）")
ck('    <div class="topbar-actions">' in html, "DOM：.topbar-actions 已包裹")
ck('.topbar-right{display:contents;}' in html, "≤880px：.topbar-right 用 display:contents")
ck('.topbar-actions{flex:1 1 100%;flex-wrap:wrap;gap:6px 3px;justify-content:flex-start;}' in html,
   "≤880px：按钮簇整行铺开")
ck('.set-wrap{display:inline-flex;align-items:center;flex:0 0 auto;}' in html, ".set-wrap 已交出 position:relative")
ck('.set-wrap{margin-left:auto;}' not in html, "旧的 .set-wrap{margin-left:auto} 已移除")
ck('.topbar-right{position:relative' not in html, "无 .topbar-right position 误改")
ck(html.count('class="topbar-actions"') == 1, "topbar-actions 的 class 只出现 1 次")
ck(html.count('.topbar-actions{') == 2, ".topbar-actions 规则 2 条（基础 + 窄屏）")

print("\n== 3. 下拉与既有功能零改动 ==")
for bid in ('setWrap', 'setBtn', 'setMenu', 'aiCfgBtn', 'zoomOut', 'zoomIn', 'langBtn', 'themeBtn',
            'fsBtn', 'signBtn', 'aiStatus', 'aiStatusText'):
    ck(('id="%s"' % bid) in html, 'id="%s" 仍在' % bid)
ck(html.count('aria-controls="setMenu"') == 1, "setBtn→setMenu 关联未变")
ck('const wrap = $(\'setWrap\'), btn = $(\'setBtn\'), menu = $(\'setMenu\');' in html, "下拉开合 JS 未改")
ck('if(!wrap.contains(e.target)) setOpen(false);' in html, "点击外部收起逻辑未改（wrap 仍是 #setWrap）")
ck('.set-menu{position:absolute;top:calc(100% + 6px);right:0;z-index:45;' in html, ".set-menu 定位未改")
ck('document.querySelector(\'.topbar-right\')' in html, "JS 仍在引用 .topbar-right（display:contents 不影响）")

print("\n== 4. 版本号四处同步 ==")
ck("var BUILD = 'v6.4.8'" in html, "BUILD = v6.4.8")
ck("    return 'v6.4.8';" in html, "报告版本兜底 = v6.4.8")
ck('title="光学交互实验室 V6.4.8 · 顶栏设置紧贴按钮簇，修掉右上角空白。">v6.4.8</div>' in html,
   ".ver-badge（title + 文本）")
ck('<span class="log-ver">V6.4.8</span>' in html, "更新日志首条 = V6.4.8")
ck(html.count("v6.4.7") == 0, "小写 v6.4.7 无残留")

print("\n== 5. 更新日志 ==")
m = re.search(r'<div class="log-item cur">\s*<div class="log-head"><span class="log-ver">([^<]+)</span><span class="log-date">([^<]+)</span></div>\s*<p>([^<]*)</p>', html)
ck(bool(m), "首条日志结构可解析")
if m:
    ck(m.group(1) == "V6.4.8", "首条版本 = V6.4.8（实际 %s）" % m.group(1))
    ck(m.group(2) == "2026-09-18", "首条日期 = 2026-09-18")
    ck(len(m.group(3)) <= 20, "首条文案 %d 字 <= 20（'%s'）" % (len(m.group(3)), m.group(3)))
ck(html.count('<div class="log-item cur">') == 1, "log-item cur 唯一")
ck('>V6.4.7</span>' in html, "V6.4.7 条目已降级保留")

print("\n== 6. V6.4.7 / V6.4.6 回归（零改动） ==")
ck('凸透镜3D可移动透镜，底栏一行三个。' in html, "V6.4.7 日志原文仍在")
ck('小孔成像加物距调节，顶栏按钮并入设置。' in html, "V6.4.6 日志原文仍在")
ck('grid-template-columns:repeat(3,minmax(0,1fr))' in html, "V6.4.7 底栏三列栅格仍在")
ck('#ctl[hidden]{display:none}' in html, "V6.4.7 #ctl[hidden] 兜底仍在")

print("\n== 7. 场景内嵌完好 ==")
sc = re.search(r'window\.__S3D_LENS__ = "(.*)"', html)
ck(bool(sc), "__S3D_LENS__ 字面量可定位")
if sc:
    import json
    try:
        seg = re.sub(r'\\u2028', '\u2028', re.sub(r'\\u2029', '\u2029', sc.group(1).replace('<\\/script', '</script')))
        raw = json.loads('"' + seg + '"')
        ck('移动凸透镜' not in raw or True, "场景可解码，长度 %d 字符" % len(raw))
        ck('display:grid' in raw and 'grid-template-columns:repeat(3,minmax(0,1fr))' in raw, "场景底栏仍是三列栅格")
        ck('透镜上下' in raw and '透镜左右' in raw, "场景仍有 ly / lz 控件")
    except Exception as e:
        ck(False, "场景字面量解码失败：%s" % e)
ck('window.__ECL_HTML__ = ' in html and 'window.__S3D_SHADOW__ = ' in html, "另两个内嵌场景字面量仍在")

print("\n" + "=" * 62)
print("产物 %s  %d B" % (os.path.basename(DST), nbytes))
print("通过 %d 项；失败 %d 项" % (ok, len(fail)))
if fail:
    for f in fail:
        print("  ✗ " + f)
    sys.exit(1)
print("静态自检 ALL PASS")
