# -*- coding: utf-8 -*-
"""V6.4.19 -> V6.4.21
需求：诊断里的「20 秒超时 → 掉本地知识库兜底」延长到 45 秒；问 AI 走同一条链路，一并生效。
      （用户指定版本号 6.4.21，上一版为 6.4.19）
落点：唯一一处超时数字（callLLM 里的 fetchWithRetry 调用）+ 用户可见的超时提示文案 +
      版本号四处同步。抽成常量 AI_TIMEOUT_MS，以后调一处即可。
"""
import re, os, subprocess

SRC = "光学交互实验室_AI_v6.4.19.html"
DST = "光学交互实验室_AI_v6.4.21.html"
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
CLOSES0 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS0 = len(re.findall(r"<script", s))

# --------------------------------------------- R1 抽出常量 + 放宽默认超时 + 注释更新
old_r1 = (
    "  /* V6.4.17：fetch 包装层——20s 超时 + 失败 1 次自动重试\n"
    "     设计要点：\n"
    "     ① 用 AbortController 实现硬超时（避免浏览器默认 ~5min 挂死）\n"
    "     ② 重试策略：超时 / 网络层失败 / 5xx 重试；4xx 不重试（key 错误重试无意义）\n"
    "     ③ 重试时重新创建 controller——已 abort 的 controller 不能复用\n"
    "     ④ 仅用于本应用直连 API（baseUrl 已在调用方校验过），不影响全站其它 fetch\n"
    "     ⑤ 上抛错误时附带「已重试」标记，方便上层区分显示文案 */\n"
    "  async function fetchWithRetry(url, opts, timeoutMs, retries){\n"
    "    timeoutMs = timeoutMs || 20000;\n"
)
new_r1 = (
    "  /* V6.4.21：单次请求的硬超时统一由这里给出 —— 由 V6.4.17 的 20s 放宽到 45s。\n"
    "     起因：勾了「深度思考模式」的模型（glm-4.7 / MiniMax-M3 / Claude 等）思考链一长就撞 20s 线，\n"
    "     「诊断」和「问 AI」会静默掉进本地知识库兜底 —— 用户只看到「AI 没回答」，猜不到其实是本地兜底。\n"
    "     ⚠️ 本值只作用于「单次尝试」：外面还套着失败重试 1 次（见 fetchWithRetry 的 retries），\n"
    "        所以真正最坏要等 45s × 2 = 90s 才会掉到本地兜底。若要压总时长，得改重试策略而不是改这里。 */\n"
    "  const AI_TIMEOUT_MS = 45000;\n"
    "\n"
    "  /* V6.4.17：fetch 包装层——硬超时 + 失败 1 次自动重试\n"
    "     设计要点：\n"
    "     ① 用 AbortController 实现硬超时（避免浏览器默认 ~5min 挂死）\n"
    "     ② 重试策略：超时 / 网络层失败 / 5xx 重试；4xx 不重试（key 错误重试无意义）\n"
    "     ③ 重试时重新创建 controller——已 abort 的 controller 不能复用\n"
    "     ④ 仅用于本应用直连 API（baseUrl 已在调用方校验过），不影响全站其它 fetch\n"
    "     ⑤ 上抛错误时附带「已重试」标记，方便上层区分显示文案\n"
    "     ⑥ 单次时长由 AI_TIMEOUT_MS 统一给出（V6.4.21 起） */\n"
    "  async function fetchWithRetry(url, opts, timeoutMs, retries){\n"
    "    timeoutMs = timeoutMs || AI_TIMEOUT_MS;\n"
)
s = rep(s, old_r1, new_r1, label="R1 AI_TIMEOUT_MS 常量 + 默认值")

# ------------------------------------------------- R2 4xx 不重试注释里的 20s 字样
s = rep(s,
        "        // 4xx 不重试：key 错误 / 配额超限 / 端点不存在，重试浪费 20s",
        "        // 4xx 不重试：key 错误 / 配额超限 / 端点不存在，重试白等一个超时周期",
        label="R2 4xx 注释去 20s")

# ------------------------------------------- R3 callLLM 调用点：唯一一处超时实参
old_r3 = (
    "    // V6.4.17：20s 超时 + 失败 1 次自动重试\n"
    "    let res;\n"
    "    try{\n"
    "      res = await fetchWithRetry(p.baseUrl+p.chatPath, {method:'POST', headers:p.h(cfg.apikey), body}, 20000, 1);\n"
    "    }catch(e){\n"
    "      // 上抛文案：超时给单独说明（用户最常见的\"等了 20s 还在转圈\"）\n"
)
new_r3 = (
    "    // V6.4.21：45s 超时 + 失败 1 次自动重试（原 20s，取值见 AI_TIMEOUT_MS 注释）\n"
    "    let res;\n"
    "    try{\n"
    "      res = await fetchWithRetry(p.baseUrl+p.chatPath, {method:'POST', headers:p.h(cfg.apikey), body}, AI_TIMEOUT_MS, 1);\n"
    "    }catch(e){\n"
    "      // 上抛文案：超时给单独说明（用户最常见的\"等了很久还在转圈\"）\n"
)
s = rep(s, old_r3, new_r3, label="R3 callLLM 超时实参 -> AI_TIMEOUT_MS")

# --------------------------------------------------------- R4 用户可见的超时提示文案
s = rep(s,
        "        throw new Error('请求超时（20 秒未响应），已自动重试 1 次仍失败。请检查网络或稍后再试');",
        "        throw new Error('请求超时（45 秒未响应），已自动重试 1 次仍失败。请检查网络或稍后再试');",
        label="R4 超时提示文案 20 -> 45 秒")

# -------------------------------------------------------------- R5 版本号四处同步
s = rep(s,
        "  var BUILD = 'v6.4.19', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        "  var BUILD = 'v6.4.21', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        label="R5 BUILD 常量")

s = rep(s, "    return 'v6.4.19';", "    return 'v6.4.21';", label="R6 RPT_BUILD 兜底")

s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.19 · AI 设置里智谱 Provider 下新增端点切换按钮：GLM Coding Plan 套餐端点 / 按量计费通用端点，一键填写 Base URL 并高亮当前端点。">v6.4.19</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.21 · AI 请求单次超时由 20 秒放宽到 45 秒：勾了深度思考的模型思考久也不再过早掉进本地知识库兜底（诊断 / 问 AI 同一条链路）。">v6.4.21</div>',
        label="R7 角标文本+title")

old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.19</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>智谱新增套餐/按量端点一键切换。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.21</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>AI 超时 20 秒放宽到 45 秒。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.19</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>智谱新增套餐/按量端点一键切换。</p>\n'
           '      </div>')
s = rep(s, old_log, new_log, label="R8 更新日志新增 V6.4.21")

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 64)

# 断言：callLLM 链路上不应再残留裸 20000
assert s.count("AI_TIMEOUT_MS") == 5, "[FAIL] AI_TIMEOUT_MS 出现次数 %d != 5" % s.count("AI_TIMEOUT_MS")
print("OK  AI_TIMEOUT_MS 出现 5 处（声明 / 默认值 / 调用实参 / 2 处注释引用）")
seg = s[s.find("async function callLLM"):s.find("async function callLLM") + 4200]
assert "20000" not in seg, "[FAIL] callLLM 链路仍有裸 20000"
print("OK  callLLM 链路已无裸 20000")
# line 10114 的判卷链路本轮不动，明确记录
assert s.count("}, 20000, 1);") == 1, "[FAIL] 判卷链路 20000 处数异常 %d" % s.count("}, 20000, 1);")
print("OK  判卷链路仍为 20000（本轮刻意未动，见工作记录）")

CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script", s))
assert (CLOSES1, OPENS1) == (CLOSES0, OPENS0), "[FAIL] 脚本标签计数变化 %s -> %s" % ((CLOSES0, OPENS0), (CLOSES1, OPENS1))
print("OK  脚本标签计数不变 closes=%d opens=%d" % (CLOSES1, OPENS1))

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk6421", exist_ok=True)
nchk = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk6421", "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
    nchk += 1
print("OK  JS 语法自检通过 %d 块" % nchk)

print("-" * 64)
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
