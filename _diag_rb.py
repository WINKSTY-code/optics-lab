# -*- coding: utf-8 -*-
"""诊断：__rbOverlay 为何弹出（对比 v5.1.3 / v5.2.0）"""
import os
import sys
import pathlib
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))

for name in ["光学交互实验室_AI_v5.1.3.html", "光学交互实验室_AI_v5.2.0.html"]:
    url = (pathlib.Path(BASE) / name).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1440, "height": 950})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.on("console", lambda m: errs.append("console.%s: %s" % (m.type, m.text)) if m.type in ("error", "warning") else None)
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)
        print("=" * 70)
        print(name)
        print("  __APP_READY  =", pg.evaluate("window.__APP_READY"))
        print("  __rbErrors   =", pg.evaluate("(window.__rbErrors||[]).map(e=>e.kind+' :: '+e.detail.split('\\n').slice(0,3).join(' / '))"))
        print("  overlay      =", pg.evaluate("!!document.getElementById('__rbOverlay')"))
        print("  frames       =", [f.url for f in pg.frames])
        for e in errs[:6]:
            print("  LOG", e[:300])
        b.close()
