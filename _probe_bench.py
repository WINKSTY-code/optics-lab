# -*- coding: utf-8 -*-
"""量 shadow 场景单帧渲染耗时（判断低帧率是环境所致还是场景过重）。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()
BENCH = """() => {
  const r = window.__dbg.renderer, sc = window.__dbg.scene, cm = window.__dbg.camera;
  r.render(sc, cm);                       // 预热
  const t0 = performance.now();
  for (let i = 0; i < 10; i++) r.render(sc, cm);
  const ms = (performance.now() - t0) / 10;
  const chart = document.getElementById('chart');
  const t1 = performance.now();
  for (let i = 0; i < 10; i++) window.__demo.state();
  const ms2 = (performance.now() - t1) / 10;
  return { ms: +ms.toFixed(1), state: +ms2.toFixed(2),
           w: r.domElement.width, h: r.domElement.height,
           dpr: window.devicePixelRatio, chart: chart ? chart.width + 'x' + chart.height : 'none' };
}"""


def clear(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); });""")


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
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(400); clear(pg)
    pg.click('.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]'); pg.wait_for_timeout(2400)
    fr = pg.query_selector('.s3d-frame[data-s3d="shadow"] .s3d-ifr').content_frame()
    import json
    print("影子场景:", json.dumps(fr.evaluate(BENCH), ensure_ascii=False))
    b.close()
