# -*- coding: utf-8 -*-
"""V6.4.10 端到端（真实 Chromium / file://）
① AI 设置：「前往官网」右侧的「配置指南」按钮可见、可点、展开/收起正常、内容对；
② 关于弹窗：作者署名下已补「」，位置与格式正确、语言切换后不变；
③ 更新日志首条 / 角标 / 版本号；
④ 多档视口复扫 + 全量回归（11 tab / 12 panel / 11 canvas / 无错误账本）。
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.10.html").resolve().as_uri()

PASS, FAIL = [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)


def clear_masks(pg):
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")


def dismiss_first_run(pg):
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.fill("#stuName", "E2E测试")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(700)
    except Exception:
        pass
    clear_masks(pg)


def open_menu(pg):
    """确保「设置」下拉是展开的（#langBtn / #aiCfgBtn 都在里面）"""
    clear_masks(pg)
    if pg.evaluate("document.getElementById('setMenu').hidden"):
        pg.click("#setBtn")
        pg.wait_for_timeout(250)


def open_ai_cfg(pg):
    """打开设置下拉 → 点 AI 设置"""
    open_menu(pg)
    pg.click("#aiCfgBtn")
    pg.wait_for_timeout(350)


def set_lang(pg, target):
    """循环点 #langBtn 直到 LANG == target（zh -> zht -> en -> zh，勿写死点击次数）"""
    for _ in range(5):
        if pg.evaluate("LANG") == target:
            return True
        open_menu(pg)
        pg.click("#langBtn")
        pg.wait_for_timeout(400)
    return pg.evaluate("LANG") == target


GUIDE_MEASURE = r"""() => {
  const q = s => document.querySelector(s);
  const R = e => e ? e.getBoundingClientRect() : null;
  const modal = q('#aiCfgMask .modal');
  const v = q('#aiVisitSite'), g = q('#aiGuideBtn'), p = q('#aiGuidePanel');
  const row = v && v.parentNode;
  const vis = e => { const r = R(e); return !!(r && r.width > 0 && r.height > 0); };
  const items = [v, g].filter(vis).map(e => R(e));
  const tops = [...new Set(items.map(r => Math.round(r.top)))];
  const mr = R(modal);
  return {
    hasVisit: !!v, hasGuide: !!g, hasPanel: !!p,
    visitVis: vis(v), guideVis: vis(g), panelVis: vis(p),
    guideText: g ? g.textContent.trim() : '',
    guideAria: g ? g.getAttribute('aria-expanded') : null,
    panelText: p ? p.textContent.replace(/\s+/g,' ').trim() : '',
    panelHidden: p ? p.hidden : null,
    sameRow: tops.length === 1,
    rowGap: items.length === 2 ? +(items[1].left - items[0].right).toFixed(1) : null,
    guideRightOfVisit: items.length === 2 && items[1].left >= items[0].left,
    panelTopBelowRow: (() => { const pr = R(p), rr = R(row);
        return (pr && rr) ? +(pr.top - rr.bottom).toFixed(1) : null; })(),
    overflowX: modal ? +(modal.scrollWidth - modal.clientWidth).toFixed(1) : null,
    modalW: mr ? +mr.width.toFixed(1) : null,
    liCount: p ? p.querySelectorAll('.ai-guide-steps li').length : 0,
    hasSteps: p ? !!p.querySelector('.ai-guide-steps') : false,
    hasFaq: p ? !!p.querySelector('.ai-guide-faq') : false,
    vw: window.innerWidth
  };
}"""

ABOUT_MEASURE = r"""() => {
  const modal = document.querySelector('#aboutMask .modal');
  const kids = [...modal.children].map(e => ({tag: e.tagName, id: e.id || '', txt: (e.textContent||'').trim()}));
  const p = [...modal.querySelectorAll(':scope > p')].find(e => e.textContent.indexOf('') >= 0);
  // 参照物：同为「不挂 data-i18n 的纯正文 <p>」——邮箱那行（署名行应与之逐项同款）
  const ref = [...modal.querySelectorAll(':scope > p')].find(e => e.textContent.indexOf('winksty@qq.com') >= 0);
  const r = p ? p.getBoundingClientRect() : null;
  const cs = p ? getComputedStyle(p) : null;
  const rs = ref ? getComputedStyle(ref) : null;
  return {
    kids: kids,
    idx: kids.findIndex(k => k.txt.indexOf('') >= 0),
    idxH2: kids.findIndex(k => k.tag === 'H2'),
    idxSub: kids.findIndex(k => k.id === 'aboutSub'),
    tag: p ? p.tagName : null,
    cls: p ? (p.className || '') : null,
    refCls: ref ? (ref.className || '') : null,
    hasI18nAttr: p ? p.hasAttribute('data-i18n') : null,
    ariaLabel: p ? p.getAttribute('aria-label') : null,
    text: p ? p.textContent.trim() : null,
    fontSize: cs ? cs.fontSize : null,
    color: cs ? cs.color : null,
    fontWeight: cs ? cs.fontWeight : null,
    refFontSize: rs ? rs.fontSize : null,
    refColor: rs ? rs.color : null,
    refFontWeight: rs ? rs.fontWeight : null,
    visible: !!(r && r.width > 0 && r.height > 0),
    overflowX: +(modal.scrollWidth - modal.clientWidth).toFixed(1)
  };
}"""

REG = r"""() => ({
  tabs: document.querySelectorAll('.tab-btn').length,
  panels: document.querySelectorAll('.panel').length,
  canvases: document.querySelectorAll('canvas').length,
  badge: (document.querySelector('.ver-badge') || {}).textContent,
  rbErrors: (window.__rbErrors || []).length,
  overlay: !!document.getElementById('__rbOverlay'),
  ready: !!window.__APP_READY,
  modules: typeof MODULES === 'object' && typeof REPORT === 'object' && typeof S3D === 'object',
  logFirst: (() => { const it = document.querySelector('.log-list .log-item .log-ver');
                     return it ? it.textContent.trim() : null; })(),
  logFirstTxt: (() => { const it = document.querySelector('.log-list .log-item p');
                        return it ? it.textContent.trim() : null; })(),
  logFirstDate: (() => { const it = document.querySelector('.log-list .log-item .log-date');
                         return it ? it.textContent.trim() : null; })()
})"""

VIEWPORTS = [(1920, 900), (1600, 900), (1440, 900), (1280, 800), (1100, 800),
             (1024, 800), (900, 800), (768, 800), (480, 800), (390, 780)]

NOISE = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED",
         "ERR_ABORTED", "cdn.jsdelivr.net", "fonts.googleapis.com")


def main():
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        dismiss_first_run(pg)

        print("\n== 0. 页面健康 ==")
        reg = pg.evaluate(REG)
        noisy = [e for e in errs if not any(n in e for n in NOISE)]
        ck(reg["rbErrors"] == 0, "自带错误账本 __rbErrors == 0（实际 %s）" % reg["rbErrors"])
        ck(not reg["overlay"], "启动失败浮层 #__rbOverlay 不存在")
        ck(not noisy, "控制台无（非 CDN 噪声）错误：%s" % noisy[:3])
        ck(reg["badge"] == "v6.4.10", "右下角角标 == v6.4.10（实际 %s）" % reg["badge"])

        print("\n== 1. AI 设置：「前往官网」右侧新增「配置指南」 ==")
        open_ai_cfg(pg)
        ck(pg.is_visible("#aiCfgMask"), "AI 设置弹窗已打开")
        m = pg.evaluate(GUIDE_MEASURE)
        ck(m["hasVisit"] and m["hasGuide"] and m["hasPanel"], "三要素齐备（前往官网 / 配置指南 / 指南面板）")
        ck(m["visitVis"] and m["guideVis"], "前往官网与配置指南按钮均可见")
        ck(m["panelHidden"] is True and not m["panelVis"], "指南默认收起（不打扰已会用的用户）")
        ck(m["guideRightOfVisit"], "「配置指南」位于「前往官网」右侧（left 更大）")
        ck(m["sameRow"], "两个按钮在同一几何行（未被挤出/换行）")
        ck(m["rowGap"] is not None and 2 <= m["rowGap"] <= 40,
           "两按钮间距 %.1fpx（设计 gap 6px，同排）" % (m["rowGap"] or -1))
        ck(m["guideAria"] == "false", "初始 aria-expanded = false")
        ck(m["overflowX"] is not None and m["overflowX"] <= 1,
           "弹窗无横向溢出（scrollWidth-clientWidth = %s）" % m["overflowX"])

        print("\n== 1b. 点开「配置指南」→ 教程内容 ==")
        pg.click("#aiGuideBtn")
        pg.wait_for_timeout(300)
        m = pg.evaluate(GUIDE_MEASURE)
        ck(m["panelVis"], "点开后指南面板可见")
        ck(m["guideAria"] == "true", "aria-expanded 置为 true")
        ck(m["panelTopBelowRow"] is not None and m["panelTopBelowRow"] >= 0,
           "面板位于按钮行正下方（+%.1fpx）" % (m["panelTopBelowRow"] or -1))
        ck(m["panelText"].find("三步") >= 0, "指南含「三步搞定」标题")
        ck(m["panelText"].find("前往官网") >= 0, "指南第②步指向「前往官网」")
        ck(m["panelText"].find("保存") >= 0 and m["panelText"].find("测试") >= 0,
           "指南第③步给出「保存 → 测试」闭环")
        ck(m["panelText"].find("智谱") >= 0, "指南第①步推荐智谱 GLM")
        ck(m["panelText"].find("离线") >= 0 and m["panelText"].find("Provider") >= 0,
           "指南第①步点明先把 Provider 从「离线」换掉（否则前往官网无目标）")
        ck(m["panelText"].find("先在①") >= 0 or m["panelText"].find("先在①选好平台") >= 0,
           "指南第②步点明「先选平台再点前往官网」的顺序依赖")
        ck(m["panelText"].find("401") >= 0 and m["panelText"].find("Base URL") >= 0, "指南含 401 排查提示")
        ck(m["panelText"].find("离线") >= 0, "指南含「离线（仅 TTS）」说明")
        ck(m["liCount"] == 3 and m["hasSteps"], "三步以 <ol> 呈现（实际 %d 项）" % m["liCount"])
        ck(m["hasFaq"], "常见问题区块存在")
        ck(m["overflowX"] <= 1, "展开后弹窗仍无横向溢出（%s）" % m["overflowX"])

        print("\n== 2. 展开 / 收起交互 ==")
        pg.click("#aiGuideBtn")
        pg.wait_for_timeout(250)
        ck(not pg.is_visible("#aiGuidePanel"), "再点一次 → 面板收起")
        ck(pg.get_attribute("#aiGuideBtn", "aria-expanded") == "false", "aria-expanded = false")
        pg.click("#aiGuideBtn")
        pg.wait_for_timeout(250)
        ck(pg.is_visible("#aiGuidePanel"), "再点一次 → 面板重新展开")
        ck(pg.get_attribute("#aiGuideBtn", "aria-expanded") == "true", "aria-expanded = true")
        ck(pg.is_visible("#aiProvider"), "配置表单未被指南面板破坏（Provider 下拉仍在）")

        print("\n== 3. 三语切换 ==")
        ck(set_lang(pg, "zht"), "切到繁體（LANG=%s）" % pg.evaluate("LANG"))
        open_ai_cfg(pg)
        mz = pg.evaluate(GUIDE_MEASURE)
        ck("設定指南" in mz["guideText"], "繁體下按钮文案跟随（%s）" % mz["guideText"])
        ck(set_lang(pg, "en"), "切到 EN（LANG=%s）" % pg.evaluate("LANG"))
        open_ai_cfg(pg)
        m2 = pg.evaluate(GUIDE_MEASURE)
        ck("Setup guide" in m2["guideText"], "EN 下按钮文案跟随（%s）" % m2["guideText"])
        ck("Three steps" in m2["panelText"], "EN 下教程文案跟随（首段：%s）" % m2["panelText"][:44])
        ck(set_lang(pg, "zh"), "切回中文（LANG=%s）" % pg.evaluate("LANG"))
        open_ai_cfg(pg)
        m3 = pg.evaluate(GUIDE_MEASURE)
        ck("配置指南" in m3["guideText"], "中文下按钮文案正确（%s）" % m3["guideText"])

        print("\n== 4. 「关于」弹窗：作者署名下补单位署名 ==")
        clear_masks(pg)
        pg.click("#signBtn")
        pg.wait_for_timeout(500)
        ck(pg.is_visible("#aboutMask"), "关于弹窗已打开")
        a = pg.evaluate(ABOUT_MEASURE)
        ck(a["text"] == "", "署名文本正确：%s" % a["text"])
        ck(a["idx"] == a["idxH2"] + 1, "署名行紧跟在「作者：WINKSTY」下一行（idx %s vs %s）" % (a["idx"], a["idxH2"]))
        ck(a["idx"] < a["idxSub"], "署名行位于「苏科版2024新教材」之前")
        ck(a["tag"] == "P", "使用 <p> 标签")
        ck(a["hasI18nAttr"] is False, "不挂 data-i18n（姓名/单位不随语言切换、不被 applyLang 覆写）")
        ck(a["cls"] == a["refCls"], "class 与同为纯正文的邮箱行一致（%s vs %s，无额外样式类）" % (a["cls"], a["refCls"]))
        ck(a["fontSize"] == a["refFontSize"], "字号与正文一致（%s vs %s）" % (a["fontSize"], a["refFontSize"]))
        ck(a["color"] == a["refColor"], "字色与正文一致（%s vs %s）" % (a["color"], a["refColor"]))
        ck(a["fontWeight"] == a["refFontWeight"], "字重与正文一致（%s vs %s）" % (a["fontWeight"], a["refFontWeight"]))
        ck(a["visible"], "署名行可见")
        ck(a["overflowX"] <= 1, "关于弹窗无横向溢出（%s）" % a["overflowX"])

        print("\n== 5. 语言切换后署名行不变（不被 applyLang 覆写） ==")
        pg.click("#aboutClose")
        pg.wait_for_timeout(200)
        # 切到英语：关于弹窗内其他 <p> 应变英文，署名行必须仍是中文
        ck(set_lang(pg, "en"), "已切到 EN（LANG=%s）" % pg.evaluate("LANG"))
        clear_masks(pg)
        pg.click("#signBtn")
        pg.wait_for_timeout(500)
        a2 = pg.evaluate(ABOUT_MEASURE)
        ck(a2["text"] == "", "EN 下署名行仍是中文：%s" % a2["text"])
        bodyEn = [k["txt"] for k in a2["kids"]]
        ck(any("Built by an AI agent" in t for t in bodyEn), "EN 下正文已切换为英文（applyLang 生效）")
        # 切回中文
        pg.click("#aboutClose")
        pg.wait_for_timeout(200)
        ck(set_lang(pg, "zh"), "已切回中文")
        clear_masks(pg)
        pg.click("#signBtn")
        pg.wait_for_timeout(400)
        a3 = pg.evaluate(ABOUT_MEASURE)
        ck(a3["text"] == "", "切回中文后署名行仍正确：%s" % a3["text"])

        print("\n== 6. 更新日志 ==")
        pg.click("#aboutLog")
        pg.wait_for_timeout(500)
        ck(pg.is_visible("#logMask"), "更新日志弹窗已打开")
        reg2 = pg.evaluate(REG)
        ck(reg2["logFirst"] == "V6.4.10", "首条版本 == V6.4.10（实际 %s）" % reg2["logFirst"])
        ck(reg2["logFirstDate"] == "2026-09-18", "首条日期 == 2026-09-18（实际 %s）" % reg2["logFirstDate"])
        ck(reg2["logFirstTxt"] == "AI设置新增配置指南按钮。", "首条正文 == %s" % reg2["logFirstTxt"])
        ck(len(reg2["logFirstTxt"]) <= 20, "首条正文 %d 字 ≤ 20" % len(reg2["logFirstTxt"]))
        ck("" not in reg2["logFirstTxt"] and "东亭" not in reg2["logFirstTxt"],
           "署名改动未出现在更新日志中")
        pg.click("#logClose")
        pg.wait_for_timeout(300)

        print("\n== 7. 多档视口复扫（配置指南按钮 + 面板） ==")
        for w, h in VIEWPORTS:
            pg.set_viewport_size({"width": w, "height": h})
            pg.wait_for_timeout(350)
            open_ai_cfg(pg)
            pg.click("#aiGuideBtn")
            pg.wait_for_timeout(250)
            mm = pg.evaluate(GUIDE_MEASURE)
            okv = mm["visitVis"] and mm["guideVis"] and mm["panelVis"]
            ck(okv, "%dx%d：前往官网 + 配置指南 + 展开的教程均可见" % (w, h))
            ck(mm["sameRow"], "%dx%d：两按钮同一几何行" % (w, h))
            ck(mm["guideRightOfVisit"], "%dx%d：配置指南在前往官网右侧" % (w, h))
            ck(mm["overflowX"] <= 1, "%dx%d：弹窗无横向溢出（%s）" % (w, h, mm["overflowX"]))
            ck(mm["panelTopBelowRow"] is not None and mm["panelTopBelowRow"] >= 0,
               "%dx%d：面板在按钮行下方（+%s）" % (w, h, mm["panelTopBelowRow"]))
            clear_masks(pg)

        print("\n== 8. 全量回归 ==")
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(400)
        reg3 = pg.evaluate(REG)
        ck(reg3["tabs"] == 11, "导航按钮 == 11（实际 %s）" % reg3["tabs"])
        ck(reg3["panels"] == 12, "面板 == 12（实际 %s）" % reg3["panels"])
        ck(reg3["canvases"] == 11, "canvas == 11（实际 %s）" % reg3["canvases"])
        ck(reg3["modules"], "MODULES / REPORT / S3D 均在")
        pg.click('.tab-btn[data-tab="lens"]')
        pg.wait_for_timeout(600)
        ck(pg.evaluate("document.getElementById('tab-lens').classList.contains('active')"), "切换实验面板正常")
        errs2 = [e for e in errs if not any(n in e for n in NOISE)]
        ck(not errs2, "全程无非预期控制台错误：%s" % errs2[:3])
        ck(pg.evaluate("(window.__rbErrors||[]).length") == 0, "全程 __rbErrors 保持 0")

        b.close()

    print("\n" + "=" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  - " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
