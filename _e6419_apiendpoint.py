# -*- coding: utf-8 -*-
"""V6.4.19 e2e：AI 设置 · 智谱端点切换按钮（套餐额度 / 按量计费）

验收口径（布局）：
  A 硬指标（任何视口 / 任何语言都要过）：不溢出、标签内部不折行、说明提示在按钮行下方、按钮不出视口
  B ≥480px 时两个端点按钮必须落在同一几何行
  C <480px 允许换行，但按钮总宽必须「不劣于既有 MiniMax 按钮」（≤1.1 倍）
     —— MiniMax 的国内/国际按钮是同款组件，实测在 390/360px 下本来就换行，属作品既有行为
"""
import pathlib
from playwright.sync_api import sync_playwright

FILE = "光学交互实验室_AI_v6.4.19.html"
url = pathlib.Path(FILE).resolve().as_uri()
PASS, FAIL = [], []
VIEWPORTS = [(1920, 1080), (1440, 900), (1280, 800), (1100, 820), (900, 760),
             (800, 700), (700, 760), (560, 800), (480, 820), (390, 844), (360, 780)]


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label + (("  <" + str(extra) + ">") if extra and not cond else ""))
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


def clear_masks(pg):
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing');
      });
    }""")


def dismiss_first_run(pg):
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)          # 等入场动画结束，否则元素 not stable
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    clear_masks(pg)


def open_cfg(pg):
    clear_masks(pg)          # 只清别的残留遮罩
    if not pg.is_visible("#setMenu"):
        pg.click("#setBtn"); pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(500)
    # ⚠️ 这里绝不能再 clear_masks：配置弹窗本身也是 .modal-mask.show，会被一起关掉


def geom(pg):
    """按钮几何 + 样式 + 说明提示 + 溢出，全部来自真实渲染"""
    return pg.evaluate("""() => {
      const c = document.getElementById('aiBaseUrlBtns');
      const m = document.querySelector('#aiCfgMask .modal');
      if(!c || !m) return null;
      const cs = getComputedStyle(c);
      const bs = [...c.querySelectorAll('button[data-url]')].map(b=>{
        const r = b.getBoundingClientRect();
        return {t:b.textContent, title:b.title||'', url:b.dataset.url, fw:b.style.fontWeight,
                ws:getComputedStyle(b).whiteSpace, h:Math.round(r.height),
                top:Math.round(r.top), left:Math.round(r.left), right:Math.round(r.right),
                w:Math.round(r.width), vis:r.width>0};
      });
      const vis = bs.filter(b=>b.vis);
      const d = c.querySelector('div:not([data-url])');
      const dr = d ? d.getBoundingClientRect() : null;
      return {
        n: bs.length, visN: vis.length,
        contDisplay: cs.display, contW: Math.round(c.getBoundingClientRect().width),
        gap: parseFloat(cs.gap)||0,
        need: vis.reduce((a,b)=>a+b.w,0) + Math.max(0, vis.length-1)*(parseFloat(cs.gap)||0),
        tops: [...new Set(vis.map(b=>b.top))],
        allNowrap: vis.every(b=>b.ws==='nowrap'),
        inside: vis.every(b=>b.left>=0 && b.right<=window.innerWidth),
        labels: vis.map(b=>b.t), titles: vis.map(b=>b.title), fws: vis.map(b=>b.fw),
        noteText: d ? d.textContent : null,
        noteFlexBasis: d ? getComputedStyle(d).flexBasis : null,
        noteTop: dr ? Math.round(dr.top) : null,
        noteSingleRow: d ? (getComputedStyle(d).flexBasis === '100%') : null,
        sw: m.scrollWidth, cw: m.clientWidth,
        docSw: document.documentElement.scrollWidth, winW: window.innerWidth,
      };
    }""")


def set_lang(pg, target):
    for _ in range(6):
        if pg.evaluate("typeof LANG !== 'undefined' ? LANG : '?'") == target:
            return True
        if not pg.is_visible("#setMenu"):
            if pg.query_selector("#aiCfgMask.show"):
                pg.click("#aiCfgClose"); pg.wait_for_timeout(250)
            pg.click("#setBtn"); pg.wait_for_timeout(220)
        pg.click("#langBtn"); pg.wait_for_timeout(380)
    return pg.evaluate("typeof LANG !== 'undefined' ? LANG : '?'") == target


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    # ⚠️ 顺序要紧：先走真实首启弹窗流程再清遮罩；反过来会把首启弹窗一起关掉（§19②）
    dismiss_first_run(pg)
    clear_masks(pg)

    print("\n[A] 基础健康 + 版本")
    ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "作品自带错误账本为空",
       pg.evaluate("JSON.stringify(window.__rbErrors||[])"))
    ck(not pg.query_selector("#__rbOverlay"), "无启动失败浮层")
    ck(pg.evaluate("window.__APP_READY === true"), "APP_READY 已置真")
    ck(pg.inner_text(".ver-badge").strip() == "v6.4.19", "角标 = v6.4.19", pg.inner_text(".ver-badge"))
    bt = pg.get_attribute(".ver-badge", "title") or ""
    ck("V6.4.19" in bt and "端点" in bt, "角标 title 已更新", bt[:70])
    ck(pg.evaluate("""() => [...document.querySelectorAll('.log-item .log-ver')][0].textContent === 'V6.4.19'"""),
       "更新日志首条 = V6.4.19")
    log1 = pg.evaluate("""() => document.querySelectorAll('.log-item')[0].querySelector('p').textContent""")
    ck(len(log1.strip()) <= 20, "日志文案 ≤20 字", "%s (%d)" % (log1, len(log1.strip())))
    ck(pg.evaluate("""() => { const it=document.querySelectorAll('.log-item')[1];
        return it.querySelector('.log-ver').textContent==='V6.4.18' && !it.classList.contains('cur'); }"""),
       "旧版 V6.4.18 保留且已去掉 cur")
    ck(pg.evaluate("""() => document.querySelectorAll('.log-item.cur').length === 1"""), "cur 标记唯一")
    ck(pg.evaluate("""() => { const ls=[...document.querySelectorAll('.log-item p')].map(e=>e.textContent);
        return ls.length >= 5; }"""), "更新日志其它条目仍在")

    print("\n[B] 回归基线")
    ck(pg.evaluate("""() => document.querySelectorAll('.tab-btn').length === 11"""), ".tab-btn = 11")
    ck(pg.evaluate("""() => document.querySelectorAll('.panel').length === 12"""), ".panel = 12")
    ck(pg.evaluate("""() => document.querySelectorAll('canvas').length === 11"""), "canvas = 11")
    ck(pg.evaluate("""() => typeof MODULES === 'object' && typeof REPORT === 'object' && typeof S3D === 'object'"""),
       "MODULES / REPORT / S3D 仍在")

    print("\n[C] 智谱端点按钮")
    open_cfg(pg)
    ck(pg.is_visible("#aiProvider") and pg.is_visible("#aiBaseUrl"), "配置弹窗已打开")
    pg.select_option("#aiProvider", "zhipu")
    pg.wait_for_timeout(350)
    g = geom(pg)
    ck(g["visN"] == 2, "智谱下显示 2 个端点按钮", g["visN"])
    ck("套餐额度" in g["labels"][0] and "按量计费" in g["labels"][1], "按钮文案正确", g["labels"])
    ck(g["titles"][0] == "GLM Coding Plan 套餐专属端点：https://open.bigmodel.cn/api/coding/paas/v4/chat/completions",
       "套餐按钮 title = 完整套餐端点", g["titles"][0])
    ck(g["titles"][1] == "按量计费通用端点：https://open.bigmodel.cn/api/paas/v4/chat/completions",
       "按量按钮 title = 完整通用端点", g["titles"][1])
    ck(g["noteText"] and "GLM Coding Plan" in g["noteText"] and "1113" in g["noteText"],
       "有端点说明提示（含 1113 余额不足）", g["noteText"])
    ck(g["noteSingleRow"] and g["noteTop"] >= max(g["tops"]), "说明提示独占一行且在按钮行下方")
    base0 = pg.input_value("#aiBaseUrl")
    ck(base0 == "https://open.bigmodel.cn/api/paas/v4", "智谱默认仍是按量端点", base0)
    ck(g["fws"][1] == "800" and g["fws"][0] != "800", "默认高亮在「按量计费」", g["fws"])

    pg.click("#aiBaseUrlBtns button[data-url='https://open.bigmodel.cn/api/coding/paas/v4']")
    pg.wait_for_timeout(250)
    base1 = pg.input_value("#aiBaseUrl"); g2 = geom(pg)
    ck(base1 == "https://open.bigmodel.cn/api/coding/paas/v4", "点「套餐额度」填入套餐端点", base1)
    ck(g2["fws"][0] == "800" and g2["fws"][1] != "800", "高亮切到「套餐额度」", g2["fws"])

    pg.fill("#aiBaseUrl", "https://x.example/v1"); pg.wait_for_timeout(200)
    ck(all(x != "800" for x in geom(pg)["fws"]), "自定义 URL 时两个按钮都不高亮")
    pg.fill("#aiBaseUrl", "https://open.bigmodel.cn/api/paas/v4/"); pg.wait_for_timeout(200)
    ck(geom(pg)["fws"][1] == "800", "带尾斜杠也能识别为「按量计费」")

    print("\n[D] 保存落盘 + 其它 Provider 回归")
    pg.click("#aiBaseUrlBtns button[data-url='https://open.bigmodel.cn/api/coding/paas/v4']")
    pg.wait_for_timeout(150)
    pg.fill("#aiKey", "sk-e2e-dummy")
    pg.evaluate("() => { window.alert = () => {}; }")
    pg.click("#aiCfgSave"); pg.wait_for_timeout(300)
    saved = pg.evaluate("""() => { for (const k of Object.keys(localStorage)) {
        if(k.endsWith('_cfg')) { try { const o=JSON.parse(localStorage.getItem(k));
        if(o.provider==='zhipu') return o; }catch(e){} } } return null; }""")
    ck(saved and saved["baseUrl"] == "https://open.bigmodel.cn/api/coding/paas/v4",
       "保存后 cfg.baseUrl = 套餐端点", saved and saved.get("baseUrl"))
    ck(saved and saved.get("model"), "model 也已保存", saved and saved.get("model"))

    pg.select_option("#aiProvider", "minimax"); pg.wait_for_timeout(300)
    m = geom(pg)
    ck(m["visN"] == 2 and "国内" in m["labels"][0] and "国际" in m["labels"][1],
       "MiniMax 国内/国际按钮逐字未动", m["labels"])
    ck(m["noteText"] is None, "MiniMax 不该出现智谱端点说明")
    ck(pg.input_value("#aiBaseUrl") == "https://api.minimaxi.com/v1", "MiniMax 仍默认国内端点")
    pg.select_option("#aiProvider", "kimi"); pg.wait_for_timeout(250)
    k = geom(pg)
    ck(k["visN"] == 2 and "国内" in k["labels"][0], "Kimi 区域按钮逐字未动", k["labels"])
    pg.select_option("#aiProvider", "deepseek"); pg.wait_for_timeout(250)
    d = geom(pg)
    ck(d["contDisplay"] == "none" and d["visN"] == 0, "DeepSeek 无端点按钮（容器隐藏）", d["contDisplay"])
    pg.select_option("#aiProvider", "zhipu"); pg.wait_for_timeout(300)
    z = geom(pg)
    ck(z["visN"] == 2 and z["fws"][1] == "800", "切回智谱：端点回落并正确高亮", z["fws"])

    print("\n[E] 多视口布局（中文）")
    for w, h in VIEWPORTS:
        pg.set_viewport_size({"width": w, "height": h}); pg.wait_for_timeout(240)
        g = geom(pg)
        rows = len(g["tops"])
        ck(g["allNowrap"], "%dpx 按钮标签内部不折行" % w)
        ck(g["inside"], "%dpx 按钮不出视口" % w, g["labels"])
        ck(g["noteTop"] >= max(g["tops"]), "%dpx 说明提示在按钮行下方" % w)
        ck(g["sw"] <= g["cw"] + 1, "%dpx 弹窗无横向溢出" % w, (g["sw"], g["cw"]))
        ck(g["docSw"] <= w + 1, "%dpx 页面无横向溢出" % w, (g["docSw"], w))
        if w >= 480:
            ck(rows == 1, "%dpx 两个端点按钮同一几何行（容器够宽）" % w, g["tops"])
        else:
            # 窄屏允许换行，但必须不劣于既有 MiniMax 按钮
            zhipu_need = g["need"]
            pg.select_option("#aiProvider", "minimax"); pg.wait_for_timeout(260)
            mm_need = geom(pg)["need"]
            pg.select_option("#aiProvider", "zhipu"); pg.wait_for_timeout(260)
            ck(zhipu_need <= mm_need * 1.1,
               "%dpx 窄屏换行=作品既有行为，且智谱按钮不劣于 MiniMax（%d vs %d）" % (w, zhipu_need, mm_need))

    print("\n[F] 三语词条 + 各语言布局")
    for lang, ep_plan, ep_payg, note_key in [
            ("en", "Plan quota", "Pay-as-you-go", "Zhipu has two endpoints"),
            ("zht", "套餐額度", "按量計費", "智譜分兩套端點"),
            ("zh", "套餐额度", "按量计费", "智谱分两套端点")]:
        ck(set_lang(pg, lang), "已切到语言 %s" % lang)
        if not pg.query_selector("#aiCfgMask.show"):
            open_cfg(pg)
        pg.select_option("#aiProvider", "zhipu"); pg.wait_for_timeout(320)
        for w in (1440, 560, 390):
            pg.set_viewport_size({"width": w, "height": 860}); pg.wait_for_timeout(240)
            tt = geom(pg)
            ck(ep_plan in tt["labels"][0] and ep_payg in tt["labels"][1],
               "%s @%dpx 按钮已本地化" % (lang, w), tt["labels"])
            ck(tt["allNowrap"] and tt["inside"] and tt["sw"] <= tt["cw"] + 1 and tt["docSw"] <= w + 1,
               "%s @%dpx 无溢出/不折行" % (lang, w), (tt["sw"], tt["cw"], tt["docSw"]))
            ck(tt["noteTop"] >= max(tt["tops"]), "%s @%dpx 说明提示在按钮行下方" % (lang, w))
            if w >= 480:
                ck(len(tt["tops"]) == 1, "%s @%dpx 同一几何行" % (lang, w), tt["tops"])
        tt = geom(pg)
        ck(note_key in (tt["noteText"] or ""), "%s 说明提示已本地化" % lang, tt["noteText"])
        ck("GLM Coding Plan" in tt["titles"][0] and "chat/completions" in tt["titles"][0],
           "%s 套餐按钮 title 已本地化" % lang, tt["titles"][0])
        if lang == "zh":
            ck("套餐" in tt["titles"][0], "中文 title 已本地化")
        if lang != "zh":
            pg.click("#aiCfgClose"); pg.wait_for_timeout(280)
    ck(pg.evaluate("typeof LANG !== 'undefined' ? LANG : '?'") == "zh", "回到中文")
    pg.set_viewport_size({"width": 1440, "height": 900}); pg.wait_for_timeout(200)

    print("\n[G] 控制台噪声")
    noise = [e for e in errs if not any(x in e for x in
             ("Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "favicon"))]
    ck(len(noise) == 0, "无真实控制台错误", noise[:3])
    ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "全程结束后错误账本仍为空")
    ck(pg.evaluate("window.__APP_READY === true"), "结尾 APP_READY 仍为真")

    b.close()

print("\n" + "=" * 62)
print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 62)
