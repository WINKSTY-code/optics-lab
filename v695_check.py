# -*- coding: utf-8 -*-
"""V6.9.5 静态回归：针对【落盘后的产物】复读断言（§59②）。"""
import re, os, subprocess

DST = "光学交互实验室_AI_v6.9.5.html"
s = open(DST, encoding="utf-8", newline="").read()
fails = []

def ck(cond, msg):
    print(("OK  " if cond else "FAIL") + "  " + msg)
    if not cond: fails.append(msg)

# ① 新模型名只在 4 类位置出现（列表 1 + 注释 1 + 日志 1 + 角标 1），逐一 grep 数过
ck(s.count("{v:'claude-haiku-5.5'}") == 1, "模型列表里 claude-haiku-5.5 恰 1 处")
ck(s.count("claude-haiku-5.5") == 4, "全文件 claude-haiku-5.5 共 4 处（列表/注释/日志/角标）")

# ② anthropic 列表：精确序列 + 顺序正确（§60③）
blk = re.search(r"anthropic:\s*\[(.*?)\]\s*\n", s, re.S).group(1)
order = re.findall(r"\{v:'([^']+)'", blk)
ck(order == ['claude-fable-5.1', 'claude-opus-5.5', 'claude-haiku-5.5', 'claude-opus-5'],
   "anthropic 列表顺序 = fable-5.1 / opus-5.5 / haiku-5.5 / opus-5  实得 %s" % order)
entry = re.search(r"\{v:'claude-haiku-5\.5'[^}]*\}", blk).group(0)
ck(entry == "{v:'claude-haiku-5.5'}", "新条目不带 tag（同族 opus-5 也不带） 实得 %r" % entry)

# ③ 旧条目逐字未动（防误伤）
ck("{v:'claude-fable-5.1',       tag:'旗舰'}," in s, "旗舰条目 claude-fable-5.1 逐字未动")
ck("{v:'claude-opus-5'}" in s, "上一代 claude-opus-5 保留")
ck("anthropic:'claude-fable-5.1'" in s, "默认模型 anthropic 仍是 fable-5.1（默认值变更属另一需求，本轮不动）")
ck("model: 'claude-haiku-4-5'" in s, "判卷链路默认模型逐字未动")

# ④ 版本号四处同步
ck("var BUILD = 'v6.9.5'" in s, "BUILD 常量 = v6.9.5")
ck(">v6.9.5</div>" in s, "角标显示 v6.9.5")
ck('title="光学交互实验室 V6.9.5 · 新增模型支持：claude-haiku-5.5' in s, "角标 title 已更新")
ck("<span class=\"log-ver\">V6.9.5</span><span class=\"log-date\">2026-10-09</span>" in s, "更新日志首条 = V6.9.5 / 2026-10-09")
ck(s.count('class="log-item cur"') == 1, "cur 标记唯一且已前移到新条目")

# ⑤ 日志文案：精确相等（§59⑧），并断言历史条目未被覆写
m = re.search(r'<div class="log-item cur">.*?<p>(.*?)</p>', s, re.S)
ck(m.group(1) == "新增模型支持：claude-haiku-5.5。", "日志正文 =「新增模型支持：claude-haiku-5.5。」 实得 %r" % m.group(1))
ck("四处修正：小孔成像的倒立像高度原来算成了孔的模糊带宽" in s, "V6.9.4 历史条目未被覆写")

# ⑥ 基线回归
ck(s.count('class="tab-btn') == 11, "tab-btn 仍 11 个")
ck(s.count('class="panel') == 12, "panel 仍 12 个")

# ⑦ JS 拆块 node --check（浏览器口径正则 §12）
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk695", exist_ok=True)
bad = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20: continue
    p = "_chk695/b%d.js" % i
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:300]))
ck(bad == 0, "%d 个 script 块全部通过 node --check" % len(blocks))

print("\n体积 %d B  |  失败 %d 项" % (os.path.getsize(DST), len(fails)))
raise SystemExit(1 if fails else 0)
