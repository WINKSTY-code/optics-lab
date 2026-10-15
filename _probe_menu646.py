# -*- coding: utf-8 -*-
"""V6.4.6 视觉取证：设置下拉（浅色/深色/手机）+ 小孔成像物距组。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.6.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "取景")
        pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd")
        pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")

    # 1) 浅色主题 · 设置下拉展开
    pg.click("#setBtn")
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(BASE / "_v646_设置下拉_浅色.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 420})

    # 2) 深色主题 · 下拉展开
    pg.click("#themeBtn")
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(BASE / "_v646_设置下拉_深色.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 420})
    pg.click("#themeBtn")
    pg.wait_for_timeout(400)
    if not pg.evaluate("document.getElementById('setMenu').hidden"):
        pg.keyboard.press("Escape")

    # 3) 小孔成像：物距组出现（截控制区）
    pg.click('.tab-btn[data-tab="line"]')
    pg.wait_for_timeout(400)
    pg.click('#line-mode [data-m="pinhole"]')
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(BASE / "_v646_小孔物距.png"), clip={"x": 960, "y": 100, "width": 470, "height": 420})

    # 4) 手机 390 宽
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.wait_for_timeout(500)
    pg.click("#setBtn")
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(BASE / "_v646_设置下拉_手机.png"), clip={"x": 0, "y": 0, "width": 390, "height": 300})
    print("geo mobile:", pg.evaluate("""() => {
      const r = document.getElementById('setMenu').getBoundingClientRect();
      return { l: r.left, r: r.right, w: r.width, vw: window.innerWidth,
               mode: document.documentElement.dataset.mode };
    }"""))
    b.close()
print("done")
