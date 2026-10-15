# -*- coding: utf-8 -*-
"""对比 v6.4.8 / v6.4.9 的「色散与颜色」面板：三种模式下各自控件的位置与高度，
用来确认「布局结构」到底有没有被动过。只读。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")

MEASURE = r"""() => {
  const q = s => document.querySelector(s);
  const R = e => { if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.left - 0), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; };
  const stage = q('#tab-disperse .stage');
  return { stage: R(stage),
           left: R(q('#tab-disperse .left')), right: R(q('#tab-disperse .right')),
           cv: R(q('#cv-disp')),
           modeCtrl: R(q('#disp-mode').closest('.ctrl')),
           rgbCtrl: R(q('#disp-rgb-ctrl')), objCtrl: R(q('#disp-obj-ctrl')),
           dataPanel: R(q('#tab-disperse .data-panel')),
           centerCol: getComputedStyle(stage).flexDirection };
}"""


def run(url, tag, shots):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(1500)
        pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
            m.classList.remove('show'); m.classList.remove('is-closing'); })""")
        try:
            if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
                pg.fill("#stuName", "E2E"); pg.fill("#stuNo", "E2E")
                pg.click("#stuAdd"); pg.wait_for_timeout(700)
        except Exception:
            pass
        pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
            m.classList.remove('show'); m.classList.remove('is-closing'); })""")
        pg.click('.tab-btn[data-tab="disperse"]')
        pg.wait_for_timeout(500)
        out = {}
        for mode in ("prism", "rgb", "obj"):
            pg.click('#disp-mode .sec[data-m="%s"]' % mode)
            pg.wait_for_timeout(300)
            out[mode] = pg.evaluate(MEASURE)
            if shots:
                top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-disperse .stage').getBoundingClientRect().top - 8)")
                pg.screenshot(path=str(BASE / ("_v649chk_%s_%s.png" % (tag, mode))),
                              clip={"x": 0, "y": top, "width": 1440, "height": 640})
        b.close()
    return out


a = run((BASE / "光学交互实验室_AI_v6.4.8.html").resolve().as_uri(), "648", True)
b_ = run((BASE / "光学交互实验室_AI_v6.4.9.html").resolve().as_uri(), "649", False)

for mode in ("prism", "rgb", "obj"):
    print("=== mode = %s ===" % mode)
    for k in ("stage", "left", "right", "cv", "modeCtrl", "rgbCtrl", "objCtrl", "dataPanel"):
        print("  %-9s 648: %-34s 649: %s" % (k, str(a[mode][k]), str(b_[mode][k])))
