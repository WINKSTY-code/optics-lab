# -*- coding: utf-8 -*-
"""V6.5.0 母文件静态自检：拆块 node --check（浏览器口径）+ 结构断言 + 回归。"""
import os, re, subprocess

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
DST = os.path.join(BASE, "光学交互实验室_AI_v6.5.0.html")
TMP = os.path.join(BASE, "_chk650")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

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
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        print("  FAIL block %d: %s" % (i, r.stderr[:600]))
        fail.append("node --check block %d" % i)
    nb += 1
ck(True, "script 块 %d 个全部通过 node --check" % nb)
ck(len(blocks) == 17, "顶层 script 块数 == 17（v6.4.26 为 16 + 新增常量块 1，实际 %d）" % len(blocks))
ck(len(re.findall(r"</script(?=[\s>/])", html)) == 17, "脚本收尾标签字面量 == 17")
ck(len(re.findall(r"<script", html)) == 31, "<script 计数 == 31（36 - 抽走的 6 份库 + 常量块 1，实际 %d）"
   % len(re.findall(r"<script", html)))

print("\n== 2. three.js 集中存放（方案 C 核心） ==")
ck(html.count('window.__THREE_SRC__ = "') == 1, "window.__THREE_SRC__ 定义 1 处")
ck(html.count('window.__THREE_SRC_SHADOW__ = "') == 1, "window.__THREE_SRC_SHADOW__ 定义 1 处")
ck(html.count("window.__threeInject__ = function") == 1, "__threeInject__ 定义 1 处")
ck('window.__THREE_SRC__ = "/*' in html or 'window.__THREE_SRC__ = "\\n' in html,
   "r147 常量以库头（注释/换行）起头")
ck(html.count("__S3D_THREE_LIB__") == 11, "占位标记 11 处（6 处占位 + 5 处引用），实际 %d" % html.count("__S3D_THREE_LIB__"))
ck(html.count("\\n__S3D_THREE_LIB__\\n") == 6, "内嵌页独立占位标记 6 处")
# 抽库后：6 个内嵌页里都不再出现内联库（THREE.REVISION 只剩常量块里的 2 处）
ck(html.count("t.REVISION=e") == 2, "t.REVISION=e 只剩常量块里的 2 处（r147 + r150），实际 %d" % html.count("t.REVISION=e"))
ck(html.count("Multiple instances of Three.js being imported") == 3,
   "「Multiple instances」串 3 处 = 两份库各 1 + 常量块注释引用 1（实际 %d）"
   % html.count("Multiple instances of Three.js being imported"))
# 挂载层两处都已接上回填
ck("var eclSrc = window.__threeInject__ ? window.__threeInject__(SRC, false) : SRC;" in html,
   "ECL 挂载层已接回填")
ck("src = window.__threeInject__(src, k === 'shadow');" in html, "S3D 挂载层已接回填（按 key 区分构建）")
# 命名避险：不得出现裸的 window.__THREE__ 赋值（three.js UMD 自己会占用该名）
_stripped = html.replace("window.__THREE_SRC__", "").replace("window.__THREE_SRC_SHADOW__", "")
ck("window.__THREE__ = " not in _stripped, "未使用与 three.js UMD 撞名的 window.__THREE__")
for nm in ["__ECL_HTML__", "__S3D_PINHOLE__", "__S3D_REFL__", "__S3D_LENS__",
           "__S3D_MIRROR__", "__S3D_SHADOW__"]:
    ck(html.count("window.%s = " % nm) == 1, "内嵌页字面量 %s 仍在（1 处）" % nm)

print("\n== 3. 移除 E2E 自检钩子（审计 P1-4） ==")
ck("function runE2E" not in html, "runE2E 定义已删除")
ck("#e2e" not in html, "#e2e hash 触发已删除")
ck("e2e-report" not in html, "#e2e-report 输出容器已删除")
ck("window.AI.runE2E" not in html, "window.AI 上的 runE2E 导出已删除")
_seg = html[html.index("window.AI = AI"):html.index("window.AI = AI") + 900]
ck("runE2E" not in html[html.rindex("return { tts"):html.rindex("return { tts") + 700],
   "AI 模块 return 里已无 runE2E")
ck("if(!curStudent && !seen){ setTimeout(()=>showStudentModal(true), 400); }" in html,
   "首屏身份弹窗的 #e2e 例外已同步移除")

print("\n== 4. 版本号四处同步 + 更新日志 ==")
ck("var BUILD = 'v6.5.0'" in html, "BUILD == v6.5.0")
ck("return 'v6.5.0';" in html, "报告兜底 RPT_BUILD == v6.5.0")
ck('">v6.5.0</div>' in html, "右下角角标文本 == v6.5.0")
ck('title="光学交互实验室 V6.5.0 ' in html, "角标 title 已同步")
ck(html.count("v6.4.26") == 0, "小写 v6.4.26 零残留")
ck(html.count("v6.5.0") == 3, "小写 v6.5.0 == 3 处（实际 %d）" % html.count("v6.5.0"))
m = re.search(r'<span class="log-ver">V6\.5\.0</span><span class="log-date">([\d-]+)</span></div>\s*<p>(.*?)</p>', html)
ck(bool(m), "更新日志首条为 V6.5.0")
if m:
    ck(m.group(1) == "2026-09-21", "日志日期 2026-09-21（实际 %s）" % m.group(1))
    ck(len(m.group(2)) <= 20, "日志正文 %d 字 <= 20：%s" % (len(m.group(2)), m.group(2)))
ck(html.count('class="log-item cur"') == 1, "只有 1 条 cur（最新一条）")
ck(html.count('<span class="log-ver">V6.5.0</span>') == 1, "V6.5.0 日志条目唯一")

print("\n== 5. 回归：既有结构与接口未变 ==")
ck(html.count('class="tab-btn') == 11, '导航按钮 11 个（实际 %d）' % html.count('class="tab-btn'))
ck("var MODULES = {}" in html or "const MODULES = {}" in html, "MODULES 注册表仍在")
ck(html.count('id="cv-judge"') == 1, "挑战模式判卷画布 #cv-judge 仍在")
ck(html.count('id="line-mode"') == 1 and html.count('id="line-reset"') == 1, "直线传播控件 id 仍在")
ck(html.count('id="line-eclIfr"') == 1, "日食月食 iframe #line-eclIfr 仍在")
ck(html.count("__rbErrors") >= 1, "自带错误账本仍在")
ck(html.count("var SRC = { refl: window.__S3D_REFL__") == 1, "S3D 场景表仍在")
ck(html.count("var SRC = window.__ECL_HTML__ || '';") == 1, "ECL 场景表仍在")
ck(html.count("playWelcomeOnLoad") >= 1 and html.count("maybeShowHint") >= 1, "首屏启动链路仍在")
ck(html.count("function reclaim") >= 1 and html.count("_lostN") >= 2, "3D 上下文自愈仍在")

print("-" * 66)
print("通过 %d 项，失败 %d 项" % (ok, len(fail)))
print("产物 %s (%d B = %.2f MB)" % (os.path.basename(DST), nbytes, nbytes / 1048576))
if fail:
    print("失败清单：")
    for f in fail:
        print("  - " + f)
    raise SystemExit(1)
