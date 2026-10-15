# -*- coding: utf-8 -*-
import pathlib
from playwright.sync_api import sync_playwright
BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.12.html").resolve().as_uri()
CLR = """() => { document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.classList.remove('is-closing');}); }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 1440, "height": 950})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(2000)
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.fill("#stuName", ""); pg.fill("#stuNo", "81001"); pg.click("#stuAdd"); pg.wait_for_timeout(800)
        if theme == "dark":
            pg.evaluate(CLR)
            pg.click("#setBtn"); pg.wait_for_timeout(250); pg.click("#themeBtn"); pg.wait_for_timeout(400); pg.click("#setBtn"); pg.wait_for_timeout(250)
        pg.evaluate(CLR)
        pg.click('.tab-btn[data-tab="judge"]'); pg.wait_for_timeout(900)
        pg.locator("#tab-judge").screenshot(path=str(BASE/("_v6412_挑战模式_自动选择题_%s.png" % theme)))
        pg.close()

    pg = b.new_page(viewport={"width": 390, "height": 780}, device_scale_factor=2)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(2000)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", ""); pg.fill("#stuNo", "81001"); pg.click("#stuAdd"); pg.wait_for_timeout(800)
    pg.evaluate(CLR)
    pg.click('.tab-btn[data-tab="judge"]'); pg.wait_for_timeout(900)
    pg.locator("#tab-judge").screenshot(path=str(BASE/"_v6412_挑战模式_自动选择题_手机390.png"))
    pg.close()
    b.close()
print("shots done")
