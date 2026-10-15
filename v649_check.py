# -*- coding: utf-8 -*-
"""V6.4.9 母文件静态自检：拆块 node --check + 结构断言 + 旧写法零残留 + 全量回归。"""
import os, re, subprocess, sys, json

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.9.html")
TMP = os.path.join(BASE, "_chk649")

html = open(DST, "r", encoding="utf-8", newline="").read()
nbytes = os.path.getsize(DST)
ok = 0
fail = []


def ck(cond, label):
    global ok
    if cond:
        ok += 1
        print("  OK   " + label)
    else:
        fail.append(label)
        print("  FAIL " + label)


print("== 1. 拆块 JS 语法自检（浏览器口径） ==")
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
        print("  FAIL block %d: %s" % (i, r.stderr[:500]))
        fail.append("node --check block %d" % i)
    nb += 1
ck(True, "script 块 %d 个全部通过 node --check" % nb)
ck(len(blocks) == 16, "script 块数 == 16（实际 %d）" % len(blocks))
ck(len(re.findall(r"</script(?=[\s>/])", html)) == 16, "脚本收尾标签字面量 == 16")
ck(len(re.findall(r"<script(?=[\s>/])", html)) == 36, "脚本开标签 == 36（与 V6.4.8 一致）")

print("\n== 2. ① 直线传播：调节栏已移到画布下方（.left 内） ==")
tl = html.index('id="tab-line"')
pos_ctrl = html.index('data-i18n="line.mode"', tl)
pos_right = html.index('<div class="right">', tl)
ck(pos_ctrl < pos_right, "调节栏出现在 .right 之前（即 .left / 画布那侧）")
ck('\n        <div class="ctrl">\n          <span class="clabel" data-i18n="line.mode">' in html,
   "调节栏已按 .left 子级缩进（+4 空格）")
ck('id="line-mode"' in html and 'id="line-reset"' in html, "模式段与重置按钮仍在")
for i in ("line-uSlider", "line-objSlider", "line-vSlider", "line-holeSlider",
          "line-uPlay", "line-objPlay", "line-vPlay", "line-holePlay"):
    ck(('id="%s"' % i) in html, 'id="%s" 仍在' % i)
ck(html.count('data-g="shadow pinhole"') == 1 and html.count('data-g="pinhole"') == 2,
   "data-g 分组未变（shadow pinhole ×1、pinhole ×2）")

print("\n== 3. ② 物体颜色：结构 bug 已修 + 新增物体本色 ==")
ck('</label>\n    </div>\n    <!-- V6.4.9' in html, "#disp-rgb-ctrl 已正确闭合（不再套住 #disp-obj-ctrl）")
ck('id="disp-obj-color"' in html, "新增 #disp-obj-color（物体本色）")
ck(html.count('id="disp-obj-color"') == 1, "#disp-obj-color 唯一")
ck(html.count('data-oc="') == 5, "5 个本色按钮（实际 %d）" % html.count('data-oc="'))
ck(html.count('data-l="') == 4, "4 个照射光按钮（实际 %d）" % html.count('data-l="'))
ck('id="disp-light"' in html, "#disp-light 仍在")
ck('id="disp-obj-ctrl"' in html and 'id="disp-rgb-ctrl"' in html, "两个控件组 id 都在")

print("\n== 4. i18n 词条 ==")
for k in ("disp.objct", "disp.oc.red", "disp.oc.green", "disp.oc.blue", "disp.oc.yellow",
          "disp.oc.white", "disp.pc.black", "disp.pc.red", "disp.pc.green", "disp.pc.blue",
          "disp.pc.yellow", "disp.pc.white", "disp.why.white", "disp.why.mono", "disp.why.black"):
    m = re.search(r"'%s':\s*\{" % re.escape(k), html)
    ck(bool(m), "词条 %s 存在" % k)
ck("'disp.light':     {zh:'照射光：', zht:'照射光：', en:'Light:'}" in html, "disp.light 已改为「照射光：」")
ck(html.count("disp.note.") == 0, "旧 disp.note.* 已清零")
# 每条的 zh/zht/en 三语都要齐（抽 3 条验证）
for k in ("disp.objct", "disp.pc.black", "disp.why.mono"):
    m = re.search(r"'%s':\s*\{zh:'(.*?)',\s*zht:'(.*?)',\s*en:'(.*?)'\}" % re.escape(k), html, re.S)
    ck(bool(m), "%s 三语齐全" % k)
# 所有 data-i18n 键都能在词典里找到（防裸键）
keys_used = set(re.findall(r'data-i18n="([^"]+)"', html))
dict_keys = set(re.findall(r"\n'([a-z][\w.]+)':\s*\{zh:", html))
missing = sorted(k for k in keys_used if k not in dict_keys)
ck(not missing, "无裸 i18n 键（缺失 %d 个%s）" % (len(missing), ("：" + ",".join(missing[:6])) if missing else ""))
ck(('disp.objct' in keys_used) and ('disp.oc.red' in keys_used), "新键已被 DOM 引用")

print("\n== 5. 版本号四处同步 + 更新日志 ==")
ck("var BUILD = 'v6.4.9'" in html, "BUILD = v6.4.9")
ck("    return 'v6.4.9';" in html, "报告版本兜底 = v6.4.9")
ck('title="光学交互实验室 V6.4.9 · 直线传播调节栏移到画布下，物体颜色可调。">v6.4.9</div>' in html,
   ".ver-badge（title + 文本）")
m = re.search(r'<div class="log-item cur">\s*<div class="log-head"><span class="log-ver">([^<]+)</span>'
              r'<span class="log-date">([^<]+)</span></div>\s*<p>([^<]*)</p>', html)
ck(bool(m), "首条日志结构可解析")
if m:
    ck(m.group(1) == "V6.4.9", "首条版本 = V6.4.9（实际 %s）" % m.group(1))
    ck(m.group(2) == "2026-09-18", "首条日期 = 2026-09-18")
    ck(len(m.group(3)) <= 20, "首条文案 %d 字 <= 20（'%s'）" % (len(m.group(3)), m.group(3)))
ck(html.count('<div class="log-item cur">') == 1, "log-item cur 唯一")
ck('>V6.4.8</span>' in html and '>V6.4.7</span>' in html, "V6.4.8 / V6.4.7 条目已降级保留")
ck(html.count("v6.4.8") == 0, "小写 v6.4.8 无残留")

print("\n== 6. 回归（V6.4.5~V6.4.8 成果零改动） ==")
ck('修顶栏设置按钮与按钮簇间的空白。' in html, "V6.4.8 日志原文仍在")
ck('.topbar-actions{position:relative' in html, "V6.4.8 顶栏按钮簇结构仍在")
ck('grid-template-columns:repeat(3,minmax(0,1fr))' in html, "V6.4.7 底栏三列栅格仍在")
ck('凸透镜3D可移动透镜，底栏一行三个。' in html, "V6.4.7 日志原文仍在")
ck('小孔成像加物距调节，顶栏按钮并入设置。' in html, "V6.4.6 日志原文仍在")
ck("'红苹果" in html and html.count("'红苹果") == 3, "知识图谱里的「红苹果」例题原样保留（3 处）")

print("\n== 6.5 DOM 嵌套体检（★ 上一轮漏掉的检查） ==")
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("v649s", os.path.join(BASE, "v649_structure.py"))
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_pfx = html[:html.find('window.__S3D_LENS__')]
t = _mod.Tree()
t.feed(_pfx)
bad_panels = [(p, par) for p, par in t.section_parents if par != ".wrap"]
ck(len(t.section_parents) == 12, ".panel 数量 12（实际 %d）" % len(t.section_parents))
ck(not bad_panels, "所有面板的父级都是 .wrap（异常 %d 个%s）"
   % (len(bad_panels), ("：" + str(bad_panels[:4])) if bad_panels else ""))
ck(t.parent.get("disp-rgb-ctrl") == ".ctrl", "#disp-rgb-ctrl 的父级是 .ctrl（实际 %s）" % t.parent.get("disp-rgb-ctrl"))
ck(t.parent.get("disp-obj-ctrl") == ".ctrl", "#disp-obj-ctrl 的父级是 .ctrl（实际 %s）" % t.parent.get("disp-obj-ctrl"))
ck(t.parent.get("disp-light") == "#disp-obj-ctrl", "#disp-light 仍在 #disp-obj-ctrl 内")
ck(t.parent.get("disp-dataBody") == ".dtable", "#disp-dataBody 在表格内")
ck(not t.errors, "无未匹配的收尾标签（%d 个）" % len(t.errors))
# .stage 的子级数量：色散面板必须仍是 [left, right] 两个
import re as _re
i = html.index('id="tab-disperse"')
j = html.index('<div class="data-panel">', i)
ck(html.count('<div class="right">', i, j) == 1 and html.count('<div class="left">', i, j) == 1,
   "色散面板 .stage 仍只有 left / right 两列（数据表没被顶出去）")

print("\n== 7. 场景内嵌完好 ==")
sc = re.search(r'window\.__S3D_LENS__ = "(.*)"', html)
ck(bool(sc), "__S3D_LENS__ 字面量可定位")
if sc:
    try:
        seg = re.sub(r'\\u2028', '\u2028', re.sub(r'\\u2029', '\u2029', sc.group(1).replace('<\\/script', '</script')))
        raw = json.loads('"' + seg + '"')
        ck(len(raw) == 689232, "场景解码长度 689,232 字符（实际 %d）" % len(raw))
        ck('grid-template-columns:repeat(3,minmax(0,1fr))' in raw, "场景底栏仍是三列栅格")
    except Exception as e:
        ck(False, "场景字面量解码失败：%s" % e)
ck('window.__ECL_HTML__ = ' in html and 'window.__S3D_SHADOW__ = ' in html, "另两个内嵌场景字面量仍在")

print("\n" + "=" * 66)
print("产物 %s  %d B" % (os.path.basename(DST), nbytes))
print("通过 %d 项；失败 %d 项" % (ok, len(fail)))
if fail:
    for f in fail:
        print("  ✗ " + f)
    sys.exit(1)
print("静态自检 ALL PASS")
