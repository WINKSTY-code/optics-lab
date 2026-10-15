# -*- coding: utf-8 -*-
"""截取 V6.4.23 自检图：关于弹窗顶部（更新日志最新一条 + 版本信息）。
用法：python _shot_v6423.py 光学交互实验室_AI_v6.4.23.html 自检_输出额度分档_V6423.png
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "自检_输出额度分档_V6423.png"
url = pathlib.Path(FILE).resolve().as_uri()

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2400)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click("#signBtn")
    pg.wait_for_timeout(1400)
    pg.click("#aboutLog")          # 关于 → 更新日志
    pg.wait_for_timeout(1600)
    # 把更新日志列表滚动到最顶部，确保 V6.4.23 首条可见
    pg.evaluate("""() => { const l = document.querySelector('#logMask .log-list'); if(l) l.scrollTop = 0;
        const m = document.querySelector('#logMask .modal'); if(m) m.scrollTop = 0; }""")
    pg.wait_for_timeout(400)
    pg.screenshot(path=OUT, full_page=False)
    txt = pg.evaluate("() => (document.querySelector('#logMask .log-list')||{}).innerText || ''")
    print("首屏日志：")
    print(txt[:200])
    print("saved", OUT)
    ctx.close(); b.close()
