# -*- coding: utf-8 -*-
"""V6.4.21 -> V6.4.22
Bug 1（根因）：深度思考模式下 max_tokens 只给 2000，而智谱 GLM-5.3 / 5.3-Flash 是「强制思考」模型，
              思考（reasoning_content）与正文（content）共享该额度 → 思考吃光 2000，
              正文为 ''、finish_reason='length'（用户实测 reasoning_tokens=1984 / completion_tokens=2000）。
              官方文档：glm-5.3-flash 默认 max_tokens 65536、上限 131072 —— 是我们给得太小。
              强制思考模型 sending thinking=disabled 无效，所以唯一正确修法是加额度。
Bug 2（症状放大器）：raw 为空时旧代码走 `return raw || JSON.stringify(data)`，
              把整包响应（含英文思考过程）当正文渲染到学情面板上，学生看到一大坨 JSON。
              改成抛出明确错误 → 上层 catch 走「⚠️ 说明 + 本地知识库兜底」。
"""
import re, os, subprocess

SRC = "光学交互实验室_AI_v6.4.21.html"
DST = "光学交互实验室_AI_v6.4.22.html"
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-56s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
CLOSES0 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS0 = len(re.findall(r"<script", s))

# ------------------------------------------- R1 输出额度常量（根因修复）
old_r1 = (
    "  const AI_TIMEOUT_MS = 45000;\n"
    "\n"
    "  /* V6.4.17：fetch 包装层——硬超时 + 失败 1 次自动重试\n"
)
new_r1 = (
    "  const AI_TIMEOUT_MS = 45000;\n"
    "\n"
    "  /* V6.4.22：输出额度。V6.4.15 起「深度思考模式」默认开启，而智谱 GLM-5.3 / 5.3-Flash\n"
    "     以及 GLM-4.7 是**强制思考**模型（官方文档：传 thinking=disabled 也关不掉），\n"
    "     思考写在 message.reasoning_content，且与正文 content **共享 max_tokens**。\n"
    "     原来只给 2000 —— 实测一次诊断的思考就吃掉 1984，正文一个字没轮到，\n"
    "     接口返回 200 + finish_reason='length' + content=''。\n"
    "     官方额度（docs.bigmodel.cn 核心参数）：glm-5.3-flash 默认 65536、上限 131072，\n"
    "     即「默认值本来就够，是我们主动限小了」。这里给到 8000：\n"
    "       · 思考 + 正文都够用；\n"
    "       · 同时不超过其它 Provider 的输出上限（DeepSeek 8K 是最紧的一档，8000 仍在其内），\n"
    "         所以一套值可以安全地套用到所有 OpenAI 协议厂商。 */\n"
    "  const AI_MAX_TOKENS_THINK = 8000;\n"
    "  const AI_MAX_TOKENS_PLAIN = 800;\n"
    "\n"
    "  /* V6.4.17：fetch 包装层——硬超时 + 失败 1 次自动重试\n"
)
s = rep(s, old_r1, new_r1, label="R1 新增 AI_MAX_TOKENS_* 常量")

# ------------------------------------------------- R2 OpenAI 协议分支 max_tokens
s = rep(s,
        "      const oaObj = { model:p.model, messages:[{role:'system', content:sysMsg},{role:'user', content:prompt}], temperature:0.5, max_tokens:THINK_ON?2000:800 };",
        "      const oaObj = { model:p.model, messages:[{role:'system', content:sysMsg},{role:'user', content:prompt}], temperature:0.5, max_tokens:THINK_ON?AI_MAX_TOKENS_THINK:AI_MAX_TOKENS_PLAIN };",
        label="R2 OpenAI 分支 max_tokens 提到常量")

# --------------------------------------------- R3 Anthropic 分支 max_tokens（同类隐患）
s = rep(s,
        "      const anthObj = { model:p.model, max_tokens:THINK_ON?2048:1024, system:sysMsg, messages:[{role:'user', content:prompt}] };",
        "      const anthObj = { model:p.model, max_tokens:THINK_ON?AI_MAX_TOKENS_THINK:AI_MAX_TOKENS_PLAIN, system:sysMsg, messages:[{role:'user', content:prompt}] };",
        label="R3 Anthropic 分支 max_tokens 同步")

# ------------------------------------------------------------- R4 i18n 新增词条
old_r4 = "'err.needKey':    {zh:'请先在「AI 设置」中填 API Key', zht:'請先在「AI 設定」中填 API Key', en:'Set an API key in AI Settings first'},"
new_r4 = (old_r4 + "\n"
          "'err.thinkAte':  {zh:'模型把输出额度全花在「思考」上了，没轮到正文（finish_reason={0}；本次共 {1} tokens，其中思考 {2}）。可以换一个非思考模型再试；若模型本身是强制思考型，请把 max_tokens 调大。', zht:'模型把輸出額度全花在「思考」上了，沒輪到正文（finish_reason={0}；本次共 {1} tokens，其中思考 {2}）。可以換一個非思考模型再試；若模型本身是強制思考型，請把 max_tokens 調大。', en:'The model spent its whole output budget on reasoning and never produced an answer (finish_reason={0}; {1} tokens total, {2} of them reasoning). Try a non-reasoning model, or raise max_tokens if the model forces thinking.'},\n"
          "'err.emptyContent':{zh:'模型返回了空内容（finish_reason={0}，共 {1} tokens）。请稍后重试或换个模型。', zht:'模型回傳了空內容（finish_reason={0}，共 {1} tokens）。請稍後重試或換個模型。', en:'The model returned empty content (finish_reason={0}, {1} tokens). Retry later or switch models.'},\n"
          "'err.truncated':  {zh:'（此回答因输出长度上限被截断，后面可能还有内容）', zht:'（此回答因輸出長度上限被截斷，後面可能還有內容）', en:'(This answer was cut off by the output length limit.)'},")
s = rep(s, old_r4, new_r4, label="R4 i18n 新增 3 条错误词条")

# --------------------------------- R5 空正文不再糊 JSON（症状修复，核心）
old_r5 = (
    "    // v1.8：过滤可能的 <think>...</think> 思考块残留\n"
    "    raw = String(raw).replace(/<think>[\\s\\S]*?<\\/think>/gi, '').replace(/<\\|.*?\\|>/g, '').trim();\n"
    "    return raw || JSON.stringify(data);\n"
)
new_r5 = (
    "    // v1.8：过滤可能的 <think>...</think> 思考块残留\n"
    "    raw = String(raw).replace(/<think>[\\s\\S]*?<\\/think>/gi, '').replace(/<\\|.*?\\|>/g, '').trim();\n"
    "    /* V6.4.22：正文为空 / 被截断时的处理\n"
    "       —— 旧代码在 raw 为空时直接 `return JSON.stringify(整包)`：一旦模型没产出正文，\n"
    "          就把**整包 JSON**（含英文 reasoning_content、usage、request_id）当正文渲染，\n"
    "          学情面板/问 AI 面板上会出现一大坨 JSON，既看不懂也帮不到学生。\n"
    "       现在改成抛出可读错误：上层 catch 会渲染成「⚠️ 原因 + 本地知识库兜底」，\n"
    "       学生至少能看到该实验的核心考点，而不是一堆原始报文。 */\n"
    "    const fr = (p.fmt === 'anthropic') ? (data.stop_reason || '') : (data.choices?.[0]?.finish_reason || '');\n"
    "    const truncated = (fr === 'length' || fr === 'max_tokens');\n"
    "    if(!raw){\n"
    "      const u = data.usage || {};\n"
    "      const comp = u.completion_tokens || u.output_tokens || 0;\n"
    "      const think = (u.completion_tokens_details && u.completion_tokens_details.reasoning_tokens) || 0;\n"
    "      if(truncated && think > 0) throw new Error(fmt(T('err.thinkAte'), fr, comp, think));\n"
    "      throw new Error(fmt(T('err.emptyContent'), fr, comp));\n"
    "    }\n"
    "    if(truncated) raw += '\\n\\n' + T('err.truncated');\n"
    "    return raw;\n"
)
s = rep(s, old_r5, new_r5, label="R5 空正文改为明确报错（不再糊 JSON）")

# -------------------------------------------------------------- R6~R9 版本号四处
s = rep(s,
        "  var BUILD = 'v6.4.21', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        "  var BUILD = 'v6.4.22', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        label="R6 BUILD 常量")
s = rep(s, "    return 'v6.4.21';", "    return 'v6.4.22';", label="R7 RPT_BUILD 兜底")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.21 · AI 请求单次超时由 20 秒放宽到 45 秒：勾了深度思考的模型思考久也不再过早掉进本地知识库兜底（诊断 / 问 AI 同一条链路）。">v6.4.21</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.22 · 修复强制思考模型（GLM-5.3/4.7 等）把输出额度全花在思考上、正文为空时，学情面板会糊出一整包 JSON 的问题；深度思考的输出额度由 2000 提到 8000。">v6.4.22</div>',
        label="R8 角标文本+title")

old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.21</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>AI 超时 20 秒放宽到 45 秒。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.22</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>修思考占满输出额度致正文为空。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.21</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>AI 超时 20 秒放宽到 45 秒。</p>\n'
           '      </div>')
s = rep(s, old_log, new_log, label="R9 更新日志新增 V6.4.22")

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("-" * 68)

assert s.count("AI_MAX_TOKENS_THINK") == 3, "[FAIL] AI_MAX_TOKENS_THINK 次数 %d" % s.count("AI_MAX_TOKENS_THINK")
assert s.count("AI_MAX_TOKENS_PLAIN") == 3, "[FAIL] AI_MAX_TOKENS_PLAIN 次数 %d" % s.count("AI_MAX_TOKENS_PLAIN")
print("OK  额度常量引用：THINK x3 / PLAIN x3")
assert "max_tokens:THINK_ON?2000" not in s, "[FAIL] 旧 2000 仍在"
print("OK  旧 max_tokens:2000 已清零")
assert "JSON.stringify(data)" not in s, "[FAIL] 裸糊 JSON 的入口仍在"
print("OK  `return raw || JSON.stringify(data)` 已清零（全文件无 JSON.stringify(data)）")
assert s.count("'length'") >= 1 and "finish_reason" in s
print("OK  已引入 finish_reason 判定")

CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script", s))
assert (CLOSES1, OPENS1) == (CLOSES0, OPENS0), "[FAIL] 脚本标签计数变化"
print("OK  脚本标签计数不变 closes=%d opens=%d" % (CLOSES1, OPENS1))

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk6422", exist_ok=True)
nchk = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk6422", "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
    nchk += 1
print("OK  JS 语法自检通过 %d 块" % nchk)

print("-" * 68)
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
