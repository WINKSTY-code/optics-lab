# -*- coding: utf-8 -*-
"""V6.4.26 -> V6.5.0
方案 C（审计报告 P0-2 的方案 C）：three.js 抽成集中常量存放，消灭「6 处各自为政」；
并把审计 P1-4 的自检钩子 runE2E 从生产文件里移除。

改动：
 R0   新增 three.js 集中常量块（__THREE_SRC__ / __THREE_SRC_SHADOW__ / __threeInject__）
 R1-6 6 个内嵌子页内联的 three.js 库整段 -> 占位标记 __S3D_THREE_LIB__
 R7   ECL 挂载层：挂载时回填 three.js
 R8   S3D 挂载层：挂载时回填 three.js（按 key 区分影子页的另一个构建）
 R9   S3D 挂载层头注释：修正「自带的 three.js r147」这句与事实不符的说明
 R10  S3D 源码块头注释：补 V6.5.0 说明
 R11  ECL 源码块头注释：补 V6.5.0 说明
 R12  删除 runE2E 定义 + #e2e 触发块
 R13  首屏身份弹窗的 #e2e 例外同步移除 + return 里的 runE2E 导出
 R14  版本号 BUILD / RPT_BUILD / ver-badge / title
 R15  更新日志新增 V6.5.0 条目（正文 <= 20 字）
"""
import os
import re

SRC = "光学交互实验室_AI_v6.4.26.html"
DST = "光学交互实验室_AI_v6.5.0.html"
LOG = []
LINE_DELTA = [0]

BS = chr(92)
BQ = BS + '"'
ESC_CLOSE = "<" + BS + "/script>"
UMD = "!function(t,e){" + BQ + "object"
MARKER = "__S3D_THREE_LIB__"


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LINE_DELTA[0] += (new.count("\n") - old.count("\n")) * c
    LOG.append("OK  %-50s x%d" % (label, c))
    return s.replace(old, new)


def unesc(s):
    """把内嵌页 JS 字符串字面量还原成真实 HTML（与浏览器读到的 srcdoc 一致）"""
    out = []; k = 0; n = len(s)
    while k < n:
        c = s[k]
        if c != BS:
            out.append(c); k += 1; continue
        k += 1
        if k >= n: break
        e = s[k]
        if e == "n": out.append("\n"); k += 1
        elif e == "t": out.append("\t"); k += 1
        elif e == "r": out.append("\r"); k += 1
        elif e == "u": out.append(chr(int(s[k + 1:k + 5], 16))); k += 5
        else: out.append(e); k += 1
    return "".join(out)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
N_LF0 = s.count("\n")
n_open0 = len(re.findall(r"<script", s))
n_close0 = len(re.findall(r"</script(?=[\s>/])", s))
lines = s.split("\n")

# ================================================================ R1~R6 抽库
embeds = []
for i, l in enumerate(lines):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*"', l)
    if m:
        embeds.append({"name": m.group(1), "i": i, "st": m.end(), "en": l.rfind('";')})
assert len(embeds) == 6, "内嵌页数量异常: %d" % len(embeds)
assert [e["name"] for e in embeds] == ["__ECL_HTML__", "__S3D_PINHOLE__", "__S3D_REFL__",
                                       "__S3D_LENS__", "__S3D_MIRROR__", "__S3D_SHADOW__"], embeds


def lib_span(body):
    i_umd = body.find(UMD)
    assert i_umd > 0, "未找到 UMD 头"
    sc = body.rfind("<script>", 0, i_umd)
    assert sc > 0, "未找到库的 <script> 开标签"
    i_rev = body.find("t.REVISION=e")
    assert i_rev > i_umd, "未找到 t.REVISION=e"
    k = body.find("}));", i_rev)
    assert k > i_rev, "未找到库尾 }));"
    cl = body.find(ESC_CLOSE, k)
    assert cl > k, "未找到库的脚本收尾标签"
    return sc, cl + len(ESC_CLOSE), body[sc + len("<script>"):cl]


raw_lib = {}
orig_body = {}
for e in embeds:
    l = lines[e["i"]]
    body = l[e["st"]:e["en"]]
    assert body.count(UMD) == 1, "%s 里 UMD 头不止一处" % e["name"]
    assert body.count("<script>") >= 1
    sc, ee, inner = lib_span(body)
    raw_lib[e["name"]] = inner
    orig_body[e["name"]] = unesc(body)
    lines[e["i"]] = l[:e["st"]] + body[:sc] + MARKER + body[ee:] + l[e["en"]:]
    LOG.append("OK  %-50s (移出 %d B 内联库)" % ("R1-6 抽库 " + e["name"], ee - sc))

s = "\n".join(lines)
assert s.count(MARKER) == 6, s.count(MARKER)

REFL_LIB = raw_lib["__S3D_REFL__"]
SHADOW_LIB = raw_lib["__S3D_SHADOW__"]
# r147 五份的库体只允许差首尾空白 / PINHOLE 那句装饰性注释 —— 交叉确认可共用同一常量
# 注意：必须在【反转义域】比对 —— 文件里真实换行写成了两字符 \n，转义域里它不是空白
_nw = lambda t: re.sub(r"\s+", "", t)
_nb = lambda t: _nw(unesc(t))
_base = _nb(REFL_LIB)
for _n in ("__ECL_HTML__", "__S3D_REFL__", "__S3D_LENS__", "__S3D_MIRROR__"):
    assert _nb(raw_lib[_n]) == _base, "%s 与 REFL 库体不等价" % _n
_pin = _nb(raw_lib["__S3D_PINHOLE__"]).replace(
    "/*!three.jsr147·内嵌单文件（离线可用）*/", "")
assert _pin == _base, "PINHOLE 库体（去装饰注释后）与 REFL 不等价"
assert _nb(SHADOW_LIB) != _base, "SHADOW 竟与 r147 同体，方案前提有变"

# ================================================================ R0 常量块
R0_ANCHOR = ("<script>\n"
             "/* ==========================================================================\n"
             "   V5.2.0 · 直线传播实验内嵌的")
R0_NEW = "\n".join([
    "<script>",
    "/* ==========================================================================",
    "   V6.5.0 · three.js 集中存放（防漂移）",
    "   --------------------------------------------------------------------------",
    "   · 6 个内嵌 3D 子页原先各自内联一份 three.js：其中 5 份（日食月食 / 小孔 /",
    "     反射 / 凸透镜 / 平面镜）是同一个构建（r147），1 份（路灯影子）是另一个",
    "     构建（r150+ 弃用版）。同一页跑两套构建 → OrbitControls 手感、色彩管理、",
    "     阴影贴图默认值都可能不一致；且升级 three.js 要改 6 处，极易漏改、越改越偏。",
    "   · 现在把两份库各抽成一个常量，子页源码里只留占位标记 " + MARKER + "，",
    "     挂载时由 __threeInject__ 回填。库在文件里只此一份，漂移被结构性消除；",
    "     顺带把 6 份重复库收敛为 2 份，文件体积下降约 2.4 MB。",
    "   · 命名刻意不用 window.__THREE__：three.js 的 UMD 自身就用 window.__THREE__",
    "     存放命名空间，并据此告警「Multiple instances of Three.js being imported」，",
    "     父页复用同名是隐患，故取名 __THREE_SRC__ / __THREE_SRC_SHADOW__。",
    "   ========================================================================== */",
    'window.__THREE_SRC__ = "' + REFL_LIB + '";',
    'window.__THREE_SRC_SHADOW__ = "' + SHADOW_LIB + '";',
    "/* 挂载时把子页源码里的占位标记换回 three.js 的脚本标签。",
    "   用 split/join 做字面替换：String.replace 会把替换串里的 $& / $1 当反向引用，",
    "   而压缩库正文里出现 $ 的概率不为零，必须避开这个坑。 */",
    "window.__threeInject__ = function(html, shadow){",
    "  if (typeof html !== 'string' || html.indexOf('" + MARKER + "') < 0) return html;",
    "  var lib = shadow ? window.__THREE_SRC_SHADOW__ : window.__THREE_SRC__;",
    "  if (!lib) return html;",
    "  return html.split('" + MARKER + "').join('<scr' + 'ipt>' + lib + '<" + BS + "/scr' + 'ipt>');",
    "};",
    "</script>",
    "",
]) + "\n"
s = rep(s, R0_ANCHOR, R0_NEW + R0_ANCHOR, 1, "R0 新增 three.js 集中常量块")

# ================================================================ R7 ECL 挂载层
s = rep(s,
        "    try { ifr.setAttribute('srcdoc', SRC); }",
        "    /* V6.5.0：子页源码里的 three.js 是占位标记，挂载时用集中常量回填 */\n"
        "    var eclSrc = window.__threeInject__ ? window.__threeInject__(SRC, false) : SRC;\n"
        "    try { ifr.setAttribute('srcdoc', eclSrc); }",
        1, "R7 ECL 挂载时回填 three.js")

# ================================================================ R8 S3D 挂载层
s = rep(s,
        "    var src = SRC[k];\n"
        "    if (!src){ console.warn('[S3D] 缺少 3D 场景源码:', k); return false; }\n"
        "    try {\n"
        "      ifrOf(k).setAttribute('srcdoc', src);",
        "    var src = SRC[k];\n"
        "    if (!src){ console.warn('[S3D] 缺少 3D 场景源码:', k); return false; }\n"
        "    /* V6.5.0：子页源码里的 three.js 是占位标记，挂载时用集中常量回填\n"
        "       （路灯影子页用的是另一个构建，故按 key 区分） */\n"
        "    if (window.__threeInject__) src = window.__threeInject__(src, k === 'shadow');\n"
        "    try {\n"
        "      ifrOf(k).setAttribute('srcdoc', src);",
        1, "R8 S3D 挂载时回填 three.js")

# ================================================================ R9 修正失真注释
s = rep(s,
        "   · 五个 3D 场景各自是【自包含单文件】（自带的 three.js r147 + OrbitControls +\n"
        "     场景外壳），这里只负责：懒挂载（首次切到 3D 才注入 srcdoc）、把父页参数\n"
        "     通过 postMessage 推给子场景、全屏进出、切页时暂停渲染省电。",
        "   · 五个 3D 场景各自是【自包含单文件】（three.js + OrbitControls + 场景外壳）。\n"
        "     ★ V6.5.0：three.js 由 6 份内联改为集中存放（文件顶部 __THREE_SRC__ /\n"
        "     __THREE_SRC_SHADOW__ 常量，本层挂载时经 __threeInject__ 回填）。此处原注释写\n"
        '     "自带的 three.js r147" 与事实不符（影子页用的是另一个构建），一并修正。\n'
        "   · 本层只负责：懒挂载（首次切到 3D 才注入 srcdoc）、把父页参数\n"
        "     通过 postMessage 推给子场景、全屏进出、切页时暂停渲染省电。",
        1, "R9 修正 S3D 挂载层失真注释")

s = rep(s,
        "   V6.0.0 · 三个 3D 立体场景的完整源码（各自自包含：内联 three.js r147 +\n"
        "   OrbitControls + 场景外壳 + 场景脚本；无任何外链、无网络请求、离线可用）\n"
        "   装载顺序：三个源码块 → 样式 → 挂载层脚本。",
        "   V6.0.0 · 三个 3D 立体场景的完整源码（各自自包含：three.js + OrbitControls +\n"
        "   场景外壳 + 场景脚本；无任何外链、无网络请求、离线可用）\n"
        "   ★ V6.5.0：各块内联的 three.js 已改为占位标记 __S3D_THREE_LIB__，库体集中存放于\n"
        "   文件顶部常量，挂载时由 __threeInject__ 回填（详见该常量块注释）。\n"
        "   装载顺序：三个源码块 → 样式 → 挂载层脚本。",
        1, "R10 S3D 源码块头注释")

s = rep(s,
        "   V5.2.0 · 直线传播实验内嵌的「日食与月食 3D 演示」单文件源码（原样保存）\n"
        "   来源：日食与月食 3D演示.html（自包含：内联 three.js + OrbitControls + 演示逻辑，",
        "   V5.2.0 · 直线传播实验内嵌的「日食与月食 3D 演示」单文件源码（原样保存）\n"
        "   ★ V6.5.0：内联的 three.js 已改为占位标记 __S3D_THREE_LIB__，库体集中存放于\n"
        "   文件顶部常量，挂载时回填（详见 __THREE_SRC__ 常量块）。\n"
        "   来源：日食与月食 3D演示.html（自包含：three.js + OrbitControls + 演示逻辑，",
        1, "R11 ECL 源码块头注释")

# ================================================================ R12 删 runE2E
_i1 = s.index("  // ---- v2.1 C2：内置 E2E 自检")
_i2 = s.index("  return { tts, stopTTS, callLLM, logOp, enterExp,")
_block = s[_i1:_i2]
assert _block.startswith("  // ---- v2.1 C2"), _block[:60]
assert _block.endswith("\n\n"), repr(_block[-20:])
assert "function runE2E(){" in _block and "if(location.hash === '#e2e'){" in _block
assert _block.count("function runE2E") == 1
LINE_DELTA[0] -= _block.count("\n")
s = s[:_i1] + s[_i2:]
LOG.append("OK  %-50s (删 %d 行)" % ("R12 删 runE2E 定义与 #e2e 触发块", _block.count("\n")))

s = rep(s,
        "cfg:()=>cfg, runE2E, showStudentModal",
        "cfg:()=>cfg, showStudentModal",
        1, "R13 移除 window.AI.runE2E 导出")

s = rep(s,
        "  // v2.1：首次使用弹身份选择（学生 / 老师）；本会话内不重复打扰；#e2e 自检模式跳过\n"
        "  (function firstRunGate(){\n"
        "    let seen = false;\n"
        "    try{ seen = sessionStorage.getItem(K+'_firstseen') === '1'; }catch(e){}\n"
        "    if(!curStudent && !seen && location.hash !== '#e2e'){ setTimeout(()=>showStudentModal(true), 400); }",
        "  // v2.1：首次使用弹身份选择（学生 / 老师）；本会话内不重复打扰\n"
        "  (function firstRunGate(){\n"
        "    let seen = false;\n"
        "    try{ seen = sessionStorage.getItem(K+'_firstseen') === '1'; }catch(e){}\n"
        "    if(!curStudent && !seen){ setTimeout(()=>showStudentModal(true), 400); }",
        1, "R13b 首屏身份弹窗的 #e2e 例外")

# ================================================================ R14 版本号
s = rep(s, "var BUILD = 'v6.4.26',", "var BUILD = 'v6.5.0',", 1, "R14a var BUILD")
s = rep(s, "    return 'v6.4.26';", "    return 'v6.5.0';", 1, "R14b RPT_BUILD 兜底")

R14C_OLD = ('<div class="ver-badge" title="光学交互实验室 V6.4.26 · ① 批作图题（AI 判卷）的「思考模式」'
            '改为跟随顶部 AI 设置的「深度思考模式」，不再自己硬关；② 判卷超时由写死的 20 秒改为与主链路'
            '一致的 180 秒（实测判卷默认模型关思考也要 27.2 秒，20 秒必然掐断）；③ 判卷设置弹窗与结果卡'
            '都标出当前思考模式。">v6.4.26</div>')
R14C_NEW = ('<div class="ver-badge" title="光学交互实验室 V6.5.0 · ① three.js 由 6 份内联改为 2 份常量集中'
            '存放（反射/凸透镜/平面镜/小孔/日食月食 用 r147，路灯影子用 r150 构建），挂载时回填，消除'
            '同页两构建与升级漏改的漂移风险，文件由 8.37 MB 降到约 5.9 MB；② 生产文件移除内置 E2E 自检'
            '钩子及它挂在 window.AI 上的导出，自检改由独立侧脚本承担；③ 修正内嵌页说明里「自带 '
            'three.js r147」这处与事实不符的注释。">v6.5.0</div>')
s = rep(s, R14C_OLD, R14C_NEW, 1, "R14c ver-badge")

# ================================================================ R15 更新日志
R15_OLD = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.26</span>'
           '<span class="log-date">2026-09-21</span></div>\n'
           '        <p>判卷（批作图题）的思考模式改为跟随 AI 设置，判卷超时与主链路统一为 180 秒。</p>\n'
           '      </div>')
R15_TEXT = "three.js 抽为常量，删自检钩子。"
assert len(R15_TEXT) <= 20, len(R15_TEXT)
R15_NEW = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.5.0</span>'
           '<span class="log-date">2026-09-21</span></div>\n'
           '        <p>' + R15_TEXT + '</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.26</span>'
           '<span class="log-date">2026-09-21</span></div>\n'
           '        <p>判卷（批作图题）的思考模式改为跟随 AI 设置，判卷超时与主链路统一为 180 秒。</p>\n'
           '      </div>')
s = rep(s, R15_OLD, R15_NEW, 1, "R15 更新日志")

# ================================================================ 收尾断言
n_open1 = len(re.findall(r"<script", s))
n_close1 = len(re.findall(r"</script(?=[\s>/])", s))
assert n_close1 == n_close0 + 1, "顶层脚本收尾标签应 +1: %d -> %d" % (n_close0, n_close1)
assert s.count("\n") == N_LF0 + LINE_DELTA[0], \
    "行数变化异常: %d -> %d（期望 %+d）" % (N_LF0, s.count("\n"), LINE_DELTA[0])
for bad in ["function runE2E", "#e2e", "runE2E,", "window.AI.runE2E", "e2e-report"]:
    assert bad not in s, "[FAIL] 残留：%s" % bad
assert "self runE2E" not in s
assert s.count('function runE2E') == 0
assert s.count(MARKER) == 11, "占位标记总数应 11（6 处占位 + 常量块/注释 5 处引用），实际 %d" % s.count(MARKER)
assert s.count(BS + "n" + MARKER + BS + "n") == 6, \
    "内嵌页里的独立占位标记应 6 处（前后各一个转义换行），实际 %d" % s.count(BS + "n" + MARKER + BS + "n")
assert s.count('window.__THREE_SRC__ = "') == 1
assert s.count('window.__THREE_SRC_SHADOW__ = "') == 1
assert s.count("window.__threeInject__ = function") == 1
for nm in ["__ECL_HTML__", "__S3D_PINHOLE__", "__S3D_REFL__", "__S3D_LENS__",
           "__S3D_MIRROR__", "__S3D_SHADOW__"]:
    assert s.count("window.%s = " % nm) == 1, nm
assert s.count("v6.4.26") == 0, "小写 v6.4.26 仍有残留 %d" % s.count("v6.4.26")
assert s.count("v6.5.0") == 3, "小写 v6.5.0 应 3 处（实际 %d）" % s.count("v6.5.0")
assert '<span class="log-ver">V6.5.0</span>' in s
assert s.count('class="log-item cur"') == 1
assert s.count('class="log-ver">V6.5.0<') == 1
assert "该注释与实现不符" not in s
assert s.count("var BUILD = 'v6.5.0'") == 1
assert s.count("return 'v6.5.0';") == 1
assert "window.__THREE__ " not in s.replace("window.__THREE_SRC__", "").replace("window.__THREE_SRC_SHADOW__", "")

# ================================================================ 重建等价性比对
lines2 = s.split("\n")
new_bodies = {}
for i, l in enumerate(lines2):
    m = re.match(r'\s*window\.(__[A-Z0-9_]+__)\s*=\s*"', l)
    if m and m.group(1) not in ("__THREE_SRC__", "__THREE_SRC_SHADOW__"):
        new_bodies[m.group(1)] = l[m.end():l.rfind('";')]
assert len(new_bodies) == 6, list(new_bodies)

nw = lambda t: re.sub(r"\s+", "", t)
print("\n== 重建等价性（占位标记回填 three.js 后 vs 原内嵌页，只允许空白/注释差异）==")
for nm in ["__ECL_HTML__", "__S3D_PINHOLE__", "__S3D_REFL__", "__S3D_LENS__",
           "__S3D_MIRROR__", "__S3D_SHADOW__"]:
    lib = SHADOW_LIB if nm == "__S3D_SHADOW__" else REFL_LIB
    inj = unesc(new_bodies[nm]).replace(MARKER, "<script>" + unesc(lib) + "</script>")
    if MARKER in unesc(new_bodies[nm]):
        pass
    old = orig_body[nm]
    a, b = nw(old), nw(inj)
    if nm == "__S3D_PINHOLE__":
        a = a.replace("/*!three.jsr147·内嵌单文件（离线可用）*/", "")
    same = (a == b)
    print("  %-18s 原 %7d 字 / 回填 %7d 字  去空白后 %s" % (nm, len(old), len(inj), "完全一致" if same else "!! 有差异"))
    assert same, "%s 回填后与原文不等价（非空白/注释差异）" % nm

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("---")
print("script 元素: opens %d->%d  closes %d->%d" % (n_open0, n_open1, n_close0, n_close1))
print("占位标记 %d 处；常量块 2 份库（r147 %d B / r150 %d B）" % (s.count(MARKER), len(REFL_LIB), len(SHADOW_LIB)))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
