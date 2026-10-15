# -*- coding: utf-8 -*-
"""V6.4.11 母文件静态自检：拆块 node --check（浏览器口径）+ 结构断言 + 全量回归。"""
import os, re, subprocess

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.11.html")
TMP = os.path.join(BASE, "_chk6411")

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
ck(len(re.findall(r"<script(?=[\s>/])", html)) == 36, "脚本开标签 == 36（与 V6.4.9 一致）")

print("\n== 2. ① AI 设置：「前往官网」右侧新增「配置指南」 ==")
ck('id="aiGuideBtn"' in html, "① 按钮 #aiGuideBtn 存在")
ck('aria-controls="aiGuidePanel"' in html, "① 按钮带 aria-controls（无障碍）")
ck('id="aiGuidePanel" class="ai-guide" hidden' in html, "① 指南面板默认收起（hidden）")
ck("function aiGuideHtml()" in html, "① 指南内容由 aiGuideHtml() 生成")
ck("$('aiGuideBtn').onclick" in html, "① 展开/收起已绑定")
ck(".ai-guide[hidden]{display:none;}" in html, "① [hidden] 显式兜底（防 grid/flex 提权）")
# 位置：指南按钮必须在「前往官网」按钮之后、tokenInfo 之前
i_visit = html.index('id="aiVisitSite"')
i_guide = html.index('id="aiGuideBtn"')
i_token = html.index('id="aiTokenInfo"')
ck(i_visit < i_guide < i_token, "① 按钮紧挨「前往官网」右侧，面板插在按钮行之后")
# 三语词条齐备
for k in ("aiCfg.guide", "aiCfg.gTitle", "aiCfg.g1", "aiCfg.g2", "aiCfg.g3",
          "aiCfg.gFaqTitle", "aiCfg.gFaq1", "aiCfg.gFaq2", "aiCfg.gFaq3", "aiCfg.gFaq4"):
    ck(("'%s':" % k) in html, "① 词条 %s 存在" % k)
ck(html.count("aiCfg.g1':") == 1 and html.count("T('aiCfg.g1')") == 1,
   "① 词条 aiCfg.g1 定义与引用各 1 处")
for k in ("aiCfg.g2", "aiCfg.g3", "aiCfg.gFaq1", "aiCfg.gFaq2", "aiCfg.gFaq3", "aiCfg.gFaq4"):
    m = re.search(re.escape("'%s':" % k) + r"\s*\{zh:'(.*?)', zht:'(.*?)', en:'(.*?)'\},", html)
    ck(bool(m) and all(m.group(i).strip() for i in (1, 2, 3)), "① 词条 %s 三语齐全" % k)

print("\n== 3. ② 「关于」弹窗：作者署名下补单位署名 ==")
i_h2 = html.index('id="aboutTitle"')
seg = html[i_h2:i_h2 + 700]
i_line = seg.index("")
i_sub = seg.index('id="aboutSub"')
ck(i_line < i_sub, "② 署名行位于 h2 之后、aboutSub 之前")
ck("" in seg, "② 使用与正文一致的裸 <p> 格式")
_line_tag = re.search(r"<p[^>]*></p>", seg)
ck(bool(_line_tag) and _line_tag.group(0) == "",
   "② 署名行是裸 <p>（无 class / 无 data-i18n → 不随语言切换、不被 applyLang 覆写）")
ck("" not in html.replace(seg, ""), "② 全文仅此 1 处")

print("\n== 4. ③ 版本号四处同步 + 更新日志 ==")
ck("var BUILD = 'v6.4.11'" in html, "BUILD == v6.4.11")
ck("return 'v6.4.11';" in html, "报告兜底 RPT_BUILD == v6.4.11")
ck('">v6.4.11</div>' in html, "右下角角标文本 == v6.4.11")
ck('title="光学交互实验室 V6.4.11 ' in html, "角标 title 已同步")
ck(html.count("v6.4.9") == 0, "小写 v6.4.9 零残留")
ck(html.count("v6.4.10") == 0, "小写 v6.4.10 零残留")
ck(html.count("v6.4.11") == 3, "小写 v6.4.11 == 3 处（实际 %d）" % html.count("v6.4.11"))
m = re.search(r'<span class="log-ver">V6\.4\.11</span><span class="log-date">([\d-]+)</span></div>\s*<p>(.*?)</p>', html)
ck(bool(m), "更新日志首条为 V6.4.11")
if m:
    ck(m.group(1) == "2026-09-18", "日志日期 2026-09-18（实际 %s）" % m.group(1))
    ck(len(m.group(2)) <= 20, "日志正文 %d 字 ≤ 20：%s" % (len(m.group(2)), m.group(2)))
    # 用户要求：署名那一行不写进更新日志
    ck("" not in m.group(2) and "东亭" not in m.group(2), "署名改动未写进更新日志")
ck(html.count('class="log-item cur"') == 1, "只有 1 条 cur（最新一条）")
ck(html.count('<span class="log-ver">V6.4.11</span>') == 1, "V6.4.11 日志条目唯一")
ck(html.count('<span class="log-ver">V6.4.10</span>') == 1, "V6.4.10 条目仍保留（历史不删）")

print("\n== 4b. 指南第①步：不指定平台，改为泛指 ==")
_g1 = re.search(r"'aiCfg\.g1':\s*\{.*?\},", html, re.S)
ck(bool(_g1), "定位到 aiCfg.g1 词条")
_g1txt = _g1.group(0) if _g1 else ""
ck("智谱" not in _g1txt and "智譜" not in _g1txt and "Zhipu" not in _g1txt,
   "指南第①步不再点名任何具体平台")
ck("换成你想用的 AI 大模型即可" in _g1txt, "zh：用「你想用的 AI 大模型即可」表述")
ck("換成你想用的 AI 大模型即可" in _g1txt, "zht：同步改写")
ck("to any AI model you want to use." in _g1txt, "en：any AI model you want to use")
ck("⚡" not in _g1txt and "⭐" not in _g1txt, "指南第①步不再带「推荐」星标")
# 既有 UI 的推荐项必须原样保留
ck("'aiCfg.optZhipu': {zh:'智谱 GLM ⭐ 推荐'" in html,
   "Provider 下拉里的既有推荐项 aiCfg.optZhipu 原样保留")
ck("'aiCfg.optZhipu': {zh:'智谱 GLM ⭐ 推荐', zht:'智譜 GLM ⭐ 推薦', en:'Zhipu GLM ⭐ recommended'}," in html,
   "optZhipu 三语完整未动")
# 第②步的「先选大模型」顺序依赖仍在
_g2 = re.search(r"'aiCfg\.g2':\s*\{.*?\},", html, re.S).group(0)
ck("先在①选好大模型" in _g2 and "先在①選好大模型" in _g2, "第②步仍点明「先选好大模型」的顺序依赖")
ck("前往官网" in _g2 and "Visit site" in _g2, "第②步仍指向「前往官网」")

print("\n== 5. 回归：既有结构与接口未变 ==")
ck(html.count('class="tab-btn') == 11, '导航按钮 11 个（实际 %d）' % html.count('class="tab-btn'))
ck(html.count('<section id="tab-') == 12 - 1 or html.count('class="panel"') >= 11,
   "面板数量保持")
ck(html.count("var MODULES = {}") == 1 or "const MODULES = {}" in html, "MODULES 注册表仍在")
ck(html.count('id="cv-judge"') == 1, "挑战模式判卷画布 #cv-judge 仍在")
ck(html.count('id="disp-obj-color"') == 1 and html.count("disp-obj-color") == 3,
   "V6.4.10/6.4.9 的 #disp-obj-color 仍在（DOM 1 + JS 2 = 3 处）")
ck(html.count('id="line-mode"') == 1 and html.count('id="line-reset"') == 1, "直线传播控件 id 仍在")
ck(html.count("window.__S3D_SHADOW__ = ") == 1, "路灯影子 3D 场景字面量仍在")
ck(html.count("window.__S3D_LENS__ = ") == 1, "凸透镜 3D 场景字面量仍在")
ck(html.count("__rbErrors") >= 1, "自带错误账本仍在")

print("-" * 66)
print("通过 %d 项，失败 %d 项" % (ok, len(fail)))
print("产物 %s (%d B)" % (os.path.basename(DST), nbytes))
if fail:
    print("失败清单：")
    for f in fail:
        print("  - " + f)
    raise SystemExit(1)
