# -*- coding: utf-8 -*-
"""V6.4.25 -> V6.4.26
主题：批作图题（AI 判卷）的「是否启用思考模式」改为跟随顶部「AI 设置」的深度思考模式。

改动：
 R1  getJudgeCfg() 增加 thinkMode（读主配置 ai_optics_v1_cfg.thinkMode）
 R2  callVisionModel() 的 thinking 逻辑与 callLLM 同构（anthropic 分支）
 R3  callVisionModel() 的 thinking 逻辑（OpenAI 兼容分支）
 R4  判卷超时由写死的 20s 改为跟随 window.AI_TIMEOUT_MS（180s）+ 超时文案
 R5  AI 模块把 AI_TIMEOUT_MS 一并挂到 window
 R6  判卷结果卡的 modelDisplay 标出当前思考模式
 R7  判卷模型设置弹窗加一句「思考模式跟随 AI 设置」的说明
 R8  版本号 BUILD / RPT_BUILD
 R9  右下角版本角标
 R10 更新日志新增 V6.4.26 条目
"""
import os
import re

SRC = "光学交互实验室_AI_v6.4.25.html"
DST = "光学交互实验室_AI_v6.4.26.html"
LOG = []
LINE_DELTA = [0]


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LINE_DELTA[0] += (new.count("\n") - old.count("\n")) * c
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
N_LF0 = s.count("\n")
# 浏览器口径的 script 元素计数（<script / </script 后跟 空白 / > ）
n_open0 = len(re.findall(r"<script", s))
n_close0 = len(re.findall(r"</script(?=[\s>/])", s))

# ---------------------------------------------------------------- R1
R1_OLD = """/* V4.4 判卷配置：独立于主 AI 设置（provider/model 可不同，key 留空复用主配置） */
function getJudgeCfg(){"""
R1_NEW = """/* V4.4 判卷配置：独立于主 AI 设置（provider/model 可不同，key 留空复用主配置）
   V6.4.26：另把主配置的「深度思考模式」（thinkMode）一并读出来 —— 判卷的思考模式跟随它，
            判卷自己不再单独一套（原来 V4.7 是把思考硬关掉的）。 */
function getJudgeCfg(){"""
s = rep(s, R1_OLD, R1_NEW, 1, "R1a getJudgeCfg 头注释")

R1B_OLD = """  return {
    provider: jc.provider || mainP,
    model: jc.model || '',
    apikey: jc.apikey || main.apikey || '',
    baseUrl: jc.baseUrl || ''
  };
}"""
R1B_NEW = """  return {
    provider: jc.provider || mainP,
    model: jc.model || '',
    apikey: jc.apikey || main.apikey || '',
    baseUrl: jc.baseUrl || '',
    /* V6.4.26：判卷的思考模式 = AI 设置里的「深度思考模式」（默认开）。
       只读一个布尔值，判卷设置弹窗里不再需要自己的开关。 */
    thinkMode: main.thinkMode !== false
  };
}"""
s = rep(s, R1B_OLD, R1B_NEW, 1, "R1b getJudgeCfg 返回值加 thinkMode")

# ---------------------------------------------------------------- R2
R2_OLD = """  let headers, body;
  // V4.7：noThink——GLM/M3 系列默认可能输出思考过程导致 JSON 解析失败，显式关闭
  const NO_THINK = ['zhipu', 'minimax', 'kimi'];"""
R2_NEW = """  let headers, body;
  /* V6.4.26：思考模式跟随顶部「⚙ AI 设置」的「深度思考模式」，与 callLLM 同一套语义。
     —— 判卷原来与主链路**不一致**：V4.7 起把思考**硬关**（NO_THINK 名单永远传 disabled），
        用户在主设置里勾了「深度思考模式」，判卷却仍然不思考；现在改为直接读 cfg.thinkMode。
      开：智谱显式 thinking=enabled；Anthropic 走官方扩展思考（temperature 必须为 1）；其余厂商不传，走各自默认。
      关：对支持的厂商（智谱 / MiniMax / Kimi / Anthropic）显式 thinking=disabled。
     ⚠️ 只有「要不要想」跟随开关，**输出额度不跟着退回 800 档** ——
        判卷要吐「评分 JSON + 错因归因 + 变式题」，额度太紧会把 JSON 截断，反而判不出来。 */
  const NO_THINK = ['zhipu', 'minimax', 'kimi'];
  const THINK_ON = jc.thinkMode !== false;"""
s = rep(s, R2_OLD, R2_NEW, 1, "R2a 判卷 THINK_ON 定义")

R2B_OLD = """    body = JSON.stringify({
      model, max_tokens: judgeMaxTokens(jc.provider), system: sysMsg, temperature: temperature,
      messages: [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: 'image/png', data: dataUrl.split(',')[1] } },
        { type: 'text', text: prompt }
      ]}]
    });"""
R2B_NEW = """    const anthObj = {
      model, max_tokens: judgeMaxTokens(jc.provider), system: sysMsg,
      // V6.4.26：Anthropic 官方要求 —— 开启扩展思考时 temperature 必须为 1
      temperature: THINK_ON ? 1 : temperature,
      messages: [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: 'image/png', data: dataUrl.split(',')[1] } },
        { type: 'text', text: prompt }
      ]}]
    };
    anthObj.thinking = THINK_ON ? { type: 'enabled', budget_tokens: 1024 } : { type: 'disabled' };
    body = JSON.stringify(anthObj);"""
s = rep(s, R2B_OLD, R2B_NEW, 1, "R2b anthropic 分支 thinking")

# ---------------------------------------------------------------- R3
R3_OLD = """    if (NO_THINK.indexOf(jc.provider) >= 0) obj.thinking = { type: 'disabled' };   // V4.7"""
R3_NEW = """    // V6.4.26：与 callLLM 同构 —— 勾了深度思考则智谱显式 enabled；未勾则按 noThink 名单显式 disabled
    if (THINK_ON) { if (jc.provider === 'zhipu') obj.thinking = { type: 'enabled' }; }
    else if (NO_THINK.indexOf(jc.provider) >= 0) obj.thinking = { type: 'disabled' };"""
s = rep(s, R3_OLD, R3_NEW, 1, "R3 OpenAI 兼容分支 thinking")

# ---------------------------------------------------------------- R4
R4_OLD = """  // V6.4.17：20s 超时 + 失败 1 次自动重试（判卷模型截图较大，超时比 chat 更常见）
  // V6.4.24 🔥 修历史 bug：fetchWithRetry 定义在「AI 模块」的另一个 IIFE 里，
  //   本模块看不到它 —— 自 V6.4.17 把这里从原生 fetch 改成 fetchWithRetry 起，
  //   判卷每次都在这一行抛 ReferenceError，整条链路不可用（6.4.17→6.4.23 共 7 版）。
  //   现改走 window 共享版本；万一缺失退化为原生 fetch（少一层重试，但不至于全挂）。
  const _fetchR = (typeof window.fetchWithRetry === 'function')
    ? window.fetchWithRetry
    : function(u, o){ return fetch(u, o); };
  let res;
  try{
    res = await _fetchR(baseUrl + d.chatPath, { method: 'POST', headers, body }, 20000, 1);
  }catch(e){
    const msg = String((e && (e.message || e)) || '');
    if(/abort|timeout/i.test(msg) || (e && e.name === 'AbortError')){
      throw new Error('判卷请求超时（20 秒未响应），已自动重试 1 次仍失败。请检查网络或稍后再试');
    }"""
R4_NEW = """  // V6.4.17：超时 + 失败 1 次自动重试（判卷模型截图较大，超时比 chat 更常见）
  // V6.4.24 🔥 修历史 bug：fetchWithRetry 定义在「AI 模块」的另一个 IIFE 里，
  //   本模块看不到它 —— 自 V6.4.17 把这里从原生 fetch 改成 fetchWithRetry 起，
  //   判卷每次都在这一行抛 ReferenceError，整条链路不可用（6.4.17→6.4.23 共 7 版）。
  //   现改走 window 共享版本；万一缺失退化为原生 fetch（少一层重试，但不至于全挂）。
  // V6.4.26 🔥 超时从写死的 20s 改为跟随主链路的 window.AI_TIMEOUT_MS（180s）。
  //   起因：判卷默认视觉模型 GLM-5.3-Flash 实测**关思考也要 27.2s**、开思考 86.4s（见 V6.4.24/V6.4.25 实测），
  //   20s 线必然掐断 —— 那样「思考模式跟随 AI 设置」这个开关根本没有生效空间。
  //   取不到 window 值则回落 180000；配合 V6.4.25 的「超时不重试」，总等待上限仍是一次 180s。
  const _to = (typeof window.AI_TIMEOUT_MS === 'number' && window.AI_TIMEOUT_MS > 0)
    ? window.AI_TIMEOUT_MS : 180000;
  const _fetchR = (typeof window.fetchWithRetry === 'function')
    ? window.fetchWithRetry
    : function(u, o){ return fetch(u, o); };
  let res;
  try{
    res = await _fetchR(baseUrl + d.chatPath, { method: 'POST', headers, body }, _to, 1);
  }catch(e){
    const msg = String((e && (e.message || e)) || '');
    if(/abort|timeout/i.test(msg) || (e && e.name === 'AbortError')){
      throw new Error('判卷请求超时（' + Math.round(_to / 1000) + ' 秒未响应）。该模型思考耗时较长，可稍后重试；若持续超时请改用更快的模型，或关掉「深度思考模式」');
    }"""
s = rep(s, R4_OLD, R4_NEW, 1, "R4 判卷超时跟随主链路 + 文案")

# ---------------------------------------------------------------- R5
R5_OLD = """  try { window.aiMaxTokens = aiMaxTokens; window.fetchWithRetry = fetchWithRetry; } catch(e) {}"""
R5_NEW = """  // V6.4.26：AI_TIMEOUT_MS 也一并挂出去 —— 判卷侧要读它做超时（原来判卷写死 20s）
  try { window.aiMaxTokens = aiMaxTokens; window.fetchWithRetry = fetchWithRetry; window.AI_TIMEOUT_MS = AI_TIMEOUT_MS; } catch(e) {}"""
s = rep(s, R5_OLD, R5_NEW, 1, "R5 AI_TIMEOUT_MS 挂到 window")

# ---------------------------------------------------------------- R6
R6_OLD = """  best.modelDisplay = jc.provider + ' · ' + (jc.model || '(默认视觉模型)');"""
R6_NEW = """  // V6.4.26：把当前思考模式标出来，方便一眼核对「判卷确实跟随了 AI 设置」
  best.modelDisplay = jc.provider + ' · ' + (jc.model || '(默认视觉模型)') + (jc.thinkMode !== false ? ' · 🧠 深度思考' : ' · ⚡ 已关思考');"""
s = rep(s, R6_OLD, R6_NEW, 1, "R6 判卷结果卡标出思考模式")

# ---------------------------------------------------------------- R7
R7_OLD = """    <p style="margin:6px 0;font-size:12px;color:var(--muted2);line-height:1.6">判卷使用<b>多模态（看图）模型</b>对学生的手绘截图评分。推荐：智谱 GLM-5.3-Flash、MiniMax-M3、Kimi 视觉版。API Key 留空则复用顶部「⚙ AI 设置」的 Key。</p>"""
R7_NEW = R7_OLD + """
    <p style="margin:6px 0;font-size:12px;color:var(--muted2);line-height:1.6">🧠 <b>思考模式与顶部「⚙ AI 设置」的「深度思考模式」保持一致</b>，这里不单独设置：关掉它判卷更快（实测 GLM-5.3-Flash 由 86 秒降到 27 秒），打开则评分更细致。判卷超时同样与主链路一致（180 秒）。</p>"""
s = rep(s, R7_OLD, R7_NEW, 1, "R7 判卷设置弹窗加说明")

# ---------------------------------------------------------------- R8
s = rep(s, "  var BUILD = 'v6.4.25'", "  var BUILD = 'v6.4.26'", 1, "R8a var BUILD")
s = rep(s, "    return 'v6.4.25';", "    return 'v6.4.26';", 1, "R8b RPT_BUILD 兜底")

# ---------------------------------------------------------------- R9
R9_OLD = """<div class="ver-badge" title="光学交互实验室 V6.4.25 · ① 单次请求超时 45 秒放宽到 180 秒（实测智谱 GLM-5.3-Flash 单次需 86.4 秒，慢在思考输出侧）；② 超时不再触发重试，避免白等第二轮；③ 诊断等待提示改为「可能需要 1-2 分钟」。">v6.4.25</div>"""
R9_NEW = """<div class="ver-badge" title="光学交互实验室 V6.4.26 · ① 批作图题（AI 判卷）的「思考模式」改为跟随顶部 AI 设置的「深度思考模式」，不再自己硬关；② 判卷超时由写死的 20 秒改为与主链路一致的 180 秒（实测判卷默认模型关思考也要 27.2 秒，20 秒必然掐断）；③ 判卷设置弹窗与结果卡都标出当前思考模式。">v6.4.26</div>"""
s = rep(s, R9_OLD, R9_NEW, 1, "R9 ver-badge")

# ---------------------------------------------------------------- R10
R10_OLD = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.25</span><span class="log-date">2026-09-21</span></div>
        <p>AI 超时 45 秒放宽到 180 秒（实测智谱 GLM-5.3-Flash 单次需 86 秒），超时不再重试。</p>
      </div>"""
R10_NEW = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.26</span><span class="log-date">2026-09-21</span></div>
        <p>判卷（批作图题）的思考模式改为跟随 AI 设置，判卷超时与主链路统一为 180 秒。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.25</span><span class="log-date">2026-09-21</span></div>
        <p>AI 超时 45 秒放宽到 180 秒（实测智谱 GLM-5.3-Flash 单次需 86 秒），超时不再重试。</p>
      </div>"""
s = rep(s, R10_OLD, R10_NEW, 1, "R10 更新日志")

# ---------------------------------------------------------------- 收尾断言
n_open1 = len(re.findall(r"<script", s))
n_close1 = len(re.findall(r"</script(?=[\s>/])", s))
assert n_open1 == n_open0, "[FAIL] script 开标签计数变了: %d -> %d" % (n_open0, n_open1)
assert n_close1 == n_close0, "[FAIL] script 收尾标签计数变了: %d -> %d" % (n_close0, n_close1)
assert s.count("\n") == N_LF0 + LINE_DELTA[0], \
    "[FAIL] 行数变化异常: %d -> %d（期望 %+d）" % (N_LF0, s.count("\n"), LINE_DELTA[0])
assert "20000, 1)" not in s, "[FAIL] 判卷旧超时值仍在"
assert "判卷请求超时（20 秒未响应）" not in s, "[FAIL] 判卷旧超时文案仍在"
assert "' · 🧠 深度思考'" in s and "' · ⚡ 已关思考'" in s, "[FAIL] 结果卡标记未落地"
assert "const THINK_ON = jc.thinkMode !== false;" in s, "[FAIL] 判卷 THINK_ON 未落地"
assert "window.AI_TIMEOUT_MS = AI_TIMEOUT_MS;" in s, "[FAIL] AI_TIMEOUT_MS 未挂 window"
# 主链路那套（callLLM 的 THINK_ON）必须逐字未动
assert s.count("const THINK_ON = cfg.thinkMode !== false;") == 1, "[FAIL] 主链路 THINK_ON 被误改"
assert s.count("const NO_THINK = ['zhipu', 'minimax', 'kimi'];") == 1, "[FAIL] NO_THINK 名单数异常"
assert "const AI_TIMEOUT_MS = 180000;" in s, "[FAIL] 主链路超时常量被误改"

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("---")
print("script 元素: opens %d->%d  closes %d->%d" % (n_open0, n_open1, n_close0, n_close1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
