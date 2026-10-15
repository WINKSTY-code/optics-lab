# -*- coding: utf-8 -*-
"""V6.4.18 -> V6.4.18a：更新日志条目精简到 20 字以内。"""
import os

F = "光学交互实验室_AI_v6.4.18.html"

old = "        <p>APIKey 本地存储提示改为「关闭页面时」弹出——不再一打开就拦一道，只在离开前提醒处理 Key。</p>"
new = "        <p>APIKey 提示改到关闭页面时弹。</p>"

s = open(F, encoding="utf-8").read()
assert s.count(old) == 1, "[FAIL] 旧条目命中 %d 处" % s.count(old)
s = s.replace(old, new)
assert s.count(new) == 1

pure = "APIKey 提示改到关闭页面时弹。"
assert len(pure) <= 20, "[FAIL] 文案 %d 字，超过 20" % len(pure)

open(F, "w", encoding="utf-8", newline="").write(s)
print("OK  更新日志条目精简：%d 字 -> %d 字" % (len("APIKey 本地存储提示改为「关闭页面时」弹出——不再一打开就拦一道，只在离开前提醒处理 Key。"), len(pure)))
print("本次改动 %d B" % (len(s) - os.path.getsize(F)))

# 复核：角标（右下角）版本与 title
import re
badge = re.search(r'<div class="ver-badge"[^>]*>([^<]+)</div>', s)
print("右下角角标正文:", badge.group(1))
t = re.search(r'<div class="ver-badge" title="([^"]*)"', s)
print("右下角角标 title:", t.group(1))
assert badge.group(1).strip() == "v6.4.18"
assert "V6.4.18" in t.group(1) and "关闭页面时" in t.group(1)
print("OK  右下角角标已同步")
