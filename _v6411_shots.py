# -*- coding: utf-8 -*-
import pathlib
from playwright.sync_api import sync_playwright
BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.11.html").resolve().as_uri()
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
        # --- AI 设置：收起态 ---
        pg.click("#setBtn"); pg.wait_for_timeout(250); pg.click("#aiCfgBtn"); pg.wait_for_timeout(450)
        pg.locator("#aiCfgMask .modal").screenshot(path=str(BASE/("_v6411_配置指南_收起_%s.png" % theme)))
        # --- AI 设置：展开教程 ---
        pg.click("#aiGuideBtn"); pg.wait_for_timeout(400)
        pg.locator("#aiCfgMask .modal").screenshot(path=str(BASE/("_v6411_配置指南_展开_%s.png" % theme)))
        pg.evaluate(CLR)
        # --- 关于弹窗 ---
        pg.click("#signBtn"); pg.wait_for_timeout(900)
        pg.locator("#aboutMask .modal").screenshot(path=str(BASE/("_v6411_关于_%s.png" % theme)))
        # --- 更新日志顶部 ---
        pg.click("#aboutLog"); pg.wait_for_timeout(500)
        pg.locator("#logMask .modal").screenshot(path=str(BASE/("_v6411_更新日志_%s.png" % theme)))
        pg.close()

    # 手机竖屏
    pg = b.new_page(viewport={"width": 390, "height": 780}, device_scale_factor=2)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(2000)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", ""); pg.fill("#stuNo", "81001"); pg.click("#stuAdd"); pg.wait_for_timeout(800)
    pg.evaluate(CLR)
    pg.click("#setBtn"); pg.wait_for_timeout(250); pg.click("#aiCfgBtn"); pg.wait_for_timeout(450)
    pg.click("#aiGuideBtn"); pg.wait_for_timeout(400)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(BASE/"_v6411_配置指南_手机390.png"))
    pg.evaluate(CLR)
    pg.click("#signBtn"); pg.wait_for_timeout(900)
    pg.locator("#aboutMask .modal").screenshot(path=str(BASE/"_v6411_关于_手机390.png"))
    pg.close()
    b.close()
print("shots done")
