# -*- coding: utf-8 -*-
"""V6.4.23 -> V6.4.24

需求：用户确认「要的」—— 把 AI 判卷链路（callVisionModel）里两处硬编码
      `max_tokens: 2000` 也纳入 V6.4.23 的「按 Provider 分档」。

关键差异：**判卷读的是另一份配置**。主链路用 cfg.provider（顶部「⚙ AI 设置」），
         判卷用 getJudgeCfg().provider（「⚖ 判卷模型设置」），两者常常不是同一家。
         所以分档函数必须支持显式传入 Provider，不能写死 cfg.provider。

改法：
  · aiMaxTokens(thinkOn) → aiMaxTokens(thinkOn, provider)，provider 省略时回落 cfg.provider；
  · callVisionModel 的 anthropic / openai 两分支的 max_tokens: 2000 → aiMaxTokens(true, jc.provider)。
    判卷要吐「评分 JSON + 变式题」，2000 确实紧，故走"大额度档"（true）；
    额度只是上限，判卷对 zhipu/minimax/kimi 依旧显式关思考，给大不会改变结果。
"""
import re, os, subprocess

SRC = "光学交互实验室_AI_v6.4.23.html"
DST = "光学交互实验室_AI_v6.4.24.html"
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

# 前置：判卷两处目标串必须各 1 处，且总 2000 恰好 2 处
assert s.count("max_tokens: 2000") == 2, "[FAIL] 源文件 max_tokens:2000 应为 2 处，实际 %d" % s.count("max_tokens: 2000")

# ------------------------------------------------ R1 分档函数支持显式 Provider
s = rep(s,
        "  function aiMaxTokens(thinkOn){\n"
        "    if(!thinkOn) return AI_MAX_TOKENS_PLAIN;\n"
        "    return AI_MAX_TOKENS_BY_PROVIDER[cfg.provider] || AI_MAX_TOKENS_THINK;\n"
        "  }\n",
        "  /* V6.4.24：第二个参数支持显式传入 Provider。\n"
        "     原因：判卷链路（callVisionModel）读的是「判卷模型设置」里的 Provider（getJudgeCfg()），\n"
        "     与主链路的 cfg.provider 常常不是同一家，写死 cfg.provider 会取错档位。\n"
        "     省略时仍回落 cfg.provider，主链路（问 AI / 诊断）调用方式不变。 */\n"
        "  function aiMaxTokens(thinkOn, provider){\n"
        "    if(!thinkOn) return AI_MAX_TOKENS_PLAIN;\n"
        "    return AI_MAX_TOKENS_BY_PROVIDER[provider || cfg.provider] || AI_MAX_TOKENS_THINK;\n"
        "  }\n"
        "  /* V6.4.24：🔥 必须挂到 window —— 判卷模块位于**另一个 script 块的 IIFE**\n"
        "     中（callVisionModel 属「挑战模式」模块，见文件后段），看不到本作用域的函数。\n"
        "     跨块共享一律走 window，与既有的 window.AiLoading 同一套约定。\n"
        "     fetchWithRetry 同理：判卷侧的 `fetchWithRetry(...)` 正是因为它不可见而抛\n"
        "     ReferenceError（V6.4.17 引入、直到 V6.4.24 才被 e2e 抓出），故一并挂出去。\n"
        "     （注：注释里刻意不写尖括号 script 字样 —— 内联脚本中它会污染标签计数，\n"
        "       且可能触发 HTML 的 script-data-escaped 状态。） */\n"
        "  try { window.aiMaxTokens = aiMaxTokens; window.fetchWithRetry = fetchWithRetry; } catch(e) {}\n",
        label="R1 aiMaxTokens 增加 provider 形参 + 挂 window 共享")

# ------------------------------------------------ R2 常量区注释补一句（判卷已接入）
s = rep(s,
        "     问 AI（runChat）与诊断（runDiag）走的是同一个 callLLM，因此分档对两者同时生效。 */",
        "     问 AI（runChat）与诊断（runDiag）走的是同一个 callLLM，因此分档对两者同时生效。\n"
        "     V6.4.24 起**判卷链路也接入** —— 它按「判卷模型设置」里那家 Provider 取档，不是主 Provider。 */",
        label="R2 常量区注释补充判卷说明")

# ------------------------------------------------ R3 判卷模块：新增取额度的小助手
s = rep(s,
        "/* V4.4：多模态判卷调用——截图 base64 随 prompt 发给视觉模型 */\n"
        "async function callVisionModel(prompt, dataUrl, temperature){\n",
        "/* V6.4.24：判卷的输出额度取分档值。\n"
        "   分档函数定义在「AI 模块」的另一个 IIFE 里，本模块看不到，只能走 window 共享。\n"
        "   万一取不到也回落通用档 8000 —— 绝不让判卷因为额度取不到而整条挂掉。 */\n"
        "function judgeMaxTokens(provider){\n"
        "  try{\n"
        "    if(typeof window.aiMaxTokens === 'function') return window.aiMaxTokens(true, provider);\n"
        "  }catch(e){}\n"
        "  return 8000;\n"
        "}\n"
        "\n"
        "/* V4.4：多模态判卷调用——截图 base64 随 prompt 发给视觉模型 */\n"
        "async function callVisionModel(prompt, dataUrl, temperature){\n",
        label="R3 判卷模块新增 judgeMaxTokens() 助手")

# ------------------------------------------------ R4 判卷 · Anthropic 分支
s = rep(s,
        "    headers = { 'x-api-key': jc.apikey, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' };\n"
        "    body = JSON.stringify({\n"
        "      model, max_tokens: 2000, system: sysMsg, temperature: temperature,\n",
        "    headers = { 'x-api-key': jc.apikey, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' };\n"
        "    // V6.4.24：判卷要吐「评分 JSON + 变式题」，原来硬编码 2000 偏紧 —— 改走大额度档，\n"
        "    //           并按**判卷自己的** Provider 取分档值（判卷 Provider ≠ 主 Provider）。\n"
        "    body = JSON.stringify({\n"
        "      model, max_tokens: judgeMaxTokens(jc.provider), system: sysMsg, temperature: temperature,\n",
        label="R4 判卷 Anthropic 分支 2000 → 分档")

# ------------------------------------------------ R5 判卷 · OpenAI 兼容分支
s = rep(s,
        "    const obj = {\n"
        "      model, temperature: temperature, max_tokens: 2000,\n",
        "    const obj = {\n"
        "      // V6.4.24：同上——判卷额度改按判卷 Provider 分档（原来是硬编码 2000）\n"
        "      model, temperature: temperature, max_tokens: judgeMaxTokens(jc.provider),\n",
        label="R5 判卷 OpenAI 分支 2000 → 分档")

# ------------------------------------------------ R5b 判卷请求：修 V6.4.17 起的跨块 ReferenceError
s = rep(s,
        "  // V6.4.17：20s 超时 + 失败 1 次自动重试（判卷模型截图较大，超时比 chat 更常见）\n"
        "  let res;\n"
        "  try{\n"
        "    res = await fetchWithRetry(baseUrl + d.chatPath, { method: 'POST', headers, body }, 20000, 1);\n",
        "  // V6.4.17：20s 超时 + 失败 1 次自动重试（判卷模型截图较大，超时比 chat 更常见）\n"
        "  // V6.4.24 🔥 修历史 bug：fetchWithRetry 定义在「AI 模块」的另一个 IIFE 里，\n"
        "  //   本模块看不到它 —— 自 V6.4.17 把这里从原生 fetch 改成 fetchWithRetry 起，\n"
        "  //   判卷每次都在这一行抛 ReferenceError，整条链路不可用（6.4.17→6.4.23 共 7 版）。\n"
        "  //   现改走 window 共享版本；万一缺失退化为原生 fetch（少一层重试，但不至于全挂）。\n"
        "  const _fetchR = (typeof window.fetchWithRetry === 'function')\n"
        "    ? window.fetchWithRetry\n"
        "    : function(u, o){ return fetch(u, o); };\n"
        "  let res;\n"
        "  try{\n"
        "    res = await _fetchR(baseUrl + d.chatPath, { method: 'POST', headers, body }, 20000, 1);\n",
        label="R5b 判卷请求改走 window.fetchWithRetry（修 V6.4.17 跨块 ReferenceError）")

# ------------------------------------------------ R6~R9 版本号四处
s = rep(s,
        "  var BUILD = 'v6.4.23', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        "  var BUILD = 'v6.4.24', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        label="R6 BUILD 常量")
s = rep(s, "    return 'v6.4.23';", "    return 'v6.4.24';", label="R7 RPT_BUILD 兜底")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.23 · AI 输出额度改为按 Provider 分档：智谱（官方上限 131072）由 8000 放大到 32000，DeepSeek 等仍守 8000 通用档以免超限；问 AI 与诊断共用同一条链路，同时生效。">v6.4.23</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.24 · ① 修复 AI 判卷自 V6.4.17 起整条失效（跨脚本块引用 fetchWithRetry 抛 ReferenceError）；② 判卷输出额度由硬编码 2000 改为按「判卷模型设置」里的 Provider 分档：智谱 32000、其余 8000。">v6.4.24</div>',
        label="R8 角标文本+title")

old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.23</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>输出额度按厂商分档，智谱放大到32K。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.24</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>修复判卷链路失效，额度按厂商分档。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.23</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>输出额度按厂商分档，智谱放大到32K。</p>\n'
           '      </div>')
s = rep(s, old_log, new_log, label="R9 更新日志新增 V6.4.24")

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("-" * 68)

# ---------------------------------------------------------------- 一致性断言
assert s.count("max_tokens: 2000") == 0, "[FAIL] 仍有硬编码 2000：%d 处" % s.count("max_tokens: 2000")
print("OK  硬编码 max_tokens:2000 已清零")
assert s.count("max_tokens: judgeMaxTokens(jc.provider)") == 2, "[FAIL] 判卷分档调用 %d 处" % s.count("max_tokens: judgeMaxTokens(jc.provider)")
print("OK  判卷两分支均按 jc.provider 分档")
assert s.count("function judgeMaxTokens(provider){") == 1
assert s.count("window.aiMaxTokens(true, provider)") == 1
print("OK  judgeMaxTokens() 助手已就位并读取 window 共享函数")
assert s.count("window.aiMaxTokens = aiMaxTokens;") == 1
print("OK  🔥 aiMaxTokens 已挂 window（跨 script 块共享的必需一步）")
assert s.count("window.fetchWithRetry = fetchWithRetry;") == 1
print("OK  🔥 fetchWithRetry 已挂 window（修 V6.4.17 起的判卷致命 bug）")
assert s.count("await fetchWithRetry(baseUrl") == 0
print("OK  判卷侧对 fetchWithRetry 的裸引用已清零")
assert s.count("_fetchR(baseUrl + d.chatPath") == 1 and s.count("const _fetchR =") == 1
print("OK  判卷请求改走 window 共享版本（带原生 fetch 回落）")
assert s.count("AI_MAX_TOKENS_BY_PROVIDER[provider || cfg.provider]") == 1
print("OK  分档查找已支持显式 provider")
assert s.count("v6.4.24") == 3 and "V6.4.24" in s
print("OK  版本号：小写 v6.4.24 x3 + 大写 V6.4.24（title/日志）")

# 跨块可用性：两个函数必须在不同的 script 块里（这正是必须挂 window 的原因）
import re
for _kw in ("window.aiMaxTokens = aiMaxTokens;", "window.aiMaxTokens(true, provider)"):
    assert _kw in s
print("OK  跨块共享自检：判卷侧只经 window 调用，不再直接引用块内标识符")

CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script", s))
assert (CLOSES1, OPENS1) == (CLOSES0, OPENS0), "[FAIL] 脚本标签计数变化"
print("OK  脚本标签计数不变 closes=%d opens=%d" % (CLOSES1, OPENS1))

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk6424", exist_ok=True)
nchk = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk6424", "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
    nchk += 1
print("OK  JS 语法自检通过 %d 块" % nchk)

print("-" * 68)
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
