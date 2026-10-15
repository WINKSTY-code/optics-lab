# -*- coding: utf-8 -*-
"""V6.4.19 截图：智谱端点切换按钮（浅色/深色 × 桌面/手机）"""
import pathlib
from playwright.sync_api import sync_playwright

url = pathlib.Path("光学交互实验室_AI_v6.4.19.html").resolve().as_uri()
OUT = pathlib.Path("_shot6419")


def prep(pg):
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "白老师"); pg.fill("#stuNo", "T01")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click("#setBtn"); pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(600)
    pg.select_option("#aiProvider", "zhipu"); pg.wait_for_timeout(500)
    pg.evaluate("""() => { const p=document.getElementById('aiGuidePanel'); if(p) p.hidden = false; }""")
    pg.wait_for_timeout(400)


def menu_click(pg, sel):
    """「设置」下拉里的按钮：菜单没开就先点开，并等它真正可见再点"""
    for _ in range(6):
        if pg.is_visible(sel):
            pg.click(sel); pg.wait_for_timeout(350); return True
        pg.click("#setBtn"); pg.wait_for_timeout(350)
    raise RuntimeError("菜单项不可见: " + sel)


def open_cfg(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    if pg.is_visible("#setMenu"):
        pg.click("#setBtn"); pg.wait_for_timeout(300)
    menu_click(pg, "#aiCfgBtn")
    pg.wait_for_timeout(500)


def zhipu(pg, highlight_plan=False):
    pg.select_option("#aiProvider", "zhipu"); pg.wait_for_timeout(450)
    if highlight_plan:
        pg.click("#aiBaseUrlBtns button[data-url='https://open.bigmodel.cn/api/coding/paas/v4']")
        pg.wait_for_timeout(300)
    pg.evaluate("""() => { const p=document.getElementById('aiGuidePanel'); if(p) p.hidden = false; }""")
    pg.wait_for_timeout(350)


OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()

    # 桌面 · 浅色
    pg = b.new_page(viewport={"width": 1440, "height": 960})
    prep(pg)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(OUT / "桌面_浅色.png"))
    pg.close()

    # 桌面 · 深色（智谱「套餐额度」高亮态）
    pg = b.new_page(viewport={"width": 1440, "height": 960})
    prep(pg)
    pg.click("#aiCfgClose"); pg.wait_for_timeout(300)
    menu_click(pg, "#themeBtn")          # 切主题
    open_cfg(pg)
    zhipu(pg, highlight_plan=True)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(OUT / "桌面_深色_套餐高亮.png"))
    pg.close()

    # 手机竖屏
    pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    prep(pg)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(OUT / "手机_390.png"))
    pg.close()
    b.close()

for f in sorted(OUT.glob("*.png")):
    print(f, f.stat().st_size, "B")
