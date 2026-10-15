# -*- coding: utf-8 -*-
"""对照：shadow（新增）vs pinhole（既有 v6.4.3）在同一环境下的
   (a) 子文档 rAF 实际频率  (b) 点 tab 切走后是否真的停。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()
RAF_COUNT = """() => new Promise(res => {
  let n = 0; const t0 = performance.now();
  (function f(){ n++;
     if (performance.now() - t0 < 600) requestAnimationFrame(f); else res(n); })();
})"""


def clear(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); });""")


def frames(fr):
    return fr.evaluate("((window.__dbg||window.S3D||{}).renderer||{info:{render:{frame:-1}}}).info.render.frame")


def probe(pg, key):
    print("\n===== %s =====" % key)
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(500); clear(pg)
    if key == "pinhole":
        pg.click('#line-mode .sec[data-m="pinhole"]'); pg.wait_for_timeout(600); clear(pg)
    pg.click('.s3d-bar[data-s3d="%s"] .s3d-b[data-m="3d"]' % key)
    pg.wait_for_timeout(2400)
    fr = pg.query_selector('.s3d-frame[data-s3d="%s"] .s3d-ifr' % key).content_frame()
    print("  可见性: hidden=%s visibilityState=%s" % (
        fr.evaluate("document.hidden"), fr.evaluate("document.visibilityState")))
    print("  3D 态 子文档 rAF/600ms =", fr.evaluate(RAF_COUNT))
    a = frames(fr); pg.wait_for_timeout(700); b = frames(fr)
    print("  3D 态 render.frame: %s -> %s" % (a, b))
    print("  __demo.run() =", fr.evaluate("typeof __demo!=='undefined' ? __demo.run() : 'n/a'"))
    # ★ 用真实点击切页（不是 evaluate switchTab）
    pg.click('.tab-btn[data-tab="lens"]'); pg.wait_for_timeout(800)
    c = frames(fr); pg.wait_for_timeout(900); d = frames(fr)
    print("  点 tab 切走 render.frame: %s -> %s  (停了=%s)" % (c, d, d == c))
    print("  切走后 __demo.run() =", fr.evaluate("typeof __demo!=='undefined' ? __demo.run() : 'n/a'"))
    # 切回来（真实点击）→ 应恢复
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(900); clear(pg)
    e = frames(fr); pg.wait_for_timeout(700); f2 = frames(fr)
    print("  点 tab 切回 render.frame: %s -> %s  (醒了=%s)" % (e, f2, f2 > e))
    print("  切回后 __demo.run() =", fr.evaluate("typeof __demo!=='undefined' ? __demo.run() : 'n/a'"))
    if key == "pinhole":
        pg.click('#line-mode .sec[data-m="pinhole"]'); pg.wait_for_timeout(400)
    clear(pg)


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    for pat in ("**/cdn.jsdelivr.net/**", "**/fonts.googleapis.com/**", "**/fonts.gstatic.com/**"):
        pg.route(pat, lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd")
        pg.wait_for_timeout(700)
    clear(pg)
    probe(pg, "shadow")
    probe(pg, "pinhole")
    b.close()
