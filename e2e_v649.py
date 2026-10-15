# -*- coding: utf-8 -*-
"""V6.4.9 端到端：
① 直线传播（影子形成 / 小孔成像）调节栏已在画布下方，且 3D 模式下正确让位；
② 物体颜色：控件全部可见可点，20 种「本色 × 照射光」组合的看到的颜色都符合物理。
"""
import pathlib, sys, itertools
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.9.html").resolve().as_uri()

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
            pg.fill("#stuName", "E2E")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(700)
    except Exception:
        pass
    clear_masks(pg)


OC = {'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1), 'yellow': (1, 1, 0), 'white': (1, 1, 1)}
LT = {'white': (1, 1, 1), 'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1)}
ZH = {'000': '黑', '100': '红', '010': '绿', '001': '蓝', '110': '黄', '111': '白'}
HEX_OC = {'red': (229, 57, 53), 'green': (67, 160, 71), 'blue': (30, 136, 229),
          'yellow': (253, 216, 53), 'white': (242, 242, 242)}


def expect_key(oc, lt):
    o, L = OC[oc], LT[lt]
    return '%d%d%d' % (1 if (o[0] and L[0]) else 0, 1 if (o[1] and L[1]) else 0, 1 if (o[2] and L[2]) else 0)


def hue_of(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 32:
        return 'black'
    if mn > 115:
        return 'white'
    if r > g * 1.6 and r > b * 1.6:
        return 'red'
    if g > r * 1.6 and g > b * 1.6:
        return 'green'
    if b > r * 1.6 and b > g * 1.6:
        return 'blue'
    if r > b * 1.6 and g > b * 1.6 and abs(r - g) < 0.25 * max(r, g):
        return 'yellow'
    return '?'


PIXEL_JS = r"""() => {
  const cv = document.querySelector('#cv-disp');
  const ctx = cv.getContext('2d');
  const ax = cv.width / 2, ay = cv.height / 2;
  const body = ctx.getImageData(Math.round(ax), Math.round(ay), 1, 1).data;
  const sw = ctx.getImageData(Math.round(ax - 157), Math.round(ay + 94), 1, 1).data;
  return { body: [body[0], body[1], body[2]], swatch: [sw[0], sw[1], sw[2]],
           w: cv.width, h: cv.height };
}"""


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
        ck(pg.evaluate("window.__rbErrors === undefined || window.__rbErrors.length === 0"), "错误账本为空")
        ck(not pg.query_selector("#__rbOverlay"), "启动失败浮层不存在")
        ck(pg.inner_text(".ver-badge").strip() == "v6.4.9", "版本角标 = v6.4.9")
        ck(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "tab-btn == 11")
        ck(pg.evaluate("document.querySelectorAll('canvas').length") == 11, "canvas == 11")
        ck(pg.evaluate("document.querySelectorAll('.panel').length") == 12, ".panel == 12")
        ck(pg.evaluate("document.querySelectorAll('script').length") == 16, "script 元素 == 16")
        ck(pg.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object' && typeof S3D === 'object'"),
           "MODULES / REPORT / S3D 就绪")

        print("\n== B. ① 直线传播：调节栏在画布下方 ==")
        pg.click('.tab-btn[data-tab="line"]')
        pg.wait_for_timeout(400)
        clear_masks(pg)
        info = pg.evaluate("""() => {
          const ctl = document.querySelector('#line-mode').closest('.ctrl');
          const cv  = document.querySelector('#cv-line');
          const l = ctl.getBoundingClientRect(), c = cv.getBoundingClientRect();
          const col = ctl.closest('.left');
          return { inLeft: !!col, afterCanvas: l.top >= c.bottom - 6,
                   leftColW: col ? Math.round(col.getBoundingClientRect().width) : -1,
                   ctlW: Math.round(l.width), ctlTop: Math.round(l.top), cvBottom: Math.round(c.bottom),
                   parentCls: ctl.parentNode.className,
                   ovf: document.documentElement.scrollWidth - document.documentElement.clientWidth };
        }""")
        ck(info["inLeft"], "调节栏是 .left（画布那列）的子级")
        ck(info["afterCanvas"], "调节栏在画布下方（top %d >= 画布底 %d）" % (info["ctlTop"], info["cvBottom"]))
        ck(info["parentCls"] == "left", "调节栏的直接父级 = .left（实际 %s）" % info["parentCls"])
        ck(info["ovf"] <= 2, "无横向溢出")
        # 对照：前几个 2D 实验同样在画布下方
        pg.click('.tab-btn[data-tab="reflect"]')
        pg.wait_for_timeout(300)
        r = pg.evaluate("""() => {
          const ctl = document.querySelector('#refl-iSlider').closest('.ctrl');
          const cv  = document.querySelector('#cv-refl');
          return { parentCls: ctl.parentNode.className,
                   afterCanvas: ctl.getBoundingClientRect().top >= cv.getBoundingClientRect().bottom - 6 };
        }""")
        ck(r["parentCls"] == "left" and r["afterCanvas"],
           "对照：光的反射调节栏同样在 .left / 画布下方")
        # 三模式：控件显隐
        pg.click('.tab-btn[data-tab="line"]')
        pg.wait_for_timeout(300)
        pg.click('#line-mode .sec[data-m="pinhole"]')
        pg.wait_for_timeout(250)
        vis = pg.evaluate("""() => {
          const g = s => { const e = document.querySelector(s);
            return e ? getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0 : false; };
          return { u: g('#line-uSlider'), v: g('#line-vSlider'), hole: g('#line-holeSlider'),
                   obj: g('#line-objSlider'), reset: g('#line-reset') };
        }""")
        ck(vis["u"] and vis["v"] and vis["hole"] and not vis["obj"] and vis["reset"],
           "小孔成像：物距/像距/孔大小可见，物体位置隐藏（%s）" % vis)
        pg.click('#line-mode .sec[data-m="shadow"]')
        pg.wait_for_timeout(250)
        vis2 = pg.evaluate("""() => {
          const g = s => { const e = document.querySelector(s);
            return e ? getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0 : false; };
          return { u: g('#line-uSlider'), obj: g('#line-objSlider'), v: g('#line-vSlider'), hole: g('#line-holeSlider') };
        }""")
        ck(vis2["u"] and vis2["obj"] and not vis2["v"] and not vis2["hole"],
           "影子形成：物距/物体位置可见，像距/孔大小隐藏（%s）" % vis2)
        # 控件仍能用
        pg.eval_on_selector("#line-uSlider", "el => { el.value = 20; el.dispatchEvent(new Event('input', {bubbles:true})); }")
        pg.wait_for_timeout(220)
        ck(abs(float(pg.inner_text("#line-uVal")) - 20.0) < 0.05,
           "物距滑杆仍生效（#line-uVal = %s）" % pg.inner_text("#line-uVal"))
        pg.eval_on_selector("#line-objSlider", "el => { el.value = 3; el.dispatchEvent(new Event('input', {bubbles:true})); }")
        pg.wait_for_timeout(220)
        ck(pg.inner_text("#line-objVal").strip() not in ("", "中"),
           "物体位置滑杆仍生效（%s）" % pg.inner_text("#line-objVal"))
        pg.click("#line-reset")
        pg.wait_for_timeout(250)
        ck(pg.inner_text("#line-uVal").strip() == "30", "重置回 30（%s）" % pg.inner_text("#line-uVal"))
        # 3D 模式下调节栏让位（与其它实验一致）
        pg.click('.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(900)
        ck(pg.evaluate("""() => { const c = document.querySelector('#line-mode').closest('.ctrl');
              return c.getBoundingClientRect().width === 0 || getComputedStyle(c).display === 'none'; }"""),
           "切 3D 后调节栏收起（与其它实验一致）")
        pg.click('.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="2d"]')
        pg.wait_for_timeout(600)
        ck(pg.evaluate("""() => { const c = document.querySelector('#line-mode').closest('.ctrl');
              return c.getBoundingClientRect().width > 0; }"""), "切回 2D 后调节栏恢复")

        print("\n== C. ② 物体颜色：控件可见 + 20 组组合的物理正确性 ==")
        pg.click('.tab-btn[data-tab="disperse"]')
        pg.wait_for_timeout(350)
        pg.click('#disp-mode .sec[data-m="obj"]')
        pg.wait_for_timeout(350)
        st = pg.evaluate("""() => {
          const q = s => document.querySelector(s);
          const g = e => !!e && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0;
          const o = q('#disp-obj-ctrl'), r = q('#disp-rgb-ctrl');
          return { objVis: g(o), rgbVis: g(r),
                   objParent: o.parentNode.id || o.parentNode.className,
                   objH: Math.round(o.getBoundingClientRect().height),
                   objBtns: [...o.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0).length,
                   ocBtns: document.querySelectorAll('#disp-obj-color .sec').length,
                   lightBtns: document.querySelectorAll('#disp-light .sec').length,
                   oc: [...document.querySelectorAll('#disp-obj-color .sec')].map(b => b.dataset.oc),
                   lt: [...document.querySelectorAll('#disp-light .sec')].map(b => b.dataset.l) };
        }""")
        ck(st["objVis"], "物体颜色控件组可见（高度 %d px）" % st["objH"])
        ck(not st["rgbVis"], "色光三原色控件组已隐藏")
        ck(st["objParent"] == "ctrl", "控件组不再被嵌进 #disp-rgb-ctrl（父级 = %s）" % st["objParent"])
        ck(st["objBtns"] == 9, "可见按钮 9 个（5 本色 + 4 照射光），实际 %d" % st["objBtns"])
        ck(st["oc"] == ['red', 'green', 'blue', 'yellow', 'white'], "本色选项 = %s" % st["oc"])
        ck(st["lt"] == ['white', 'red', 'green', 'blue'], "照射光选项 = %s" % st["lt"])

        # ★ DOM 嵌套：修嵌套时绝不能把 .right 顶出 .stage（上一轮就是这里翻的车）
        nest = pg.evaluate("""() => {
          const st = document.querySelector('#tab-disperse .stage');
          const kids = [...st.children].map(e => e.className || e.tagName);
          const o = document.querySelector('#disp-obj-ctrl');
          return { kids: kids, dataInRight: !!document.querySelector('#tab-disperse .data-panel').closest('.right'),
                   objParent: o.parentNode.id || o.parentNode.className,
                   inWrap: [...document.querySelectorAll('.panel')].filter(p => p.parentNode.className === 'wrap').length,
                   total: document.querySelectorAll('.panel').length };
        }""")
        ck(nest["kids"] == ['left', 'right'], "色散面板 .stage 仍是 left + right 两列（%s）" % nest["kids"])
        ck(nest["dataInRight"], "数据表面板仍在 .right 内（没被顶出去）")
        ck(nest["objParent"] == "ctrl", "#disp-obj-ctrl 的父级是 .ctrl（%s）" % nest["objParent"])
        ck(nest["inWrap"] == nest["total"] == 12, "12 个面板全部在 .wrap 内（%d/%d）" % (nest["inWrap"], nest["total"]))

        bad = []
        for oc, lt in itertools.product(OC.keys(), LT.keys()):
            pg.click('#disp-obj-color .sec[data-oc="%s"]' % oc)
            pg.click('#disp-light .sec[data-l="%s"]' % lt)
            pg.wait_for_timeout(110)
            key = expect_key(oc, lt)
            want_zh = ZH[key]
            d = pg.evaluate(PIXEL_JS)
            vtxt = pg.inner_text("#verdict-disp")
            got_hue = hue_of(*d["body"])
            want_hue = {'000': 'black', '100': 'red', '010': 'green', '001': 'blue',
                        '110': 'yellow', '111': 'white'}[key]
            sw_ok = all(abs(a - b) <= 6 for a, b in zip(d["swatch"], HEX_OC[oc]))
            v_ok = ('看到的颜色：' + want_zh + '色') in vtxt
            ok = (got_hue == want_hue) and v_ok and sw_ok
            if not ok:
                bad.append("%s物体+%s光 → 期望%s(hue=%s,文本%s,色块%s) 实测 body=%s hue=%s swatch=%s v=%r"
                           % (oc, lt, want_zh, want_hue, v_ok, sw_ok, d["body"], got_hue, d["swatch"], vtxt[:60]))
            print("     %-6s × %-6s → 看到的颜色 %s   body=%-16s %s" %
                  (oc, lt, want_zh, str(d["body"]), "OK" if ok else "FAIL"))
        ck(not bad, "20 组「本色 × 照射光」全部物理正确（画布像素 + 结论文本 + 本色色块）")
        for x in bad:
            print("       ✗ " + x)

        # 结论中的「原因」句
        pg.click('#disp-obj-color .sec[data-oc="red"]')
        pg.click('#disp-light .sec[data-l="white"]')
        pg.wait_for_timeout(200)
        ck('白光里含各种色光' in pg.inner_text("#verdict-disp"), "白光照射 → 命中「白光含各种色光」说明")
        pg.click('#disp-light .sec[data-l="red"]')
        pg.wait_for_timeout(200)
        ck('两者共有的色光' in pg.inner_text("#verdict-disp"), "单色光照射（有反射）→ 命中「共有的色光」说明")
        pg.click('#disp-obj-color .sec[data-oc="red"]')
        pg.click('#disp-light .sec[data-l="green"]')
        pg.wait_for_timeout(200)
        ck('没有' in pg.inner_text("#verdict-disp") and '黑的' in pg.inner_text("#verdict-disp"),
           "绿光照射红物体 → 命中「没有可反射的色光 → 黑的」说明")
        ck(pg.evaluate("document.querySelector('#disp-obj-color .sec.active').dataset.oc") == "red",
           "本色高亮状态跟随点击")

        # 数据记录
        pg.click('#disp-recBtn')
        pg.wait_for_timeout(400)
        row = pg.evaluate("""() => { const tr = document.querySelectorAll('#disp-dataBody tr');
            if (!tr.length) return null; const t = tr[tr.length-1];
            return [...t.children].map(td => td.textContent.trim()); }""")
        ck(bool(row) and row[1] == "物体颜色" and row[2] == "物体本色：红；照射光：绿光"
           and row[3].startswith("看到的颜色：黑"),
           "数据记录行为「本色/照射光/看到的颜色」（%s）" % row)
        pg.click('.tab-btn[data-tab="reflect"]')      # 离开本页，顺带消化掉可能的弹层
        pg.wait_for_timeout(250)
        clear_masks(pg)
        pg.click('.tab-btn[data-tab="disperse"]')
        pg.wait_for_timeout(300)

        # 切回三原色模式，控件组应正确互换
        pg.click('#disp-mode .sec[data-m="rgb"]')
        pg.wait_for_timeout(300)
        sw = pg.evaluate("""() => ({ rgb: getComputedStyle(document.querySelector('#disp-rgb-ctrl')).display,
                                     obj: getComputedStyle(document.querySelector('#disp-obj-ctrl')).display })""")
        ck(sw["rgb"] != "none" and sw["obj"] == "none", "切回三原色：两组控件正确互换（%s）" % sw)
        pg.click('#disp-mode .sec[data-m="obj"]')
        pg.wait_for_timeout(250)

        print("\n== D. 多档视口：新控件不溢出、按钮不折行 ==")
        for w, h in [(1920, 900), (1440, 900), (1280, 800), (1024, 768), (900, 800), (700, 800), (480, 800), (390, 780)]:
            pg.set_viewport_size({"width": w, "height": h})
            pg.wait_for_timeout(260)
            clear_masks(pg)
            d = pg.evaluate("""() => {
              const o = document.querySelector('#disp-obj-ctrl');
              const segs = [...o.querySelectorAll('.seg')];
              return { vis: getComputedStyle(o).display !== 'none',
                       ovf: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                       segRows: segs.map(s => new Set([...s.querySelectorAll('button')]
                              .filter(b => b.getBoundingClientRect().width > 0)
                              .map(b => Math.round(b.getBoundingClientRect().top))).size) };
            }""")
            tag = "%dx%d" % (w, h)
            ck(d["vis"] and d["ovf"] <= 2, "%s 物体颜色控件可见、无横向溢出（ovf=%d, 段内行数=%s）"
               % (tag, d["ovf"], d["segRows"]))
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(200)

        print("\n== E. 控制台 ==")
        noise = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "ERR_ABORTED")
        real = [e for e in errs if not any(n in e for n in noise)]
        ck(not real, "无真实控制台错误（%d 条噪声已过滤）" % (len(errs) - len(real)))
        for e in real[:6]:
            print("       ✗ " + e[:200])

        b.close()

    print("\n" + "=" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("  ✗ " + f)
        sys.exit(1)
    print("端到端 ALL PASS")


if __name__ == "__main__":
    main()
