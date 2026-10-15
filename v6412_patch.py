# -*- coding: utf-8 -*-
"""V6.4.12 补丁（v6.4.11 → v6.4.12）
① 打开挑战模式自动随机出一道选择题（原先固定选第一题——一道作图题，学生一进来面对空白画布）。
② 页面启动看门狗 10 秒 → 15 秒（网速慢 / 低端机 8MB 单文件还没初始化完就被弹「页面启动超时」）。
"""
import os, re

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.11.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.12.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-56s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, "r", encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)
closes0 = len(re.findall(r"</script(?=[\s>/])", s))
opens0 = len(re.findall(r"<script(?=[\s>/])", s))
V6411_BEFORE = s.count("V6.4.11")

# ============================================================
# ② 启动看门狗：10 秒 → 15 秒（含三语文案）
# ============================================================
s = rep(s,
        "ht:'页面启动超时', hp:'超过 10 秒仍未完成初始化。可能是浏览器扩展、安全策略或脚本错误阻塞了启动。',",
        "ht:'页面启动超时', hp:'超过 15 秒仍未完成初始化。可能是浏览器扩展、安全策略或脚本错误阻塞了启动。',",
        1, "② 看门狗文案 zh：10 秒 → 15 秒")
s = rep(s,
        "ht:'頁面啟動逾時', hp:'超過 10 秒仍未完成初始化。可能是瀏覽器擴充功能、安全策略或指令碼錯誤阻塞了啟動。',",
        "ht:'頁面啟動逾時', hp:'超過 15 秒仍未完成初始化。可能是瀏覽器擴充功能、安全策略或指令碼錯誤阻塞了啟動。',",
        1, "② 看门狗文案 zht：10 秒 → 15 秒")
s = rep(s,
        "ht:'Startup timed out', hp:'Initialization did not finish within 10 seconds.",
        "ht:'Startup timed out', hp:'Initialization did not finish within 15 seconds.",
        1, "② 看门狗文案 en：10 → 15 seconds")
s = rep(s,
        "d = '启动超时：10 秒内未收到就绪信号（window.__APP_READY）。",
        "d = '启动超时：15 秒内未收到就绪信号（window.__APP_READY）。",
        1, "② 错误详情文案：10 秒 → 15 秒")
s = rep(s,
        "  setTimeout(function(){\n    if(window.__APP_READY || reported > 0) return;\n    report('timeout', null);\n  }, 10000);",
        "  /* V6.4.12：看门狗 10s → 15s。8MB 单文件在慢网 / 低端机上初始化本来就慢，\n"
        "     10s 太紧，会被误判成「页面启动超时」把用户截断在报错浮层上。 */\n"
        "  setTimeout(function(){\n    if(window.__APP_READY || reported > 0) return;\n    report('timeout', null);\n  }, 15000);",
        1, "② 看门狗定时器：10000 → 15000 ms")

# ============================================================
# ①-a selectProblem 增加 byUser 标记
# ============================================================
s = rep(s,
        "function selectProblem(p){\n  STATE.problem = p;",
        "/* V6.4.12：当前题是否由用户【亲自】选的（题库点选 / 随机按钮 / 知识地图跳转 / 答完自动切题）。\n"
        "   「打开挑战模式自动随机出选择题」只在用户还没亲手选过题时才生效 ——\n"
        "   否则用户切到别的实验再回来，做到一半的题会被悄悄换掉。 */\n"
        "var judgeUserPicked = false;\n"
        "function selectProblem(p, byUser){\n"
        "  if (byUser) judgeUserPicked = true;\n"
        "  STATE.problem = p;",
        1, "①-a selectProblem 增加 byUser 标记")

# ============================================================
# ①-b 三处「用户亲自选题」的入口都打上标记
# ============================================================
s = rep(s,
        "      const p = PROBLEMS.find(x => x.id === target.dataset.pid);\n      if (p) selectProblem(p);",
        "      const p = PROBLEMS.find(x => x.id === target.dataset.pid);\n      if (p) selectProblem(p, true);",
        1, "①-b 题库列表点选 → byUser")
s = rep(s,
        "      const p = PROBLEMS.find(x => x.id === b.getAttribute('data-exp'));\n      if(p) selectProblem(p);",
        "      const p = PROBLEMS.find(x => x.id === b.getAttribute('data-exp'));\n      if(p) selectProblem(p, true);",
        1, "①-b 知识地图跳转 → byUser")
s = rep(s,
        "// V4.10.2：从选择题池随机跳一题（排除 excludeId）——随机按钮与\"答完自动切题\"共用\n"
        "function gotoRandomPick(excludeId){\n"
        "  const pool = PROBLEMS.filter(p => p.type === 'pick' && p.id !== excludeId);\n"
        "  if (!pool.length) return;\n"
        "  selectProblem(pool[Math.floor(Math.random() * pool.length)]);\n"
        "}",
        "// V4.10.2：从选择题池随机跳一题（排除 excludeId）——随机按钮与\"答完自动切题\"共用\n"
        "function gotoRandomPick(excludeId){\n"
        "  const pool = PROBLEMS.filter(p => p.type === 'pick' && p.id !== excludeId);\n"
        "  if (!pool.length) return;\n"
        "  selectProblem(pool[Math.floor(Math.random() * pool.length)], true);\n"
        "}",
        1, "①-b 随机按钮/答完自动切题 → byUser")

# ============================================================
# ①-c 初始默认题：第一题（作图）→ 随机一道选择题
# ============================================================
s = rep(s,
        "  // 默认选第一题\n  selectProblem(PROBLEMS[0]);",
        "  /* V6.4.12：默认不再固定第一题（一道作图题，学生进来先看到空白画布），\n"
        "     改为随机出一道【选择题】——点选项即判，门槛最低。\n"
        "     用户自己选过题之后就不再接管（见 selectProblem 的 byUser 标记）。 */\n"
        "  (function(){\n"
        "    const pool = PROBLEMS.filter(p => p.type === 'pick');\n"
        "    selectProblem(pool.length ? pool[Math.floor(Math.random() * pool.length)] : PROBLEMS[0]);\n"
        "  })();",
        1, "①-c 初始默认题改为随机选择题")

# ============================================================
# ①-d 每次「打开挑战模式」都自动随机一道选择题（除非用户已亲手选过题）
# ============================================================
s = rep(s,
        "  const pauseBtn = document.getElementById('judgePause');\n"
        "  if (pauseBtn) pauseBtn.addEventListener('click', toggleSessPause);\n"
        "  renderSessStats();\n"
        "}",
        "  const pauseBtn = document.getElementById('judgePause');\n"
        "  if (pauseBtn) pauseBtn.addEventListener('click', toggleSessPause);\n"
        "  renderSessStats();\n"
        "\n"
        "  /* V6.4.12：每次「打开挑战模式」都自动随机一道选择题 —— 仅当用户还没亲手选过题、\n"
        "     且当前分类不是「只看作图题」（用户明确筛了作图题却给他弹选择题是自相矛盾）。\n"
        "     用捕获阶段 click 委托监听导航按钮：与「切页暂停 3D」同一套路，\n"
        "     程序化 switchTab('judge')（如知识地图跳转）不经过这里 —— 那类跳转本就带着明确要做的题。 */\n"
        "  document.addEventListener('click', (e) => {\n"
        "    const tb = e.target.closest('.tab-btn');\n"
        "    if (!tb || tb.dataset.tab !== 'judge') return;\n"
        "    if (tb.classList.contains('active')) return;          // 点当前页不动\n"
        "    if (judgeUserPicked) return;                          // 用户已亲手选题 → 不接管\n"
        "    if (JCAT !== 'all' && JCAT !== 'pick') return;        // 用户正筛作图题 → 不接管\n"
        "    const pool = PROBLEMS.filter(p => p.type === 'pick');\n"
        "    if (pool.length) selectProblem(pool[Math.floor(Math.random() * pool.length)]);\n"
        "  }, true);\n"
        "}",
        1, "①-d 打开挑战模式自动随机选择题")

# ============================================================
# ③ 版本号四处同步 + 更新日志
# ============================================================
s = rep(s, "var BUILD = 'v6.4.11'", "var BUILD = 'v6.4.12'", 1, "版本：BUILD（看门狗块）")
s = rep(s, "    return 'v6.4.11';", "    return 'v6.4.12';", 1, "版本：报告兜底 RPT_BUILD")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.11 · 配置指南改为泛指，任选大模型。">v6.4.11</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.12 · 打开挑战模式自动随机一道选择题；页面启动超时放宽到 15 秒。">v6.4.12</div>',
        1, "版本：右下角角标（title + 文本）")
s = rep(s,
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.11</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>配置指南不再指定平台，任选模型。</p>\n'
        '      </div>',
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.12</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>挑战模式自动出题，启动超时15秒。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.11</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>配置指南不再指定平台，任选模型。</p>\n'
        '      </div>',
        1, "更新日志：插入 V6.4.12 首条")

# ============================================================
# 硬校验
# ============================================================
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
opens1 = len(re.findall(r"<script(?=[\s>/])", s))
assert closes1 == closes0, "[FAIL] 脚本收尾标签字面量数变了: %d -> %d" % (closes0, closes1)
assert opens1 == opens0, "[FAIL] 脚本开标签数变了: %d -> %d" % (opens0, opens1)
assert s.count("v6.4.11") == 0, "[FAIL] 小写 v6.4.11 残留: %d" % s.count("v6.4.11")
assert s.count("v6.4.12") == 3, "[FAIL] 小写 v6.4.12 应为 3 处，实际 %d" % s.count("v6.4.12")
assert s.count("V6.4.12") == 6, "[FAIL] 大写 V6.4.12 应为 6 处（4 注释 + 日志 + 角标 title），实际 %d" % s.count("V6.4.12")
assert s.count("V6.4.11") == V6411_BEFORE - 1, "[FAIL] V6.4.11 处数异常: %d -> %d" % (V6411_BEFORE, s.count("V6.4.11"))
# 10 秒残留必须清零（本项目里「10 秒」只属于启动看门狗）
assert s.count("10 秒") == 0, "[FAIL] 仍有 %d 处「10 秒」未改" % s.count("10 秒")
assert "10000);" not in s.split("window.__S3D_LENS__")[0].split("}(window);")[0] or True
assert s.count("15000);") == 1 and s.count("10000);") == 0, \
    "[FAIL] 看门狗毫秒数异常: 15000 x%d, 10000 x%d" % (s.count("15000);"), s.count("10000);"))
assert s.count("within 15 seconds") == 1 and "within 10 seconds" not in s, "[FAIL] en 文案异常"
# ① 的关键结构
assert s.count("judgeUserPicked") == 3, \
    "[FAIL] judgeUserPicked 应为 3 处（声明 + byUser 赋值 + 打开页判断），实际 %d" % s.count("judgeUserPicked")
assert s.count("selectProblem(p, true)") == 2, "[FAIL] byUser 入口应为 2 处（列表+知识地图）"
assert s.count("selectProblem(pool[Math.floor(Math.random() * pool.length)], true)") == 1, "[FAIL] gotoRandomPick 未打 byUser"
assert "function selectProblem(p, byUser){" in s, "[FAIL] selectProblem 签名未改"
# 更新日志字数
_log = re.search(r'<span class="log-ver">V6\.4\.12</span>.*?<p>(.*?)</p>', s, re.S)
assert _log, "[FAIL] 未能取到 V6.4.12 更新日志正文"
assert len(_log.group(1)) <= 20, "[FAIL] 更新日志 %d 字 > 20: %s" % (len(_log.group(1)), _log.group(1))
LOG.append("OK  %-56s %s" % ("更新日志字数", "%d 字：%s" % (len(_log.group(1)), _log.group(1))))

# ---- DOM 嵌套体检（硬门）----
import importlib.util
_spec = importlib.util.spec_from_file_location("v649s", os.path.join(BASE, "v649_structure.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_t = _mod.Tree()
_t.feed(s[:s.find('window.__S3D_LENS__')])
_bad = [(p, par) for p, par in _t.section_parents if par != ".wrap"]
assert len(_t.section_parents) == 12, "[FAIL] .panel 数量应为 12，实际 %d" % len(_t.section_parents)
assert not _bad, "[FAIL] 有面板掉出 .wrap：%s" % _bad
assert not _t.errors, "[FAIL] 未匹配收尾标签：%s" % _t.errors[:5]
LOG.append("OK  %-56s %s" % ("DOM 嵌套体检", "12 个面板父级均为 .wrap；未匹配收尾标签 0 个"))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 66)
print("脚本标签：opens %d -> %d, closes %d -> %d" % (opens0, opens1, closes0, closes1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
