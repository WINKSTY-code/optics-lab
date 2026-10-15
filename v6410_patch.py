# -*- coding: utf-8 -*-
"""V6.4.10 补丁
① 「AI 设置」弹窗：「前往官网」右侧新增「配置指南」按钮，点开是一份面向
   第一次使用、不知道去哪拿 API Key 的用户的简明教程（内联面板，不另开弹窗）。
② 「关于」弹窗：作者署名下补一行单位署名「」——
   刻意不挂 data-i18n（姓名与单位不随语言切换），格式与下方正文各 <p> 一致。
③ 版本号四处同步 + 更新日志新增一条（≤20 字）。
"""
import os, re

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.9.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.10.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, "r", encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)
closes0 = len(re.findall(r"</script(?=[\s>/])", s))
opens0 = len(re.findall(r"<script(?=[\s>/])", s))
V649_BEFORE = s.count("V6.4.9")

# ============================================================
# ① CSS：配置指南内联面板
# ============================================================
s = rep(s,
        "  .ai-config .row button{flex:1;min-width:90px;}\n",
        "  .ai-config .row button{flex:1;min-width:90px;}\n"
        "  /* V6.4.10：「配置指南」内联面板 —— 首次配置 API Key 的简明教程。\n"
        "     [hidden] 显式兜底：本文件里已有 grid/flex 提权把 [hidden] 压过的先例，这里预先写死。 */\n"
        "  .ai-guide{margin-top:8px;padding:10px 12px;border:var(--hard-border);border-radius:8px;background:var(--cvbg);color:var(--txt);font-size:12px;line-height:1.65;}\n"
        "  .ai-guide[hidden]{display:none;}\n"
        "  .ai-guide-h{font-weight:700;margin-bottom:4px;}\n"
        "  .ai-guide-steps{margin:0;padding-left:1.4em;}\n"
        "  .ai-guide-steps li{margin:2px 0;}\n"
        "  .ai-guide-faq{margin-top:7px;padding-top:7px;border-top:1px dashed var(--muted2);color:var(--muted);}\n"
        "  .ai-guide-faq div{margin:1px 0;}\n",
        1, "① CSS：.ai-guide 内联面板样式")

# ============================================================
# ② i18n：9 条词条（三语）
# ============================================================
s = rep(s,
        "'aiCfg.goSite':   {zh:'前往官网', zht:'前往官網', en:'Visit site'},",
        "'aiCfg.goSite':   {zh:'前往官网', zht:'前往官網', en:'Visit site'},\n"
        "'aiCfg.guide':    {zh:'📖 配置指南', zht:'📖 設定指南', en:'📖 Setup guide'},\n"
        "'aiCfg.gTitle':   {zh:'三步搞定（首次约 2 分钟）', zht:'三步搞定（首次約 2 分鐘）', en:'Three steps (about 2 minutes)'},\n"
        "'aiCfg.g1':       {zh:'选平台：把上面的 Provider 从「离线（仅 TTS）」换成「智谱 GLM ⭐ 推荐」。', zht:'選平台：把上面的 Provider 從「離線（僅 TTS）」換成「智譜 GLM ⭐ 推薦」。', en:'Pick a provider — switch Provider from “Offline (TTS only)” to “Zhipu GLM ⭐”.'},\n"
        "'aiCfg.g2':       {zh:'拿 Key：先在①选好平台，再点上面的「前往官网」注册登录 → 控制台新建 API Key → 复制。', zht:'拿 Key：先在①選好平台，再點上面的「前往官網」註冊登入 → 控制台新建 API Key → 複製。', en:'Get a key — pick a provider in ①, then click “Visit site” above, sign up, create an API key, copy it.'},\n"
        "'aiCfg.g3':       {zh:'填进来：把 Key 粘到上方「API Key」框 → 点「保存」→ 点「测试」，出现 ✅ 就成功了。', zht:'填進來：把 Key 貼到上方「API Key」框 → 點「儲存」→ 點「測試」，出現 ✅ 就成功了。', en:'Paste it into the “API Key” field above → Save → Test; a ✅ means you are set.'},\n"
        "'aiCfg.gFaqTitle':{zh:'💡 常见问题', zht:'💡 常見問題', en:'💡 FAQ'},\n"
        "'aiCfg.gFaq1':    {zh:'· 换平台后模型列表会自动切换；没有想要的模型可选「— 自定义 —」手填。', zht:'· 換平台後模型清單會自動切換；沒有想要的模型可選「— 自訂 —」手填。', en:'· The model list follows the provider; pick “— Custom —” to type your own.'},\n"
        "'aiCfg.gFaq2':    {zh:'· 报 401：Key 与站点区域不匹配，换成同一区域的 Base URL 再试。', zht:'· 報 401：Key 與站點區域不匹配，換成同一區域的 Base URL 再試。', en:'· Error 401: the key and the endpoint region differ — use the matching Base URL.'},\n"
        "'aiCfg.gFaq3':    {zh:'· 提示「未配置」：Provider 还停在「离线（仅 TTS）」，选一个平台即可。', zht:'· 提示「未設定」：Provider 還停在「離線（僅 TTS）」，選一個平台即可。', en:'· “Not configured” means the provider is still “Offline (TTS only)”.'},\n"
        "'aiCfg.gFaq4':    {zh:'· 只要语音朗读：选「离线（仅 TTS）」，不填 Key 也能正常使用。', zht:'· 只要語音朗讀：選「離線（僅 TTS）」，不填 Key 也能正常使用。', en:'· Need speech only? Choose “Offline (TTS only)” — no key required.'},",
        1, "② i18n：新增 10 条配置指南词条（三语）")

# ============================================================
# ③ JS：指南内容生成函数（插在 openConfig 之前）
# ============================================================
s = rep(s,
        "  function openConfig(){",
        "  /* V6.4.10：「配置指南」——给第一次使用、不知道去哪拿 API Key 的用户看的简明教程。\n"
        "     刻意内联在同一张配置弹窗里，而不是再开一层弹窗：\n"
        "     ① 不新增遮罩容器（closeModal 只认 #aiCfgMask）；\n"
        "     ② 用户已经填了一半的 Provider / Key 不会因为重渲染 innerHTML 而丢失。 */\n"
        "  function aiGuideHtml(){\n"
        "    const steps = [T('aiCfg.g1'), T('aiCfg.g2'), T('aiCfg.g3')];\n"
        "    return '<div class=\"ai-guide-h\">' + T('aiCfg.gTitle') + '</div>' +\n"
        "      '<ol class=\"ai-guide-steps\">' + steps.map(function(x){ return '<li>' + x + '</li>'; }).join('') + '</ol>' +\n"
        "      '<div class=\"ai-guide-faq\">' +\n"
        "        '<div>' + T('aiCfg.gFaqTitle') + '</div>' +\n"
        "        '<div>' + T('aiCfg.gFaq1') + '</div>' +\n"
        "        '<div>' + T('aiCfg.gFaq2') + '</div>' +\n"
        "        '<div>' + T('aiCfg.gFaq3') + '</div>' +\n"
        "        '<div>' + T('aiCfg.gFaq4') + '</div>' +\n"
        "      '</div>';\n"
        "  }\n\n"
        "  function openConfig(){",
        1, "③ JS：新增 aiGuideHtml()")

# ============================================================
# ④ JS：按钮 + 面板进 DOM（紧挨「前往官网」右侧）
# ============================================================
OLD_ROW = ("      '<div style=\"display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;\">"
           "<button type=\"button\" id=\"aiVisitSite\" class=\"sec\" style=\"padding:6px 12px;font-size:12px;\">🔗 '"
           "+(PROVIDER_DEFAULTS[curProv]?.label || T('aiCfg.goSite'))+'</button></div>'+\n"
           "      '<div id=\"aiTokenInfo\"")

NEW_ROW = ("      '<div style=\"display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;\">"
           "<button type=\"button\" id=\"aiVisitSite\" class=\"sec\" style=\"padding:6px 12px;font-size:12px;\">🔗 '"
           "+(PROVIDER_DEFAULTS[curProv]?.label || T('aiCfg.goSite'))+'</button>'+\n"
           "        '<button type=\"button\" id=\"aiGuideBtn\" class=\"sec\" style=\"padding:6px 12px;font-size:12px;white-space:nowrap;\" "
           "aria-expanded=\"false\" aria-controls=\"aiGuidePanel\">'+T('aiCfg.guide')+'</button></div>'+\n"
           "      '<div id=\"aiGuidePanel\" class=\"ai-guide\" hidden>'+aiGuideHtml()+'</div>'+\n"
           "      '<div id=\"aiTokenInfo\"")

s = rep(s, OLD_ROW, NEW_ROW, 1, "④ DOM：配置指南按钮 + 指南面板")

# ============================================================
# ⑤ JS：展开 / 收起
# ============================================================
s = rep(s,
        "    $('aiVisitSite').onclick = () => { const def = PROVIDER_DEFAULTS[$('aiProvider').value]; "
        "if(def && def.url) window.open(def.url, '_blank'); };",
        "    $('aiVisitSite').onclick = () => { const def = PROVIDER_DEFAULTS[$('aiProvider').value]; "
        "if(def && def.url) window.open(def.url, '_blank'); };\n"
        "    /* V6.4.10：配置指南展开 / 收起（默认收起，不打扰已经会用的用户） */\n"
        "    $('aiGuideBtn').onclick = () => {\n"
        "      const box = $('aiGuidePanel'), btn = $('aiGuideBtn');\n"
        "      if(!box || !btn) return;\n"
        "      const open = !!box.hidden;\n"
        "      box.hidden = !open;\n"
        "      btn.setAttribute('aria-expanded', open ? 'true' : 'false');\n"
        "    };",
        1, "⑤ JS：配置指南展开/收起")

# ============================================================
# ⑥ 关于弹窗：署名单位一行
# ============================================================
s = rep(s,
        '    <h2 id="aboutTitle" class="wv-title" data-i18n="about.title">作者：WINKSTY</h2>\n'
        '    <p id="aboutSub" class="about-sub wv-sub" data-i18n="about.sub">苏科版2024新教材 · 初中物理</p>\n',
        '    <h2 id="aboutTitle" class="wv-title" data-i18n="about.title">作者：WINKSTY</h2>\n'
        '    <!-- V6.4.10：署名单位。刻意不挂 data-i18n —— 姓名与单位不随语言切换改写，\n'
        '         也因此不会被 applyLang() 覆写；格式与下方正文各 <p> 完全一致。 -->\n'
        '    \n'
        '    <p id="aboutSub" class="about-sub wv-sub" data-i18n="about.sub">苏科版2024新教材 · 初中物理</p>\n',
        1, "⑥ 关于弹窗：作者署名下补单位署名")

# ============================================================
# ⑦ 版本号四处同步 + 更新日志
# ============================================================
s = rep(s, "var BUILD = 'v6.4.9'", "var BUILD = 'v6.4.10'", 1, "版本：BUILD")
s = rep(s, "    return 'v6.4.9';", "    return 'v6.4.10';", 1, "版本：报告兜底 RPT_BUILD")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.9 · 直线传播调节栏移到画布下，物体颜色可调。">v6.4.9</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.10 · AI设置新增配置指南，教新手一步步填好Key。">v6.4.10</div>',
        1, "版本：右下角角标（title + 文本）")
s = rep(s,
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.9</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>直线传播调节栏移下，物体颜色可调。</p>\n'
        '      </div>',
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.10</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>AI设置新增配置指南按钮。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.9</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>直线传播调节栏移下，物体颜色可调。</p>\n'
        '      </div>',
        1, "更新日志：插入 V6.4.10 首条")

# ============================================================
# 硬校验
# ============================================================
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
opens1 = len(re.findall(r"<script(?=[\s>/])", s))
assert closes1 == closes0, "[FAIL] 脚本收尾标签字面量数变了: %d -> %d" % (closes0, closes1)
assert opens1 == opens0, "[FAIL] 脚本开标签数变了: %d -> %d" % (opens0, opens1)
assert s.count("v6.4.9") == 0, "[FAIL] 小写 v6.4.9 残留: %d" % s.count("v6.4.9")
assert s.count("v6.4.10") == 3, "[FAIL] 小写 v6.4.10 应为 3 处，实际 %d" % s.count("v6.4.10")
assert s.count("V6.4.10") == 6, "[FAIL] 大写 V6.4.10 应为 6 处（4 注释 + 更新日志 + 角标 title），实际 %d" % s.count("V6.4.10")
assert s.count("V6.4.9") == V649_BEFORE - 1, "[FAIL] V6.4.9 注释数异常: %d -> %d" % (V649_BEFORE, s.count("V6.4.9"))
assert s.count("aiGuideBtn") == 3, "[FAIL] aiGuideBtn 应为 3 处（DOM id + onclick + 取值），实际 %d" % s.count("aiGuideBtn")
assert s.count("aiGuidePanel") == 3, "[FAIL] aiGuidePanel 应为 3 处（id + aria-controls + JS 选择器），实际 %d" % s.count("aiGuidePanel")
assert s.count("aiGuideHtml") == 2, "[FAIL] aiGuideHtml 应为 2 处，实际 %d" % s.count("aiGuideHtml")
assert s.count("") == 1, "[FAIL] 署名单位行异常"
# 更新日志正文不超过 20 字（仅统计该条 <p> 内含中英数字符）
_log = re.search(r'<span class="log-ver">V6\.4\.10</span>.*?<p>(.*?)</p>', s, re.S)
assert _log, "[FAIL] 未能取到 V6.4.10 更新日志正文"
assert len(_log.group(1)) <= 20, "[FAIL] 更新日志 %d 字 > 20: %s" % (len(_log.group(1)), _log.group(1))
LOG.append("OK  %-52s %s" % ("更新日志字数", "%d 字：%s" % (len(_log.group(1)), _log.group(1))))

# ---- DOM 嵌套体检（硬门，见 skill §28）----
import importlib.util
_spec = importlib.util.spec_from_file_location("v649s", os.path.join(BASE, "v649_structure.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_t = _mod.Tree()
_t.feed(s[:s.find('window.__S3D_LENS__')])
_bad = [(p, par) for p, par in _t.section_parents if par != ".wrap"]
assert len(_t.section_parents) == 12, "[FAIL] .panel 数量应为 12，实际 %d" % len(_t.section_parents)
assert not _bad, "[FAIL] 有面板掉出 .wrap：%s" % _bad
assert not _t.errors, "[FAIL] 未匹配收尾标签：%s" % _t.errors[:5]
assert s.count("") == 1
LOG.append("OK  %-52s %s" % ("DOM 嵌套体检", "12 个面板父级均为 .wrap；未匹配收尾标签 0 个"))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 66)
print("脚本标签：opens %d -> %d, closes %d -> %d" % (opens0, opens1, closes0, closes1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
