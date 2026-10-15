# -*- coding: utf-8 -*-
"""V6.4.18 -> V6.4.19
需求：AI 设置里智谱 Provider 下新增端点切换按钮（GLM Coding Plan 套餐端点 / 按量计费通用端点），
     交互与 MiniMax「国内 / 国际」区域按钮一致。
每处替换都断言命中次数；产物过 JS 语法自检 + DOM 嵌套体检 + 标签计数不变校验。
"""
import re, os, subprocess, sys

SRC = "光学交互实验室_AI_v6.4.18.html"
DST = "光学交互实验室_AI_v6.4.19.html"
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
CLOSES0 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS0 = len(re.findall(r"<script", s))

# ---------------------------------------------------------------- R1 版本号常量
s = rep(s,
        "  var BUILD = 'v6.4.18', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        "  var BUILD = 'v6.4.19', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;",
        label="R1 BUILD 常量")

# ------------------------------------------------- R2 RPT_BUILD 兜底常量（IIFE 内）
s = rep(s,
        "    return 'v6.4.18';",
        "    return 'v6.4.19';",
        label="R2 RPT_BUILD 兜底")

# ------------------------------------------------------------- R3 角标 + title
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.18 · APIKey 本地存储提示改为「关闭页面时」弹出（不再打断刚进入页面的使用）；AI 调用保留 20 秒超时与失败 1 次自动重试。">v6.4.18</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.19 · AI 设置里智谱 Provider 下新增端点切换按钮：GLM Coding Plan 套餐端点 / 按量计费通用端点，一键填写 Base URL 并高亮当前端点。">v6.4.19</div>',
        label="R3 角标文本+title")

# --------------------------------------------------------------- R4 更新日志新增
old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.18</span><span class="log-date">2026-09-20</span></div>\n'
           '        <p>APIKey 提示改到关闭页面时弹。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.19</span><span class="log-date">2026-09-21</span></div>\n'
           '        <p>智谱新增套餐/按量端点一键切换。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.18</span><span class="log-date">2026-09-20</span></div>\n'
           '        <p>APIKey 提示改到关闭页面时弹。</p>\n'
           '      </div>')
s = rep(s, old_log, new_log, label="R4 更新日志新增 V6.4.19")

# ------------------------------------------------------------------- R5 i18n 词条
old_i18n = ("'aiCfg.baseUrl':  {zh:'Base URL（留空用当前 Provider 默认）：', zht:'Base URL（留空用當前 Provider 預設）：', en:'Base URL (empty = provider default):'},")
new_i18n = (old_i18n + "\n" +
            "'aiCfg.epPlan':   {zh:'🎫 套餐额度 · coding/paas/v4', zht:'🎫 套餐額度 · coding/paas/v4', en:'🎫 Plan quota · coding/paas/v4'},\n"
            "'aiCfg.epPayg':   {zh:'💳 按量计费 · paas/v4', zht:'💳 按量計費 · paas/v4', en:'💳 Pay-as-you-go · paas/v4'},\n"
            "'aiCfg.epPlanTip':{zh:'GLM Coding Plan 套餐专属端点：https://open.bigmodel.cn/api/coding/paas/v4/chat/completions', zht:'GLM Coding Plan 套餐專屬端點：https://open.bigmodel.cn/api/coding/paas/v4/chat/completions', en:'GLM Coding Plan dedicated endpoint: https://open.bigmodel.cn/api/coding/paas/v4/chat/completions'},\n"
            "'aiCfg.epPaygTip':{zh:'按量计费通用端点：https://open.bigmodel.cn/api/paas/v4/chat/completions', zht:'按量計費通用端點：https://open.bigmodel.cn/api/paas/v4/chat/completions', en:'Pay-as-you-go general endpoint: https://open.bigmodel.cn/api/paas/v4/chat/completions'},\n"
            "'aiCfg.epNote':   {zh:'💡 智谱分两套端点：买了 GLM Coding Plan 套餐选「套餐额度」，用充值余额 / 资源包选「按量计费」；选错会报 1113 余额不足。', zht:'💡 智譜分兩套端點：買了 GLM Coding Plan 套餐選「套餐額度」，用儲值餘額 / 資源包選「按量計費」；選錯會報 1113 餘額不足。', en:'💡 Zhipu has two endpoints: pick “Plan quota” for a GLM Coding Plan, “Pay-as-you-go” for prepaid balance / resource packs; the wrong one raises error 1113 (insufficient balance).'},")
s = rep(s, old_i18n, new_i18n, label="R5 i18n 新增 5 条词条")

# ------------------------------------- R6 REGIONS 增加 zhipu 两组 + 当前端点高亮
old_reg = (
    "      const REGIONS = {\n"
    "        minimax: [\n"
    "          {label:'🇨🇳 国内 · api.minimaxi.com', url:'https://api.minimaxi.com/v1'},\n"
    "          {label:'🌐 国际 · api.minimax.io',    url:'https://api.minimax.io/v1'}\n"
    "        ],\n"
    "        kimi: [\n"
    "          {label:'🇨🇳 国内 · api.moonshot.cn', url:'https://api.moonshot.cn/v1'},\n"
    "          {label:'🌐 国际 · api.moonshot.ai',  url:'https://api.moonshot.ai/v1'}\n"
    "        ]\n"
    "      };\n"
    "      const list = REGIONS[prov];\n"
    "      if(!list){\n"
    "        cont.innerHTML = ''; cont.style.display = 'none'; return;\n"
    "      }\n"
    "      cont.style.display = 'flex';\n"
    "      cont.innerHTML = list.map(r =>\n"
    "        '<button type=\"button\" class=\"sec\" data-url=\"'+r.url+'\" style=\"padding:5px 10px;font-size:11px;\">'+r.label+'</button>'\n"
    "      ).join('');\n"
    "      cont.querySelectorAll('button[data-url]').forEach(b => {\n"
    "        b.onclick = () => { $('aiBaseUrl').value = b.dataset.url; };\n"
    "      });\n"
)
new_reg = (
    "      const REGIONS = {\n"
    "        minimax: [\n"
    "          {label:'🇨🇳 国内 · api.minimaxi.com', url:'https://api.minimaxi.com/v1'},\n"
    "          {label:'🌐 国际 · api.minimax.io',    url:'https://api.minimax.io/v1'}\n"
    "        ],\n"
    "        kimi: [\n"
    "          {label:'🇨🇳 国内 · api.moonshot.cn', url:'https://api.moonshot.cn/v1'},\n"
    "          {label:'🌐 国际 · api.moonshot.ai',  url:'https://api.moonshot.ai/v1'}\n"
    "        ],\n"
    "        /* V6.4.19：智谱的「套餐额度」与「按量计费」是两套端点，Key 也不通用。\n"
    "           Coding Plan 专属端点 /api/coding/paas/v4 只能用套餐额度；\n"
    "           通用端点 /api/paas/v4 走充值余额 / 资源包。混用会报 1113 余额不足。 */\n"
    "        zhipu: [\n"
    "          {label:T('aiCfg.epPlan'), url:'https://open.bigmodel.cn/api/coding/paas/v4', title:T('aiCfg.epPlanTip')},\n"
    "          {label:T('aiCfg.epPayg'), url:'https://open.bigmodel.cn/api/paas/v4',        title:T('aiCfg.epPaygTip')}\n"
    "        ]\n"
    "      };\n"
    "      const list = REGIONS[prov];\n"
    "      if(!list){\n"
    "        cont.innerHTML = ''; cont.style.display = 'none'; return;\n"
    "      }\n"
    "      cont.style.display = 'flex';\n"
    "      cont.innerHTML = list.map(r =>\n"
    "        '<button type=\"button\" class=\"sec\" data-url=\"'+r.url+'\" style=\"padding:5px 10px;font-size:11px;white-space:nowrap;\"'+(r.title?' title=\"'+escapeHtml(r.title)+'\"':'')+'>'+r.label+'</button>'\n"
    "      ).join('') + (prov === 'zhipu'\n"
    "        ? '<div style=\"flex:1 1 100%;font-size:11px;color:var(--muted);line-height:1.5;\">'+T('aiCfg.epNote')+'</div>'\n"
    "        : '');\n"
    "      /* 端点按钮与输入框联动：哪个端点当前生效，就把它高亮出来 */\n"
    "      function syncActive(){\n"
    "        const bi = $('aiBaseUrl');\n"
    "        const cur = (bi ? String(bi.value||'').trim() : '').replace(/[/]+$/, '');\n"
    "        cont.querySelectorAll('button[data-url]').forEach(b => {\n"
    "          const on = !!(cur && cur === b.dataset.url);\n"
    "          b.style.fontWeight  = on ? '800' : '';\n"
    "          b.style.borderColor = on ? 'var(--acc,#4f8cff)' : '';\n"
    "          b.style.color       = on ? 'var(--acc,#4f8cff)' : '';\n"
    "        });\n"
    "      }\n"
    "      cont.querySelectorAll('button[data-url]').forEach(b => {\n"
    "        b.onclick = () => { $('aiBaseUrl').value = b.dataset.url; syncActive(); };\n"
    "      });\n"
    "      const bi = $('aiBaseUrl');\n"
    "      if(bi) bi.oninput = syncActive;\n"
    "      syncActive();\n"
)
s = rep(s, old_reg, new_reg, label="R6 REGIONS 增加 zhipu 两组+高亮")

# ------------------------------------------- R7 切 Provider 时先重置 URL 再渲染按钮
old_onchg = (
    "    $('aiProvider').onchange = () => {\n"
    "      const p = $('aiProvider').value;\n"
    "      rerenderModels(p, DEFAULT_MODELS[p] || '');\n"
    "      rerenderRegionBtns(p);\n"
    "      // v1.5：切换 Provider 时自动重置 Base URL 为该 Provider 默认 + 刷新官网按钮\n"
    "      const def = PROVIDER_DEFAULTS[p];\n"
    "      const baseInput = $('aiBaseUrl');\n"
    "      if(baseInput && def){\n"
    "        baseInput.value = def.baseUrl;\n"
    "        baseInput.placeholder = def.baseUrl;\n"
    "      }\n"
    "      const visitBtn = $('aiVisitSite');\n"
    "      if(visitBtn && def){ visitBtn.textContent = '🔗 ' + def.label; }\n"
    "    };\n"
)
new_onchg = (
    "    $('aiProvider').onchange = () => {\n"
    "      const p = $('aiProvider').value;\n"
    "      rerenderModels(p, DEFAULT_MODELS[p] || '');\n"
    "      // v1.5：切换 Provider 时自动重置 Base URL 为该 Provider 默认 + 刷新官网按钮\n"
    "      const def = PROVIDER_DEFAULTS[p];\n"
    "      const baseInput = $('aiBaseUrl');\n"
    "      if(baseInput && def){\n"
    "        baseInput.value = def.baseUrl;\n"
    "        baseInput.placeholder = def.baseUrl;\n"
    "      }\n"
    "      const visitBtn = $('aiVisitSite');\n"
    "      if(visitBtn && def){ visitBtn.textContent = '🔗 ' + def.label; }\n"
    "      // V6.4.19：按钮改到最后渲染，Base URL 已重置完毕，「当前端点」高亮才准确\n"
    "      rerenderRegionBtns(p);\n"
    "    };\n"
)
s = rep(s, old_onchg, new_onchg, label="R7 onchange 渲染顺序调整")

# ------------------------------------------------------------------- 写出产物
open(DST, "w", encoding="utf-8").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 60)

# ① 脚本标签计数：改动前后必须一致（内嵌 HTML 串里的 <script 开标签未转义属正常）
CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script", s))
assert CLOSES1 == CLOSES0, "[FAIL] 脚本收尾标签数变化：%d -> %d" % (CLOSES0, CLOSES1)
assert OPENS1 == OPENS0, "[FAIL] 脚本开标签数变化：%d -> %d" % (OPENS0, OPENS1)
print("OK  脚本标签计数不变 closes=%d opens=%d" % (CLOSES1, OPENS1))

# ② 拆块喂 node --check（浏览器口径）
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
os.makedirs("_chk6419", exist_ok=True)
nchk = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join("_chk6419", "b%02d.js" % i)
    open(p, "w", encoding="utf-8").write(b)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
    nchk += 1
print("OK  JS 语法自检通过 %d 块" % nchk)

# ③ DOM 嵌套体检（只体检面板区，到第一个内联 3D 场景字面量为止）
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parent = {}
        self.err = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if a.get("id"):
            self.parent[a["id"]] = self.stack[-1][0] if self.stack else "<root>"
        cls = a.get("class") or tag
        if tag == "section" and "panel" in (a.get("class") or ""):
            self.parent["<panel:" + (a.get("id") or "?") + ">"] = self.stack[-1][1] if self.stack else "<root>"
        self.stack.append((tag, cls))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.err.append("多余收尾标签 </%s>" % tag)
            return
        if self.stack[-1][0] != tag:
            self.err.append("嵌套不匹配：期望 </%s>，实际 </%s>" % (self.stack[-1][0], tag))
        else:
            self.stack.pop()


cut = s.find("window.__S3D_")
tree = Tree()
tree.feed(s[:cut if cut > 0 else len(s)])
# 截断处必然残留 html/body/script（脚本以 raw text 模式被吞掉），属预期，不算缺陷
residual = [t for t, _ in tree.stack if t not in ("html", "body", "script")]
print("OK  DOM 解析：未匹配收尾标签 %d 个，残留未闭合（已排除截断噪声）%s" % (len(tree.err), residual))
if tree.err:
    print("   ", tree.err[:5])
panels = {k: v for k, v in tree.parent.items() if k.startswith("<panel:")}
bad_panels = {k: v for k, v in panels.items() if not str(v).startswith("wrap")}
print("OK  .panel 总数 %d，父级非 wrap 的 %d 个" % (len(panels), len(bad_panels)))
if bad_panels:
    print("   ", list(bad_panels.items())[:6])
assert len(tree.err) == 0 and len(residual) == 0, "[FAIL] DOM 嵌套体检未通过"
assert len(panels) == 12, "[FAIL] .panel 数 %d != 12" % len(panels)
assert len(bad_panels) == 0, "[FAIL] 有 .panel 掉出 .wrap"

print("-" * 60)
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (SRC, n0, DST, n1, n1 - n0))
