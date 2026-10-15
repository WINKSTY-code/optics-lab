# -*- coding: utf-8 -*-
"""内嵌版场景的独立验证：真实 Chromium、WebGL 真出图、右下角给父页切换条留空。"""
import pathlib
import sys
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "shadow3d.html").as_uri()


def run(w, h, tag):
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": w, "height": h})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)

        info = pg.evaluate("""() => {
          const err = document.getElementById('err');
          const dock = document.getElementById('dock').getBoundingClientRect();
          const hud = document.getElementById('hud').getBoundingClientRect();
          const chart = document.getElementById('chartCard').getBoundingClientRect();
          const st = window.__demo ? window.__demo.state() : null;
          return {
            errShown: err && getComputedStyle(err).display !== 'none' ? err.textContent : '',
            webglOK: !!(window.__dbg && window.__dbg.renderer && window.__dbg.renderer.getContext()),
            draws: window.__dbg ? window.__dbg.renderer.info.render.calls : -1,
            d: st ? st.calc.d : null, xB: st ? st.calc.xB : null,
            crit: st ? st.crit : null,
            dock: {l:dock.left, r:dock.right, t:dock.top, b:dock.bottom},
            hud: {l:hud.left, r:hud.right, t:hud.top, b:hud.bottom},
            chart: {l:chart.left, r:chart.right, t:chart.top, b:chart.bottom, vis: getComputedStyle(document.getElementById('chartCard')).display},
            W: innerWidth, H: innerHeight,
            btnFullVis: getComputedStyle(document.getElementById('btnFull')).display,
            bodyCls: document.body.className
          };
        }""")
        print("=== [%s] %dx%d ===" % (tag, w, h))
        print("  body.class       :", info["bodyCls"])
        print("  webgl / drawCalls:", info["webglOK"], "/", info["draws"])
        print("  报错浮层         :", repr(info["errShown"]))
        print("  __demo.state     : d=%.4f  xB=%.4f  最小点 xB≈%.3f" % (info["d"], info["xB"], info["crit"]))
        print("  dock             : L%.0f R%.0f T%.0f B%.0f" % (info["dock"]["l"], info["dock"]["r"], info["dock"]["t"], info["dock"]["b"]))
        print("  hud              : L%.0f R%.0f T%.0f B%.0f" % (info["hud"]["l"], info["hud"]["r"], info["hud"]["t"], info["hud"]["b"]))
        print("  chartCard        : %s  L%.0f R%.0f T%.0f B%.0f" % (info["chart"]["vis"], info["chart"]["l"], info["chart"]["r"], info["chart"]["t"], info["chart"]["b"]))
        print("  自带全屏按钮      :", info["btnFullVis"])
        print("  为父页切换条留空  : right 边界 %.0f <= W-178=%d ? %s" % (info["dock"]["r"], info["W"] - 178, info["dock"]["r"] <= info["W"] - 176))
        print("  控制台错误        :", [e for e in errs if "Failed to load resource" not in e][:4])
        pg.screenshot(path=str(BASE / ("_probe_%s.png" % tag)))
        b.close()


if __name__ == "__main__":
    run(946, 522, "wide")
    run(370, 490, "narrow")
