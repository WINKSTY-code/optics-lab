# -*- coding: utf-8 -*-
"""V6.4.26 静态自检：拆 script 块过 node --check + 标签计数/换行符/关键串核对"""
import os
import re
import subprocess

NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
SRC = "光学交互实验室_AI_v6.4.25.html"
DST = "光学交互实验室_AI_v6.4.26.html"
OUT = "_chk6426"

# ① 拆块（浏览器口径：收尾标签后允许 空白 / > ）
html = open(DST, encoding="utf-8").read()
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
os.makedirs(OUT, exist_ok=True)
nb = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(OUT, "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:400])
    nb += 1
print("[OK] %d 个 script 块全部通过 node --check（共切出 %d 块）" % (nb, len(blocks)))

# ② 标签计数前后不变
s0 = open(SRC, encoding="utf-8").read()
for name, pat in (("opens", r"<script"), ("closes", r"</script(?=[\s>/])")):
    a, b = len(re.findall(pat, s0)), len(re.findall(pat, html))
    assert a == b, "[FAIL] %s 计数变了 %d -> %d" % (name, a, b)
    print("[OK] script %s 计数不变: %d" % (name, a))

# ③ 换行符保持 CRLF
raw = open(DST, "rb").read()
crlf, lf = raw.count(b"\r\n"), raw.count(b"\n")
assert crlf == lf, "[FAIL] 出现裸 LF 行: CRLF=%d LF=%d" % (crlf, lf)
print("[OK] 换行符仍为 CRLF（%d 行），磁盘 %d B" % (crlf, os.path.getsize(DST)))

# ④ 关键串核对
must_have = [
    "thinkMode: main.thinkMode !== false",
    "const THINK_ON = jc.thinkMode !== false;",
    "if (THINK_ON) { if (jc.provider === 'zhipu') obj.thinking = { type: 'enabled' }; }",
    "anthObj.thinking = THINK_ON ? { type: 'enabled', budget_tokens: 1024 } : { type: 'disabled' };",
    "window.AI_TIMEOUT_MS = AI_TIMEOUT_MS;",
    "const _to = (typeof window.AI_TIMEOUT_MS === 'number' && window.AI_TIMEOUT_MS > 0)",
    "' · 🧠 深度思考'",
    "var BUILD = 'v6.4.26'",
    "return 'v6.4.26';",
">v6.4.26</div>",
    "<span class=\"log-ver\">V6.4.26</span>",
    "思考模式与顶部「⚙ AI 设置」的「深度思考模式」保持一致",
]
for m in must_have:
    assert m in html, "[FAIL] 缺少关键串: %s" % m
print("[OK] %d 条关键串全部存在" % len(must_have))

must_not = [
    ("判卷旧超时传参", "}, 20000, 1);"),
    ("判卷旧超时文案", "判卷请求超时（20 秒未响应）"),
    ("判卷旧硬关思考", "if (NO_THINK.indexOf(jc.provider) >= 0) obj.thinking = { type: 'disabled' };   // V4.7"),
]
for label, m in must_not:
    assert m not in html, "[FAIL] %s 仍在: %s" % (label, m)
print("[OK] %d 条旧串已清零" % len(must_not))

# ⑤ 该动 / 不该动 的定向核对
assert html.count("const THINK_ON = cfg.thinkMode !== false;") == 1, "[FAIL] 主链路 THINK_ON 被动"
assert html.count("const AI_TIMEOUT_MS = 180000;") == 1, "[FAIL] 主链路超时常量被动"
# 主链路 callLLM 的 thinking 分支逐字未动
assert "if(THINK_ON){ if(cfg.provider==='zhipu') oaObj.thinking = { type:'enabled' }; }" in html, "[FAIL] 主链路 zhipu 分支被改"
assert "else if(p.noThink) oaObj.thinking = { type:'disabled' };" in html, "[FAIL] 主链路 disabled 分支被改"
assert "if(THINK_ON){ anthObj.thinking = { type:'enabled', budget_tokens:1024 }; anthObj.temperature = 1; }" in html, "[FAIL] 主链路 anthropic 分支被改"
# 判卷额度仍走思考档（不跟着降到 800）
assert "return window.aiMaxTokens(true, provider);" in html, "[FAIL] 判卷额度被改动"
print("[OK] 主链路 callLLM 与判卷额度均逐字未动")

# ⑥ 英文/繁体侧未被误伤（本次只动中文硬编码文案）
for k in ("'aiCfg.thinkMode':{zh:'🧠 深度思考模式（默认开启）'", "'aiCfg.thinkMode':{zh:'🧠 深度思考模式（預設開啟）'"):
    pass
assert "'aiCfg.thinkMode':{zh:'🧠 深度思考模式（默认开启）', zht:'🧠 深度思考模式（預設開啟）', en:'🧠 Deep thinking mode (on by default)'}," in html, "[FAIL] AI 设置里的思考模式词条被误改"
print("[OK] AI 设置「深度思考模式」词条三语逐字未动")
print("\n全部静态自检通过。")
