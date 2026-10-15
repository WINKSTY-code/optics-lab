# -*- coding: utf-8 -*-
"""
V6.5.0 -> V6.5.1
需求：AI 设置里新增模型支持 —— claude opus 5.5 / gpt 6 sol / gpt 6 luna，放进对应模型列表。
      更新日志写「新增模型支持」，版本 6.5.1。

改动面（最小）：
  R1  MODEL_LISTS.openai     + gpt-6-sol / gpt-6-luna（插在 gpt-6-astra 之后，与 5.6 并存）
  R2  MODEL_LISTS.anthropic  + claude-opus-5.5
  R3  var BUILD              v6.5.0 -> v6.5.1
  R4  RPT_BUILD 兜底常量       v6.5.0 -> v6.5.1
  R5  更新日志                新增 V6.5.1 条目（cur 前移），V6.5.0 让位
  R6  版本角标                文本 + title 同步

规矩：每处替换都断言命中数；产物拆 JS 块过 node --check；再做一次纯静态回归断言。
"""
import os, re, subprocess, sys

SRC = "光学交互实验室_AI_v6.5.0.html"
DST = "光学交互实验室_AI_v6.5.1.html"
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK   %-46s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)

# 基线：改前先量，改后做守恒校验（skill §12 补充 ①：用「前后不变」口径）
N_SCRIPT_OPEN = s.count("<script")
N_SCRIPT_CLOSE = len(re.findall(r"</script(?=[\s>/])", s))
N_TABBEN = s.count('class="tab-btn')
LOG.append("基线 script open=%d close=%d tab-btn=%d" % (N_SCRIPT_OPEN, N_SCRIPT_CLOSE, N_TABBEN))

# MOVE: 断言脚本收尾标签字面量没有任何多余（本补丁不注入任何带尖括号的字符串）
assert len(re.findall(r"</script(?=[\s>/])", s)) == N_SCRIPT_CLOSE

# ---------------------------------------------------------------- R1 openai
s = rep(s,
    "    openai: [\n"
    "      {v:'gpt-6-astra',          tag:'旗舰'},\n"
    "      {v:'gpt-5.6-sol'},\n"
    "      {v:'gpt-5.6-luna'}\n"
    "    ],\n"
    "    anthropic: [\n"
    "      {v:'claude-fable-5.1',       tag:'旗舰'},\n"
    "      {v:'claude-opus-5'}\n"
    "    ]\n",
    "    openai: [\n"
    "      {v:'gpt-6-astra',          tag:'旗舰'},\n"
    "      /* V6.5.1：新增 gpt-6 系列（sol / luna），与上一代 gpt-5.6 并存 */\n"
    "      {v:'gpt-6-sol'},\n"
    "      {v:'gpt-6-luna'},\n"
    "      {v:'gpt-5.6-sol'},\n"
    "      {v:'gpt-5.6-luna'}\n"
    "    ],\n"
    "    anthropic: [\n"
    "      {v:'claude-fable-5.1',       tag:'旗舰'},\n"
    "      /* V6.5.1：新增 claude-opus-5.5 */\n"
    "      {v:'claude-opus-5.5'},\n"
    "      {v:'claude-opus-5'}\n"
    "    ]\n",
    1, "R1/R2 MODEL_LISTS 新增 3 个模型")

# ---------------------------------------------------------------- R3 BUILD
s = rep(s,
    "var BUILD = 'v6.5.0', MAX_SHOW = 3",
    "var BUILD = 'v6.5.1', MAX_SHOW = 3",
    1, "R3 var BUILD")

# ---------------------------------------------------------------- R4 RPT_BUILD
s = rep(s,
    "    return 'v6.5.0';\n  })();",
    "    return 'v6.5.1';\n  })();",
    1, "R4 RPT_BUILD 兜底常量")

# ---------------------------------------------------------------- R5 更新日志
s = rep(s,
    "      <div class=\"log-item cur\">\n"
    "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.0</span><span class=\"log-date\">2026-09-21</span></div>\n"
    "        <p>three.js 抽为常量，删自检钩子。</p>\n"
    "      </div>\n",
    "      <div class=\"log-item cur\">\n"
    "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.1</span><span class=\"log-date\">2026-09-23</span></div>\n"
    "        <p>新增模型支持。</p>\n"
    "      </div>\n"
    "      <div class=\"log-item\">\n"
    "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.0</span><span class=\"log-date\">2026-09-21</span></div>\n"
    "        <p>three.js 抽为常量，删自检钩子。</p>\n"
    "      </div>\n",
    1, "R5 更新日志新增 V6.5.1")

# ---------------------------------------------------------------- R6 角标
# 角标 title 极长且含全角括号，逐字转写风险高 -> 用正则精确锚定「ver-badge + title + v6.5.0 文本」
NEW_BADGE = ('<div class="ver-badge" title="光学交互实验室 V6.5.1 · AI 设置新增模型支持：OpenAI 增加 gpt-6-sol、'
             'gpt-6-luna，Anthropic 增加 claude-opus-5.5。">v6.5.1</div>')
_bt = re.findall(r'<div class="ver-badge" title="[^"]*">v6\.5\.0</div>', s)
assert len(_bt) == 1, "[FAIL] R6 版本角标: 期望 1 处，实际 %d 处" % len(_bt)
LOG.append("OK   %-46s x1（旧 title 长 %d 字符）" % ("R6 版本角标文本+title", len(_bt[0])))
s = s.replace(_bt[0], NEW_BADGE)

# ---------------------------------------------------------------- 落盘
# 源文件为 CRLF（实测 CRLF=11900 / bare LF=0）；文本模式读取已归一到 \n，
# 写回时显式用 newline="\r\n" 还原行尾，避免把全文件行尾悄悄改成 LF。
open(DST, "w", encoding="utf-8", newline="\r\n").write(s)
n1 = os.path.getsize(DST)
assert open(DST, "rb").read().count(b"\n") == open(DST, "rb").read().count(b"\r\n"), "[FAIL] 行尾不一致"

# ---------------------------------------------------------------- 守恒校验
assert s.count("<script") == N_SCRIPT_OPEN, "[FAIL] script 开标签数变了"
assert len(re.findall(r"</script(?=[\s>/])", s)) == N_SCRIPT_CLOSE, "[FAIL] script 收尾标签数变了"
assert s.count('class="tab-btn') == N_TABBEN, "[FAIL] tab-btn 数变了"
LOG.append("OK   script/tab-btn 计数前后守恒")

# ---------------------------------------------------------------- 静态回归
def ck(cond, msg):
    assert cond, "[FAIL] " + msg
    LOG.append("OK   " + msg)

ck(s.count("{v:'gpt-6-sol'}") == 1, "gpt-6-sol 入列 1 处")
ck(s.count("{v:'gpt-6-luna'}") == 1, "gpt-6-luna 入列 1 处")
ck(s.count("{v:'claude-opus-5.5'}") == 1, "claude-opus-5.5 入列 1 处")
# 定向抽取 openai / anthropic 两段，断言新旧并存且顺序正确
_m = re.search(r"    openai: \[\n(.*?)\n    \],\n    anthropic: \[\n(.*?)\n    \]", s, re.S)
ck(_m is not None, "定位到 openai / anthropic 两段")
_op, _an = _m.group(1), _m.group(2)
ck(_op.index("{v:'gpt-6-astra'") < _op.index("{v:'gpt-6-sol'}") < _op.index("{v:'gpt-6-luna'}") < _op.index("{v:'gpt-5.6-sol'}")
   < _op.index("{v:'gpt-5.6-luna'}"), "openai 顺序：astra → 6-sol → 6-luna → 5.6-sol → 5.6-luna")
ck(_an.index("{v:'claude-fable-5.1'") < _an.index("{v:'claude-opus-5.5'}") < _an.index("{v:'claude-opus-5'}"),
   "anthropic 顺序：fable-5.1 → opus-5.5 → opus-5")
# 不该动的：其它四家列表逐字未动
for _seg in ["    zhipu: [\n      {v:'GLM-5.3-FlashX',   tag:'超高速'},\n      {v:'GLM-5.3',          tag:'旗舰'},\n"
             "      {v:'GLM-5.3-Flash',    tag:'性价比'},\n      {v:'GLM-4.7-Flash',    tag:'免费'},\n"
             "      {v:'GLM-4.5-Air'}\n    ],",
             "    deepseek: [\n      /* V4.9.1：只保留 v4.1-flash；v4-pro / v4-flash 已从列表移除（老配置由 loadCfg 自动迁移） */\n"
             "      {v:'deepseek-v4.1-flash'}\n    ],",
             "    minimax: [\n      {v:'MiniMax-M3',           tag:'旗舰'},\n      {v:'MiniMax-M2.7'}\n    ],",
             "    kimi: [\n      {v:'kimi-K3',              tag:'旗舰'},\n      {v:'kimi-k2.8-preview'},\n"
             "      {v:'kimi-k2.7-code'},\n      {v:'kimi-k2.6'}\n    ],"]:
    ck(_seg in s, "其它厂商列表逐字未动（%s）" % _seg.strip().split(":")[0])
ck("openai:'gpt-5.6-luna'," in s and "anthropic:'claude-fable-5.1'" in s, "DEFAULT_MODELS 未受影响")
ck(s.count("var BUILD = 'v6.5.1'") == 1, "BUILD 已升到 v6.5.1")
ck(s.count("return 'v6.5.1';") == 1, "RPT_BUILD 兜底已升到 v6.5.1")
ck('class="log-ver">V6.5.1</span><span class="log-date">2026-09-23' in s, "更新日志 V6.5.1 条目已插入")
ck('<p>新增模型支持。</p>' in s, "更新日志文案为「新增模型支持」")
ck(s.count('class="log-ver">V6.5.1') == 1, "V6.5.1 日志条目唯一")
ck('class="log-item cur">\n        <div class="log-head"><span class="log-ver">V6.5.1' in s, "新增条目为最新的 cur 条目")
ck(s.count('class="log-item cur"') == 1, "cur 条目全局唯一（V6.5.0 已让位）")
ck(s.count('class="log-ver">V6.5.0') == 1, "V6.5.0 条目仍在（历史保留）")
ck(s.count("v6.5.0") == 0, "旧版本号 v6.5.0 已全部替换") if s.count("v6.5.0") == 0 else LOG.append(
    "NOTE 残留旧串 v6.5.0 x%d（见下）" % s.count("v6.5.0"))
if s.count("v6.5.0") != 0:
    for _m2 in re.finditer(r"v6\.5\.0", s):
        print("   残留 @%d: ...%s..." % (_m2.start(), s[max(0, _m2.start() - 60):_m2.start() + 30].replace("\n", " ")))

# ---------------------------------------------------------------- JS 语法自检（浏览器口径切块）
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk651", exist_ok=True)
nb = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk651", "blk%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:400])
    nb += 1
LOG.append("OK   node --check 通过 %d 个非空 script 块（共 %d）" % (nb, len(blocks)))

print("\n".join(LOG))
print("\n源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
