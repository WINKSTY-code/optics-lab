# -*- coding: utf-8 -*-
"""V6.4.22 -> V6.4.23

需求：用户问「问 AI 那个里面有最大 token 量限制吗？如果有的话也把它放大一点。」

调查结论：
  · 问 AI **没有独立限制** —— 它和「诊断」共用同一个 callLLM（runChat / runDiag 都调它），
    V6.4.22 已经把那里的 max_tokens 提到 AI_MAX_TOKENS_THINK=8000，问 AI 因此早就吃到了。
  · 全文件另有 2 处 `max_tokens: 2000`，在 callVisionModel（AI 判卷·多模态截图判卷）里，
    那条链路独立于问 AI，本轮不动（已在工作记录中列为遗留）。
  · 真正的浪费点：8000 是为迁就**最紧的 DeepSeek（8192）**而定的一刀切值，
    而智谱 glm-5.3-flash 官方上限 131072 —— 上限高的厂商白白少用额度。

改法：按 Provider 分档。只给「有官方文档背书」的智谱单独提高（32000），
      其余一律回落 8000 通用档，避免给出超限值导致 HTTP 400。
"""
import re, os, subprocess

SRC = "光学交互实验室_AI_v6.4.22.html"
DST = "光学交互实验室_AI_v6.4.23.html"
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

# 前置：确认新符号在源文件里不存在（防止误改到同名物）
for sym in ("aiMaxTokens", "AI_MAX_TOKENS_BY_PROVIDER"):
    assert s.count(sym) == 0, "[FAIL] 源文件已存在 %s（%d 处）" % (sym, s.count(sym))

# ---------------------------------------------- R1 常量区：注释改写 + 新增分档表
old_r1 = (
    "     即「默认值本来就够，是我们主动限小了」。这里给到 8000：\n"
    "       · 思考 + 正文都够用；\n"
    "       · 同时不超过其它 Provider 的输出上限（DeepSeek 8K 是最紧的一档，8000 仍在其内），\n"
    "         所以一套值可以安全地套用到所有 OpenAI 协议厂商。 */\n"
    "  const AI_MAX_TOKENS_THINK = 8000;\n"
    "  const AI_MAX_TOKENS_PLAIN = 800;\n"
)
new_r1 = (
    "     即「默认值本来就够，是我们主动限小了」。\n"
    "     V6.4.23 起改为**按 Provider 分档**（见下方分档表）：\n"
    "     8000 退居「通用档」，智谱这类官方上限 131072 的单独给更大值。 */\n"
    "  const AI_MAX_TOKENS_THINK = 8000;   // 通用档（depth-thinking 开启）；DeepSeek 8192 最紧，留余量\n"
    "  const AI_MAX_TOKENS_PLAIN = 800;    // 普通档（未勾深度思考）\n"
    "\n"
    "  /* V6.4.23：按 Provider 分档的输出额度。\n"
    "     背景：各家 max_tokens 上限差得极远 —— 智谱 glm-5.3-flash 官方上限 131072、\n"
    "     默认 65536，而 DeepSeek 这类只有 8192。原来一刀切 8000 是为迁就最紧的一家，\n"
    "     结果上限高的厂商（正是本项目主用的智谱）白白少用了额度，深度思考时正文被挤没了\n"
    "     就是它的表现之一。\n"
    "     策略：**只给有官方文档背书的厂商单独提高，其余一律回落通用档** ——\n"
    "     宁可少用，也不能给出超限值让接口直接 HTTP 400。\n"
    "     问 AI（runChat）与诊断（runDiag）走的是同一个 callLLM，因此分档对两者同时生效。 */\n"
    "  const AI_MAX_TOKENS_BY_PROVIDER = {\n"
    "    zhipu: 32000   // 官方 glm-5.3-flash：默认 65536 / 上限 131072，取 32K 给思考留足余量\n"
    "  };\n"
    "  function aiMaxTokens(thinkOn){\n"
    "    if(!thinkOn) return AI_MAX_TOKENS_PLAIN;\n"
    "    return AI_MAX_TOKENS_BY_PROVIDER[cfg.provider] || AI_MAX_TOKENS_THINK;\n"
    "  }\n"
)
s = rep(s, old_r1, new_r1, label="R1 新增 AI_MAX_TOKENS_BY_PROVIDER + aiMaxTokens()")

# ---------------------------------------------- R2 OpenAI 分支改用分档函数
s = rep(s,
        "      const oaObj = { model:p.model, messages:[{role:'system', content:sysMsg},{role:'user', content:prompt}], temperature:0.5, max_tokens:THINK_ON?AI_MAX_TOKENS_THINK:AI_MAX_TOKENS_PLAIN };",
        "      const oaObj = { model:p.model, messages:[{role:'system', content:sysMsg},{role:'user', content:prompt}], temperature:0.5, max_tokens:aiMaxTokens(THINK_ON) };",
        label="R2 OpenAI 分支改用 aiMaxTokens(THINK_ON)")

# ---------------------------------------------- R3 Anthropic 分支同步
s = rep(s,
        "      const anthObj = { model:p.model, max_tokens:THINK_ON?AI_MAX_TOKENS_THINK:AI_MAX_TOKENS_PLAIN, system:sysMsg, messages:[{role:'user', content:prompt}] };",
        "      const anthObj = { model:p.model, max_tokens:aiMaxTokens(THINK_ON), system:sysMsg, messages:[{role:'user', content:prompt}] };",
        label="R3 Anthropic 分支同步")

# ---------------------------------------------- R4~R7 版本号四处
s = rep(s,
        "  var BUILD = 'v6.4.22', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        "  var BUILD = 'v6.4.23', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        label="R4 BUILD 常量")
s = rep(s, "    return 'v6.4.22';", "    return 'v6.4.23';", label="R5 RPT_BUILD 兜底")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.22 · 修复强制思考模型（GLM-5.3/4.7 等）把输出额度全花在思考上、正文为空时，学情面板会糊出一整包 JSON 的问题；深度思考的输出额度由 2000 提到 8000。">v6.4.22</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.23 · AI 输出额度改为按 Provider 分档：智谱（官方上限 131072）由 8000 放大到 32000，DeepSeek 等仍守 8000 通用档以免超限；问 AI 与诊断共用同一条链路，同时生效。">v6.4.23</div>',
        label="R6 角标文本+title")

old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.22</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>修思考占满输出额度致正文为空。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.23</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>输出额度按厂商分档，智谱放大到32K。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.22</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>修思考占满输出额度致正文为空。</p>\n'
           '      </div>')
s = rep(s, old_log, new_log, label="R7 更新日志新增 V6.4.23")

open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("-" * 68)

# ---------------------------------------------------------------- 一致性断言
assert s.count("AI_MAX_TOKENS_BY_PROVIDER") == 2, "[FAIL] 分档表引用 %d" % s.count("AI_MAX_TOKENS_BY_PROVIDER")
assert s.count("aiMaxTokens") == 3, "[FAIL] aiMaxTokens 次数 %d（声明 1 + 两分支 2）" % s.count("aiMaxTokens")
print("OK  aiMaxTokens 声明+调用 = 3；分档表引用 = 2")
assert s.count("THINK_ON?AI_MAX_TOKENS_THINK") == 0, "[FAIL] 仍有未改的三元表达式"
print("OK  旧的 THINK_ON?AI_MAX_TOKENS_THINK:AI_MAX_TOKENS_PLAIN 已清零")
assert s.count("max_tokens: 2000") == 2, "[FAIL] 判卷链路 2000 应保持 2 处（本轮不动）"
print("OK  判卷链路 max_tokens:2000 仍 2 处（刻意未动）")
assert "zhipu: 32000" in s
print("OK  智谱分档值 = 32000")
assert s.count("v6.4.23") == 3 and "V6.4.23" in s
print("OK  版本号：小写 v6.4.23 x3 + 大写 V6.4.23（title/日志）")

CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script", s))
assert (CLOSES1, OPENS1) == (CLOSES0, OPENS0), "[FAIL] 脚本标签计数变化"
print("OK  脚本标签计数不变 closes=%d opens=%d" % (CLOSES1, OPENS1))

blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk6423", exist_ok=True)
nchk = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk6423", "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
    nchk += 1
print("OK  JS 语法自检通过 %d 块" % nchk)

print("-" * 68)
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
