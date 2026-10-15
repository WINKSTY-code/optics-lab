# -*- coding: utf-8 -*-
"""窄屏端点按钮宽度探针：对比智谱与 MiniMax 在同一弹窗宽度下的占位"""
import pathlib
from playwright.sync_api import sync_playwright

url = pathlib.Path("光学交互实验室_AI_v6.4.19.html").resolve().as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "E"); pg.fill("#stuNo", "E")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click("#setBtn"); pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(500)

    for prov in ("zhipu", "minimax"):
        pg.select_option("#aiProvider", prov)
        pg.wait_for_timeout(300)
        print("\n=== %s ===" % prov)
        for w in (390, 360, 480, 560):
            pg.set_viewport_size({"width": w, "height": 800})
            pg.wait_for_timeout(260)
            r = pg.evaluate("""() => {
              const c = document.getElementById('aiBaseUrlBtns');
              const m = document.querySelector('#aiCfgMask .modal');
              const cs = getComputedStyle(c);
              const bs = [...c.querySelectorAll('button[data-url]')].map(x=>{
                const q = x.getBoundingClientRect();
                return {t:x.textContent, w:Math.round(q.width), top:Math.round(q.top)};
              });
              return {modalW:Math.round(m.getBoundingClientRect().width),
                      modalInner:Math.round(m.clientWidth),
                      contW:Math.round(c.getBoundingClientRect().width),
                      gap:cs.gap, pad:cs.padding, bs:bs,
                      need:bs.reduce((a,x)=>a+x.w,0) + (bs.length-1)*(parseFloat(cs.gap)||0)};
            }""")
            print("  %4dpx  modal=%-4d cont=%-4d gap=%-5s need=%-4d -> %s" % (
                w, r["modalW"], r["contW"], r["gap"], r["need"],
                "1 行" if len({x["top"] for x in r["bs"]}) == 1 else "换行 %s" % [x["top"] for x in r["bs"]]))
            for x in r["bs"]:
                print("        %-42s w=%d" % (x["t"], x["w"]))
    b.close()
