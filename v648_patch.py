# -*- coding: utf-8 -*-
"""V6.4.8 补丁：修「顶栏右上角空了一块」
根因：V6.4.6 把「设置」(.set-wrap) 从 .topbar-right 里拆出来、变成 .topbar 的第二个同级子项，
     而 .topbar 是 justify-content:space-between —— 三个子项时它会把富余空间【平均摊在每两项之间】，
     于是按钮簇被推到中间、「设置」孤零零贴最右，中间空出 ~225px 的洞。
修法：把 .topbar-right 与 .set-wrap 重新包进一个 .topbar-actions（该容器 overflow:visible，
     不会裁掉绝对定位的下拉），桌面端整簇贴右、窄屏整行铺开并让「设置」跟着按钮流排布。
"""
import os, re

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.7.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.8.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, "r", encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)
closes0 = len(re.findall(r"</script(?=[\s>/])", s))
opens0 = len(re.findall(r"<script(?=[\s>/])", s))
V647_BEFORE = s.count("V6.4.7")

# ---------- 1. DOM：把「设置」与按钮簇包成一个整体 ----------
s = rep(s, '    <div class="topbar-right">\n      <span id="aiStatus"',
       '    <div class="topbar-actions">\n    <div class="topbar-right">\n      <span id="aiStatus"',
   1, "DOM 包裹：.topbar-actions 开标签")

s = rep(s, '        <button id="themeBtn" class="set-item" role="menuitem">黑板</button>\n      </div>\n    </div>\n  </div>',
       '        <button id="themeBtn" class="set-item" role="menuitem">黑板</button>\n      </div>\n    </div>\n    </div>\n  </div>',
   1, "DOM 包裹：.topbar-actions 闭标签")

# 原注释补一句说明（V6.4.8）
s = rep(s, '    <!-- V6.4.6 · 「设置」下拉：字体调节 / 语言调节 / AI 设置 / 背景色调节 四入口合并。',
       '    <!-- V6.4.8 · 上面 .topbar-right 与下面 .set-wrap 由 .topbar-actions 包成一个整体，\n'
       '         保证「设置」紧贴按钮簇、不再被 space-between 摊到两边（修「右上角空一块」）。 -->\n'
       '    <!-- V6.4.6 · 「设置」下拉：字体调节 / 语言调节 / AI 设置 / 背景色调节 四入口合并。',
   1, "注释：补 V6.4.8 说明")

# ---------- 2. CSS：新增 .topbar-actions；.set-wrap 交出 position:relative ----------
s = rep(s, '  .set-wrap{position:relative;display:inline-flex;align-items:center;flex:0 0 auto;}',
       '  /* V6.4.8 · 顶栏右侧按钮簇：把 .topbar-right 与「设置」包成一个整体。\n'
       '     V6.4.6 曾把「设置」拆成 .topbar-right 的同级子项，而 .topbar 用 space-between ——\n'
       '     三个子项时富余空间被平均摊在每两项之间，按钮簇被推到中间、「设置」孤零零贴最右，\n'
       '     中间空出一大块（就是「右上角空了一块」）。包一层后：桌面端整簇贴右、设置紧贴簇尾。\n'
       '     容器 overflow:visible（不是滚动容器）→ 绝对定位的下拉层不会被裁掉；\n'
       '     position:relative 兼作 .set-menu 的包含块（窄屏整行铺开时下拉也绝不会溢出视口）。 */\n'
       '  .topbar-actions{position:relative;display:flex;align-items:center;gap:4px;flex:0 0 auto;min-width:0;}\n'
       '  .set-wrap{display:inline-flex;align-items:center;flex:0 0 auto;}',
   1, "CSS：新增 .topbar-actions / set-wrap 去 relative")

s = rep(s, '  /* ≤880px：顶栏必然换行（移动端闸门就在 880px），把「设置」推到本行行尾 */\n'
       '  @media (max-width:880px){\n'
       '    .set-wrap{margin-left:auto;}\n'
       '  }',
       '  /* ≤880px：顶栏必然换行（移动端闸门就在 880px）。\n'
       '     V6.4.8：按钮簇整行铺开；.topbar-right 用 display:contents 拆掉自己的盒子，\n'
       '     让它的按钮与「设置」落在同一个换行流里依次排布 —— 否则「设置」会被挤到\n'
       '     自己独占一行，那一行左边就空一大块。 */\n'
       '  @media (max-width:880px){\n'
       '    .topbar-actions{flex:1 1 100%;flex-wrap:wrap;gap:6px 3px;justify-content:flex-start;}\n'
       '    .topbar-right{display:contents;}\n'
       '  }',
   1, "CSS：≤880px 改整行铺开 + display:contents")

# ---------- 3. 版本号四处同步 ----------
s = rep(s, "var BUILD = 'v6.4.7'", "var BUILD = 'v6.4.8'", 1, "版本：BUILD")
s = rep(s, "    return 'v6.4.7';", "    return 'v6.4.8';", 1, "版本：报告兜底 RPT_BUILD")
s = rep(s, '<div class="ver-badge" title="光学交互实验室 V6.4.7 · 凸透镜3D可移透镜，底栏一行三个。">v6.4.7</div>',
       '<div class="ver-badge" title="光学交互实验室 V6.4.8 · 顶栏设置紧贴按钮簇，修掉右上角空白。">v6.4.8</div>',
   1, "版本：右下角角标（title + 文本）")

# ---------- 4. 更新日志：新增 cur 条，旧的降级 ----------
s = rep(s, '      <div class="log-item cur">\n'
       '        <div class="log-head"><span class="log-ver">V6.4.7</span><span class="log-date">2026-09-18</span></div>\n'
       '        <p>凸透镜3D可移动透镜，底栏一行三个。</p>\n'
       '      </div>',
       '      <div class="log-item cur">\n'
       '        <div class="log-head"><span class="log-ver">V6.4.8</span><span class="log-date">2026-09-18</span></div>\n'
       '        <p>修顶栏设置按钮与按钮簇间的空白。</p>\n'
       '      </div>\n'
       '      <div class="log-item">\n'
       '        <div class="log-head"><span class="log-ver">V6.4.7</span><span class="log-date">2026-09-18</span></div>\n'
       '        <p>凸透镜3D可移动透镜，底栏一行三个。</p>\n'
       '      </div>',
   1, "更新日志：插入 V6.4.8 首条")

# ---------- 硬校验 ----------
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
opens1 = len(re.findall(r"<script(?=[\s>/])", s))
assert closes1 == closes0, "[FAIL] 脚本收尾标签字面量数变了: %d -> %d" % (closes0, closes1)
assert opens1 == opens0, "[FAIL] 脚本开标签数变了: %d -> %d" % (opens0, opens1)
# 预期 4 处：DOM 的 class 属性 + DOM 注释 + 基础 CSS 规则 + ≤880px 媒体查询里的规则
assert s.count("topbar-actions") == 4, "[FAIL] topbar-actions 应为 4 处，实际 %d" % s.count("topbar-actions")
assert s.count(".topbar-actions{") == 2, "[FAIL] .topbar-actions 规则应为 2 条（基础 + 窄屏）"
assert s.count("display:contents") == 2, "[FAIL] display:contents 应为 2 处（注释 + 规则），实际 %d" % s.count("display:contents")
assert "position:relative;display:inline-flex" not in s, "[FAIL] .set-wrap 仍带 position:relative"
assert s.count("v6.4.7") == 0, "[FAIL] 小写 v6.4.7 仍有残留: %d" % s.count("v6.4.7")
# 大写 V6.4.7 在正文里共 13 处（历史标注）；其中角标 title 那 1 处已升到 V6.4.8，
# 更新日志那 1 处要保留 → 改完应为 12
assert s.count("V6.4.7") == V647_BEFORE - 1, "[FAIL] V6.4.7 注释数异常: %d -> %d" % (V647_BEFORE, s.count("V6.4.7"))
assert s.count("v6.4.8") == 3, "[FAIL] 小写 v6.4.8 应为 3 处（BUILD + 报告兜底 + 角标文本）"
assert s.count("V6.4.8") == 5, "[FAIL] 大写 V6.4.8 应为 5 处（2 CSS 注释 + 1 DOM 注释 + 更新日志 + 角标 title），实际 %d" % s.count("V6.4.8")

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 62)
print("脚本标签：opens %d -> %d, closes %d -> %d" % (opens0, opens1, closes0, closes1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
