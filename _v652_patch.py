# -*- coding: utf-8 -*-
"""
V6.5.1 -> V6.5.2 安全补丁
需求：新增模型支持 MiniMax-M3.1-Flash-Preview
口径：
  1) 只改 MODEL_LISTS.minimax（列表源头），渲染函数 / 默认值表 / 判卷自由输入一律不动
  2) 新条目插在「同代旗舰 MiniMax-M3」之后，tag 沿用同族兄弟（M2.7 无 tag -> 新条目也无 tag）
  3) 版本号四处同步：BUILD / RPT_BUILD 兜底 / 更新日志 / 右下角角标
"""
import re, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.5.1.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.5.2.html")

LOG = []
def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-34s x%d" % (label, c))
    return s.replace(old, new)

# 关键：newline='' 保留 CRLF，避免写回时把 11909 处 CRLF 归一成 LF
s = open(SRC, encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)

opens0 = len(re.findall(r"<script[\s>]", s))
closes0 = len(re.findall(r"</script(?=[\s>/])", s))

# ---------- R1 版本常量 ----------
s = rep(s, "  var BUILD = 'v6.5.1', MAX_SHOW = 3,",
           "  var BUILD = 'v6.5.2', MAX_SHOW = 3,", 1, "R1 BUILD")

# ---------- R2 模型清单（唯一改动源头） ----------
OLD2 = ("    minimax: [\r\n"
        "      {v:'MiniMax-M3',           tag:'旗舰'},\r\n"
        "      {v:'MiniMax-M2.7'}\r\n"
        "    ],")
NEW2 = ("    minimax: [\r\n"
        "      {v:'MiniMax-M3',           tag:'旗舰'},\r\n"
        "      /* V6.5.2：新增 MiniMax-M3.1-Flash-Preview（预览版），与上一代 M2.7 并存 */\r\n"
        "      {v:'MiniMax-M3.1-Flash-Preview'},\r\n"
        "      {v:'MiniMax-M2.7'}\r\n"
        "    ],")
s = rep(s, OLD2, NEW2, 1, "R2 MODEL_LISTS.minimax")

# ---------- R3 更新日志（cur 前移，历史条目不动） ----------
OLD3 = ("      <div class=\"log-item cur\">\r\n"
        "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.1</span><span class=\"log-date\">2026-09-23</span></div>\r\n"
        "        <p>新增模型支持。</p>\r\n"
        "      </div>")
NEW3 = ("      <div class=\"log-item cur\">\r\n"
        "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.2</span><span class=\"log-date\">2026-09-29</span></div>\r\n"
        "        <p>新增模型支持：MiniMax-M3.1-Flash-Preview。</p>\r\n"
        "      </div>\r\n"
        "      <div class=\"log-item\">\r\n"
        "        <div class=\"log-head\"><span class=\"log-ver\">V6.5.1</span><span class=\"log-date\">2026-09-23</span></div>\r\n"
        "        <p>新增模型支持。</p>\r\n"
        "      </div>")
s = rep(s, OLD3, NEW3, 1, "R3 更新日志")

# ---------- R4 报告模块版本兜底 ----------
s = rep(s, "    return 'v6.5.1';", "    return 'v6.5.2';", 1, "R4 RPT_BUILD 兜底")

# ---------- R5 右下角版本角标 ----------
s = rep(s,
        "<div class=\"ver-badge\" title=\"光学交互实验室 V6.5.1 · AI 设置新增模型支持：OpenAI 增加 gpt-6-sol、gpt-6-luna，Anthropic 增加 claude-opus-5.5。\">v6.5.1</div>",
        "<div class=\"ver-badge\" title=\"光学交互实验室 V6.5.2 · AI 设置新增模型支持：MiniMax 增加 MiniMax-M3.1-Flash-Preview。\">v6.5.2</div>",
        1, "R5 版本角标")

# ---------- 硬校验：脚本标签计数前后不变 ----------
opens1 = len(re.findall(r"<script[\s>]", s))
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
assert opens1 == opens0, "[FAIL] script 开标签计数变了：%d -> %d" % (opens0, opens1)
assert closes1 == closes0, "[FAIL] script 收尾标签计数变了：%d -> %d" % (closes0, closes1)
LOG.append("OK  %-34s opens %d==%d, closes %d==%d" % ("script 标签计数守恒", opens0, opens1, closes0, closes1))

# ---------- 写入 ----------
open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

# ---------- 落盘后从磁盘复读，再断言（不接受内存里的 s） ----------
s2 = open(DST, encoding="utf-8", newline="").read()
CK = []
def ck(cond, msg):
    CK.append(("OK " if cond else "!! ") + msg)
    assert cond, "[FAIL] " + msg

ck(s2.count("{v:'MiniMax-M3.1-Flash-Preview'}") == 1, "产物：新模型入列 1 处")
mi0 = s2.index("minimax: [")
mi1 = s2.index("],", mi0)
seg = s2[mi0:mi1]
order = re.findall(r"\{v:'([^']+)'", seg)
ck(order == ["MiniMax-M3", "MiniMax-M3.1-Flash-Preview", "MiniMax-M2.7"], "产物：minimax 顺序 = %s" % order)
ck("MiniMax-M3.1-Flash-Preview'" in seg and "tag:" not in seg.split("MiniMax-M3.1-Flash-Preview")[1][:40].split("\n")[0].split("\r")[0], "产物：新条目无 tag（沿用同族 M2.7 风格）")
ck("var BUILD = 'v6.5.2'" in s2, "产物：BUILD = v6.5.2")
ck("return 'v6.5.2';" in s2, "产物：RPT_BUILD 兜底 = v6.5.2")
ck('>v6.5.2</div>' in s2, "产物：版本角标文本 = v6.5.2")
ck("V6.5.1 · AI 设置" not in s2, "产物：角标 title 里旧版本串已清零")
ck(s2.count('class="log-item cur"') == 1, "产物：log-item cur 仅 1 个")
ck("<span class=\"log-ver\">V6.5.2</span><span class=\"log-date\">2026-09-29</span>" in s2, "产物：新日志条目 V6.5.2 / 2026-09-29")
ck("<p>新增模型支持：MiniMax-M3.1-Flash-Preview。</p>" in s2, "产物：新日志正文")
ck("<p>新增模型支持。</p>" in s2, "产物：V6.5.1 历史条目逐字未动")
ck(s2.count("<span class=\"log-ver\">V6.5.1</span>") == 1, "产物：V6.5.1 日志条目仍在（历史不被覆写）")
ck(s2.count("{v:'MiniMax-M3',") == 1 and s2.count("{v:'MiniMax-M2.7'}") == 1, "产物：旧 minimax 条目逐字未动")
ck(s2.count("MiniMax-M3.1-Flash-Preview") == 4, "产物：新模型名总出现 4 处（列表 1 + 注释 1 + 日志 1 + 角标 title 1）")
ck("MiniMax-M3'" in s2, "产物：判卷默认 MiniMax-M3 未动")
ck(s2.count("'gpt-6-sol'") == 1 and s2.count("'claude-opus-5.5'") == 1, "产物：V6.5.1 新增的模型条目未被误伤")
ck(len(re.findall(r"</script(?=[\s>/])", s2)) == closes0, "产物：script 收尾标签计数守恒")

print("\n".join(LOG))
print("\n".join(CK))
print("\n源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
