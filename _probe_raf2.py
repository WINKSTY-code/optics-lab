# -*- coding: utf-8 -*-
"""决定性判据：直接数子文档 rAF 在 600ms 内实际触发次数，不看任何标志位。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()
RAF_COUNT = """() => new Promise(res => {
  let n = 0; const t0 = performance.now();
  (function f(){ n++;
     if (performance.now() - t0 < 600) requestAnimationFrame(f);
     else res(n);
  })();
})"""


def clear(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); });""")


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    for pat in ("**/cdn.jsdelivr.net/**", "**/fonts.googleapis.com/**", "**/fonts.gstatic.com/**"):
        pg.route(pat, lambda r: r.abort())
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd")
        pg.wait_for_timeout(700)
    clear(pg)

    print("父页 rAF/600ms =", pg.evaluate(RAF_COUNT))

    pg.evaluate("switchTab('line')"); pg.wait_for_timeout(400); clear(pg)
    pg.click('.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
    pg.wait_for_timeout(2300)
    el = pg.query_selector('.s3d-frame[data-s3d="shadow"] .s3d-ifr')
    fr = el.content_frame()
    print("子文档 rAF/600ms（3D 态）=", fr.evaluate(RAF_COUNT))
    print("  frame 计数 =", fr.evaluate("window.__dbg.renderer.info.render.frame"))
    print("  RUN.on =", fr.evaluate("window.__demo.run()"))
    # 场景自带循环是否报错
    print("  场景内 err 浮层 =", fr.evaluate(
        "getComputedStyle(document.getElementById('err')).display"))
    b.close()
    print("父页 pageerror:", errs)
