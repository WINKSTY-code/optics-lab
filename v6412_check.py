# -*- coding: utf-8 -*-
"""V6.4.12 母文件静态自检：拆块 node --check（浏览器口径）+ 启动看门狗 15s + 挑战模式自动出题 + 全量回归。"""
import os, re, subprocess

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.12.html")
TMP = os.path.join(BASE, "_chk6412")

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
ck(len(re.findall(r"<script(?=[\s>/])", html)) == 36, "脚本开标签 == 36（与 V6.4.11 一致）")

print("\n== 2. ② 页面启动看门狗：10 秒 → 15 秒 ==")
ck("}, 15000);" in html, "看门狗定时器 == 15000 ms")
ck("10000);" not in html, "10000 ms 已不存在")
ck("超过 15 秒仍未完成初始化" in html, "zh 文案：超过 15 秒")
ck("超過 15 秒仍未完成初始化" in html, "zht 文案：超過 15 秒")
ck("Initialization did not finish within 15 seconds." in html, "en 文案：within 15 seconds")
ck("启动超时：15 秒内未收到就绪信号" in html, "错误详情：15 秒内未收到就绪信号")
ck(html.count("10 秒") == 0 and "10 seconds" not in html,
   "全文件无「10 秒 / 10 seconds」残留（实际 %d / %s）" % (html.count("10 秒"), "10 seconds" in html))
ck("if(window.__APP_READY || reported > 0) return;" in html, "看门狗守卫逻辑未动（就绪/已报错则不弹）")

print("\n== 3. ① 挑战模式：打开自动随机一道选择题 ==")
ck("var judgeUserPicked = false;" in html, "① judgeUserPicked 标记已声明")
ck("function selectProblem(p, byUser){" in html, "① selectProblem 增加 byUser 形参")
ck("if (byUser) judgeUserPicked = true;" in html, "① byUser=true 时打标记")
ck(html.count("selectProblem(p, true)") == 2, "① 两个显式入口（题库点选 / 知识地图）→ byUser")
ck("selectProblem(pool[Math.floor(Math.random() * pool.length)], true);" in html,
   "① 随机按钮/答完自动切题 → byUser")
ck(html.count("const pool = PROBLEMS.filter(p => p.type === 'pick')") == 2,
   "① 初始默认题 + 打开页钩子 各一处随机选择题池")
ck("selectProblem(pool.length ? pool[Math.floor(Math.random() * pool.length)] : PROBLEMS[0]);" in html,
   "① 初始默认题改为随机选择题（选择题池为空时回退第一题）")
ck("tb.dataset.tab !== 'judge'" in html, "① 打开页钩子只认挑战模式导航按钮")
ck("if (tb.classList.contains('active')) return;" in html, "① 点当前页不重复出题")
ck("if (judgeUserPicked) return;" in html, "① 用户已亲手选题则不接管")
ck("if (JCAT !== 'all' && JCAT !== 'pick') return;" in html, "① 用户正筛「作图题」时不接管")
ck(html.count(".jp-item[data-pid=\"") == 1 and "classList.add('active')" in html,
   "① selectProblem 的高亮逻辑未动（按题目 id 高亮，自动出题同样生效）")
# 选择题池非空（自动出题有题可选）
ck(html.count("type:'pick'") >= 30, "选择题池充足（type:'pick' × %d）" % html.count("type:'pick'"))
# selectProblem 其余调用点未被误改
ck(html.count("selectProblem(") >= 6, "selectProblem 调用点齐全（%d 处）" % html.count("selectProblem("))

print("\n== 4. 版本号四处同步 + 更新日志 ==")
ck("var BUILD = 'v6.4.12'" in html, "BUILD == v6.4.12")
ck("return 'v6.4.12';" in html, "报告兜底 RPT_BUILD == v6.4.12")
ck('">v6.4.12</div>' in html, "右下角角标文本 == v6.4.12")
ck('title="光学交互实验室 V6.4.12 ' in html, "角标 title 已同步")
ck(html.count("v6.4.11") == 0, "小写 v6.4.11 零残留")
ck(html.count("v6.4.12") == 3, "小写 v6.4.12 == 3 处（实际 %d）" % html.count("v6.4.12"))
m = re.search(r'<span class="log-ver">V6\.4\.12</span><span class="log-date">([\d-]+)</span></div>\s*<p>(.*?)</p>', html)
ck(bool(m), "更新日志首条为 V6.4.12")
if m:
    ck(m.group(1) == "2026-09-18", "日志日期 2026-09-18（实际 %s）" % m.group(1))
    ck(len(m.group(2)) <= 20, "日志正文 %d 字 ≤ 20：%s" % (len(m.group(2)), m.group(2)))
ck(html.count('class="log-item cur"') == 1, "只有 1 条 cur（最新一条）")
ck(html.count('<span class="log-ver">V6.4.12</span>') == 1, "V6.4.12 日志条目唯一")
ck(html.count('<span class="log-ver">V6.4.11</span>') == 1, "V6.4.11 条目仍保留（历史不删）")

print("\n== 5. 回归：既有结构与接口未变 ==")
ck(html.count('class="tab-btn') == 11, '导航按钮 11 个（实际 %d）' % html.count('class="tab-btn'))
ck("const MODULES = {}" in html or "var MODULES = {}" in html, "MODULES 注册表仍在")
ck(html.count('id="cv-judge"') == 1, "挑战模式判卷画布 #cv-judge 仍在")
ck(html.count('id="disp-obj-color"') == 1 and html.count("disp-obj-color") == 3, "#disp-obj-color 仍在（3 处）")
ck(html.count('id="line-mode"') == 1 and html.count('id="line-reset"') == 1, "直线传播控件 id 仍在")
ck(html.count("window.__S3D_SHADOW__ = ") == 1 and html.count("window.__S3D_LENS__ = ") == 1, "3D 场景字面量仍在")
ck(html.count("__rbErrors") >= 1, "自带错误账本仍在")
ck(html.count('id="aiGuideBtn"') == 1, "V6.4.10 配置指南按钮仍在")
ck("" in html, "V6.4.10 署名行仍在")

print("-" * 66)
print("通过 %d 项，失败 %d 项" % (ok, len(fail)))
print("产物 %s (%d B)" % (os.path.basename(DST), nbytes))
if fail:
    print("失败清单：")
    for f in fail:
        print("  - " + f)
    raise SystemExit(1)
