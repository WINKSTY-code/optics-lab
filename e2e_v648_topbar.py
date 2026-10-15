# -*- coding: utf-8 -*-
"""V6.4.8 端到端：顶栏按钮簇布局（无空洞 / 贴右 / 不溢出）+ 设置下拉四功能 + 全量回归。"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.8.html").resolve().as_uri()

PASS, FAIL = [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)


MEASURE = r"""() => {
  const q = s => document.querySelector(s);
  const R = e => e ? e.getBoundingClientRect() : null;
  const acts = document.querySelector('.topbar-actions');
  const bar  = document.querySelector('.topbar');
  const items = [...acts.querySelectorAll('button, .ai-status')]
      .filter(e => e.getBoundingClientRect().width > 0)
      .map(e => { const r = e.getBoundingClientRect();
                  return {id: e.id || (e.className || e.tagName), l:+r.left.toFixed(1), r:+r.right.toFixed(1),
                          t:+r.top.toFixed(1), b:+r.bottom.toFixed(1), w:+r.width.toFixed(1)}; });
  // 按 top 聚类成「几何行」（按钮行高一致，容差 10px）
  const tops = [...new Set(items.map(i => i.t))].sort((a,b)=>a-b);
  const rows = [];
  tops.forEach(t => { const last = rows[rows.length-1];
    if (last && t - last.t <= 10) last.top.push(t); else rows.push({t:t, top:[t]}); });
  const rowOf = t => rows.findIndex(rr => rr.top.some(x => Math.abs(x-t) <= 10));
  const grouped = rows.map((rr,i) => items.filter(it => rowOf(it.t) === i).sort((a,b)=>a.l-b.l));
  const gaps = grouped.map(g => { let m = 0;
    for (let i=1;i<g.length;i++){ const gp = +(g[i].l - g[i-1].r).toFixed(1); if (gp > m) m = gp; }
    return +m.toFixed(1); });
  const tr = R(bar), ar = R(acts), sw = R(q('.set-wrap')), ti = R(q('.title'));
  return {
    vw: window.innerWidth, mode: document.documentElement.getAttribute('data-mode'),
    rows: grouped.length,
    rowCounts: grouped.map(g => g.length),
    maxGapPerRow: gaps, worstGap: Math.max(0, ...gaps),
    ids: grouped.map(g => g.map(x => x.id)),
    bar: {l:+tr.left.toFixed(1), r:+tr.right.toFixed(1)},
    acts: {l:+ar.left.toFixed(1), r:+ar.right.toFixed(1), w:+ar.width.toFixed(1)},
    setwrap: {l:+sw.left.toFixed(1), r:+sw.right.toFixed(1), t:+sw.top.toFixed(1), b:+sw.bottom.toFixed(1)},
    title: {l:+ti.left.toFixed(1), r:+ti.right.toFixed(1)},
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    menuRect: (() => { const m = q('#setMenu'); if (!m || m.hidden) return null;
                       const r = m.getBoundingClientRect();
                       return {l:+r.left.toFixed(1), r:+r.right.toFixed(1), t:+r.top.toFixed(1), b:+r.bottom.toFixed(1)}; })()
  };
}"""

VIEWPORTS = [(1920, 900), (1600, 900), (1500, 900), (1440, 900), (1366, 800), (1280, 800),
             (1180, 800), (1100, 800), (1000, 800), (960, 800), (900, 800), (881, 800),
             (880, 800), (820, 780), (700, 800), (600, 780), (480, 800), (390, 780), (360, 780)]

FONT_ZOOM_IDS = {"zoomOut", "zoomIn"}


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
        pg.wait_for_timeout(1800)
        dismiss_first_run(pg)

        print("== A. 健康与基线 ==")
        ck(pg.evaluate("window.__rbErrors === undefined || (Array.isArray(window.__rbErrors) && window.__rbErrors.length === 0)"),
           "错误账本为空（__rbErrors 懒创建，无错时为 undefined）")
        ck(not pg.query_selector("#__rbOverlay"), "启动失败浮层不存在")
        ck(pg.inner_text(".ver-badge").strip() == "v6.4.8", "版本角标 = v6.4.8")
        ck(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "tab-btn == 11")
        ck(pg.evaluate("document.querySelectorAll('canvas').length") == 11, "canvas == 11")
        ck(pg.evaluate("document.querySelectorAll('.panel').length") == 12, ".panel == 12")
        ck(pg.evaluate("document.querySelectorAll('script').length") == 16, "script 元素 == 16")
        ck(pg.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object'"), "MODULES / REPORT 就绪")

        print("\n== B. 顶栏按钮簇结构 ==")
        ck(pg.evaluate("!!document.querySelector('.topbar > .topbar-actions')"), ".topbar-actions 是 .topbar 的直接子级")
        ck(pg.evaluate("!!document.querySelector('.topbar-actions > .topbar-right')"), ".topbar-right 在 .topbar-actions 内")
        ck(pg.evaluate("!!document.querySelector('.topbar-actions > .set-wrap')"), ".set-wrap 在 .topbar-actions 内")
        ck(pg.evaluate("getComputedStyle(document.querySelector('.topbar-actions')).overflow") == "visible",
           ".topbar-actions overflow:visible（下拉不会被裁）")
        ck(pg.evaluate("getComputedStyle(document.querySelector('.topbar-actions')).position") == "relative",
           ".topbar-actions position:relative（下拉包含块）")
        ck(pg.evaluate("getComputedStyle(document.querySelector('.set-wrap')).position") == "static",
           ".set-wrap 已不是 positioned（交出包含块）")
        ck(pg.evaluate("""() => { const a = document.querySelector('.topbar-actions');
              const ids = [...a.querySelectorAll('button, .ai-status')].filter(e=>e.getBoundingClientRect().width>0)
                          .map(e => e.id);
              return ids.slice(-3).join(',') === 'diagnose,readAloudBtn,?' || ids.indexOf('setBtn') === ids.length-1; }"""),
           "「设置」是按钮流里的最后一项")

        print("\n== C. 布局：跨视口无空洞 / 贴右 / 不溢出 ==")
        bad = []
        for w, h in VIEWPORTS:
            pg.set_viewport_size({"width": w, "height": h})
            pg.wait_for_timeout(260)
            clear_masks(pg)
            d = pg.evaluate(MEASURE)
            tag = "%dx%d" % (w, h)
            # ① 同一几何行内相邻按钮的间距不得 > 14px（含 4/3px 的设计间距；空洞会到 100px+）
            ok_gap = d["worstGap"] <= 14
            # ② 页面不得横向溢出
            ok_ovf = d["overflowX"] <= 2
            # ③ 桌面端：整簇贴 .topbar 右端
            ok_flush = (d["mode"] != "desktop") or (abs(d["bar"]["r"] - d["acts"]["r"]) <= 1.5)
            # ④ 标题仍在左端
            ok_title = abs(d["title"]["l"] - d["bar"]["l"]) <= 1.5
            if not (ok_gap and ok_ovf and ok_flush and ok_title):
                bad.append("%s mode=%s worstGap=%s ovf=%s flush=%s(%s/%s) title=%s rows=%s" % (
                    tag, d["mode"], d["worstGap"], d["overflowX"], ok_flush,
                    d["bar"]["r"], d["acts"]["r"], ok_title, d["rowCounts"]))
            print("     %-9s mode=%-8s rows=%-10s worstGap=%-6s ovf=%-3s flush=%-5s setBtn=l%s" % (
                tag, d["mode"], str(d["rowCounts"]), d["worstGap"], d["overflowX"], ok_flush, d["setwrap"]["l"]))
        ck(not bad, "19 档视口：行内无空洞 / 无横向溢出 / 桌面贴右 / 标题靠左")
        for x in bad:
            print("       ✗ " + x)

        print("\n== D. 设置下拉：锚定与不出视口 ==")
        for w, h in VIEWPORTS:
            pg.set_viewport_size({"width": w, "height": h})
            pg.wait_for_timeout(200)
            clear_masks(pg)
            pg.click("#setBtn")
            pg.wait_for_timeout(140)
            r = pg.evaluate("""() => { const m = document.querySelector('#setMenu'); if (m.hidden) return null;
                const b = m.getBoundingClientRect();
                return {l:+b.left.toFixed(1), r:+b.right.toFixed(1), t:+b.top.toFixed(1), b:+b.bottom.toFixed(1),
                        vw: window.innerWidth, vh: window.innerHeight,
                        sw: document.querySelector('.set-wrap').getBoundingClientRect().bottom,
                        hit: (() => { const e = document.elementFromPoint(b.left+b.width/2, b.top+b.height/2);
                                      return !!(e && m.contains(e)); })()}; }""")
            tag = "%dx%d" % (w, h)
            ok = bool(r) and r["l"] >= 0 and r["r"] <= r["vw"] + 0.5 and r["b"] <= r["vh"] + 0.5 and r["hit"]
            if not ok:
                FAIL.append("menu@%s" % tag)
                print("       ✗ menu@%s %s" % (tag, r))
            else:
                print("     %-9s menu l=%-7s r=%-7s (vw=%s) 未被裁剪=%s" % (tag, r["l"], r["r"], r["vw"], r["hit"]))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(80)
        ck(True, "19 档视口：下拉全部在视口内且未被裁剪（失败已单列）")

        print("\n== E. 设置下拉：四个功能回归 ==")
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(200)
        clear_masks(pg)

        def ensure_open():
            if pg.evaluate("document.querySelector('#setMenu').hidden"):
                pg.click("#setBtn")
                pg.wait_for_timeout(140)

        ck(pg.evaluate("document.querySelector('#setMenu').hidden"), "初始为收起")
        pg.click("#setBtn")
        pg.wait_for_timeout(120)
        ck(not pg.evaluate("document.querySelector('#setMenu').hidden"), "点「设置」展开")
        ck(pg.get_attribute("#setBtn", "aria-expanded") == "true", "aria-expanded=true")
        for bid in ("zoomOut", "zoomIn", "langBtn", "themeBtn", "aiCfgBtn"):
            ck(pg.is_visible("#" + bid), "#%s 可见" % bid)
        # 字号
        z0 = pg.evaluate("getComputedStyle(document.body).zoom")
        ensure_open()
        pg.click("#zoomIn")
        pg.wait_for_timeout(160)
        z1 = pg.evaluate("getComputedStyle(document.body).zoom")
        ck(z0 != z1, "A＋ 改变字号（%s -> %s）" % (z0, z1))
        ck(not pg.evaluate("document.querySelector('#setMenu').hidden"), "A± 后菜单保持展开")
        ensure_open()
        pg.click("#zoomOut")
        pg.wait_for_timeout(160)
        # 语言
        L0 = pg.inner_text("#langBtn")
        ensure_open()
        pg.click("#langBtn")
        pg.wait_for_timeout(200)
        L1 = pg.inner_text("#langBtn")
        T1 = pg.inner_text(".title")
        ck(L0 != L1, "语言按钮文案变化（%s -> %s）" % (L0, L1))
        ck(T1 != "初中光学 · 交互实验室", "标题随语言切换（%s）" % T1)
        # 切回中文
        for _ in range(5):
            if pg.inner_text(".title") == "初中光学 · 交互实验室":
                break
            ensure_open()
            pg.click("#langBtn")
            pg.wait_for_timeout(220)
        ck(pg.inner_text(".title") == "初中光学 · 交互实验室", "语言可切回中文")
        # 背景色
        B0 = pg.evaluate("document.body.className")
        ensure_open()
        pg.click("#themeBtn")
        pg.wait_for_timeout(200)
        B1 = pg.evaluate("document.body.className")
        ck(B0 != B1, "背景色按钮切换主题（%s -> %s）" % (B0, B1))
        ensure_open()
        pg.click("#themeBtn")
        pg.wait_for_timeout(200)
        # AI 设置 → 弹窗 + 菜单自动收起
        ensure_open()
        pg.click("#aiCfgBtn")
        pg.wait_for_timeout(500)
        ck(pg.evaluate("document.querySelector('#setMenu').hidden"), "点 AI 设置后菜单自动收起")
        ck(pg.evaluate("""() => !!document.querySelector('.modal-mask.show')"""), "AI 设置弹窗已打开")
        clear_masks(pg)
        pg.wait_for_timeout(250)
        # 点外部收起 / Esc 收起
        ensure_open()
        ck(not pg.evaluate("document.querySelector('#setMenu').hidden"), "再次展开")
        pg.click(".title")
        pg.wait_for_timeout(180)
        ck(pg.evaluate("document.querySelector('#setMenu').hidden"), "点外部收起")
        ensure_open()
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(180)
        ck(pg.evaluate("document.querySelector('#setMenu').hidden"), "Esc 收起")

        print("\n== F. 顶栏其它按钮未受影响 ==")
        ck(pg.evaluate("!!document.querySelector('.topbar-right #studentBtn')"), "「学生」按钮仍在顶栏按钮排内")
        ck(pg.evaluate("document.getElementById('topTts') && document.getElementById('topTts').closest('.set-menu') === null"),
           "「朗读」没有掉进下拉里")
        ck(pg.evaluate("document.getElementById('aiCfgBtn').closest('.set-menu') !== null"), "AI 设置在菜单里（预期）")
        ck(pg.is_visible("#fsBtn") and pg.is_visible("#signBtn"), "全屏 / 关于 可见")

        print("\n== G. 控制台 ==")
        noise = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "ERR_ABORTED")
        real = [e for e in errs if not any(n in e for n in noise)]
        ck(not real, "无真实控制台错误（%d 条噪声已过滤）" % (len(errs) - len(real)))
        for e in real[:8]:
            print("       ✗ " + e[:220])

        b.close()

    print("\n" + "=" * 62)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  ✗ " + f)
        sys.exit(1)
    print("端到端 ALL PASS")


if __name__ == "__main__":
    main()
