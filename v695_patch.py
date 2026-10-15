# -*- coding: utf-8 -*-
"""V6.9.5 补丁：AI 设置 anthropic 模型列表新增 claude-haiku-5.5。
清单一类的改动只改「列表源头」，其余渲染层自动跟随（§59①）。"""
import os, re

SRC = "光学交互实验室_AI_v6.9.4.html"
DST = "光学交互实验室_AI_v6.9.5.html"
LOG = []

def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %s  x%d" % (label, c))
    return s.replace(old, new)

s = open(SRC, encoding="utf-8", newline="").read()   # 原文件是 LF，禁掉换行转译
n0 = os.path.getsize(SRC)

o_open = len(re.findall(r"<script(?=[\s>/])", s))
c_open = len(re.findall(r"</script(?=[\s>/])", s))
LOG.append("基线  script开=%d 收尾=%d" % (o_open, c_open))

# R1 模型列表源头：按代际分组，新款插在上一代(opus-5)之前；非旗舰不带 tag（§60②）
s = rep(s,
"""      /* V6.5.1：新增 claude-opus-5.5 */
      {v:'claude-opus-5.5'},
      {v:'claude-opus-5'}""",
"""      /* V6.5.1：新增 claude-opus-5.5 */
      {v:'claude-opus-5.5'},
      /* V6.9.5：新增 claude-haiku-5.5（快速档，非旗舰故不带 tag），与上一代 opus-5 并存 */
      {v:'claude-haiku-5.5'},
      {v:'claude-opus-5'}""",
1, "R1 模型列表新增 claude-haiku-5.5")

# R2 版本号常量
s = rep(s, "var BUILD = 'v6.9.4', MAX_SHOW", "var BUILD = 'v6.9.5', MAX_SHOW", 1, "R2 BUILD 常量")

# R3 版本角标
s = rep(s,
'<div class="ver-badge" title="光学交互实验室 V6.9.4 · 修小孔成像像高公式（原来算成了孔的模糊带宽，与 v/u 读数自相矛盾）；修挑战判卷切题串题（旧题结果会记到新题名下）；补小孔 3D 案例的「不参与记录」守卫；切走实验时真正停掉播放动画与红外紫外场景循环。">v6.9.4</div>',
'<div class="ver-badge" title="光学交互实验室 V6.9.5 · 新增模型支持：claude-haiku-5.5（Anthropic 快速档，AI 设置模型列表可选，与上一代 claude-opus-5 并存）。">v6.9.5</div>',
1, "R3 版本角标")

# R4 更新日志：新条目置 cur，旧条目让位（§59⑧）
s = rep(s,
"""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.9.4</span><span class="log-date">2026-10-08</span></div>""",
"""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.9.5</span><span class="log-date">2026-10-09</span></div>
        <p>新增模型支持：claude-haiku-5.5。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.9.4</span><span class="log-date">2026-10-08</span></div>""",
1, "R4 更新日志新增条目")

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

# ---- 标签计数守恒 ----
o2 = len(re.findall(r"<script(?=[\s>/])", s))
c2 = len(re.findall(r"</script(?=[\s>/])", s))
assert o2 == o_open and c2 == c_open, "[FAIL] script 标签计数变化 %d/%d -> %d/%d" % (o_open, c_open, o2, c2)
LOG.append("OK  script 标签计数守恒  %d/%d" % (o2, c2))

print("\n".join(LOG))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
