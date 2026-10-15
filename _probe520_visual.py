# -*- coding: utf-8 -*-
"""探针：ecl 标题对比度（两种主题）+ 模式按钮换行（各 zoom / 移动端）"""
import os, functools, http.server, socketserver, threading
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
NAME = "光学交互实验室_AI_v5.2.0.html"
PORT = 8792


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


httpd = socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(H, directory=BASE))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d/%s" % (PORT, NAME)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")
    pg.evaluate("switchTab('line')")
    pg.wait_for_timeout(300)
    pg.click('#line-mode .sec[data-m="eclipse"]')
    pg.wait_for_timeout(600)

    for theme in ["light", "dark"]:
        pg.evaluate("THEME='%s'; applyTheme();" % theme)
        pg.wait_for_timeout(400)
        info = pg.evaluate("""() => {
          const t=document.querySelector('.ecl-title'), hd=document.querySelector('.ecl-head'),
                bd=document.querySelector('.ecl-badge'), tip=document.querySelector('.ecl-bar .ecl-tip'),
                note=document.getElementById('line-eclNote');
          const g=e=>e?getComputedStyle(e).color:'n/a';
          const bg=e=>{let n=e; while(n){const c=getComputedStyle(n).backgroundColor;
            if(c&&c!=='rgba(0, 0, 0, 0)') return c; n=n.parentElement;} return 'transparent';};
          return {theme:document.body.className||'(none)',
                  titleColor:g(t), titleBg:bg(t), badge:g(bd), tip:g(tip), note:g(note),
                  panelColor:getComputedStyle(document.querySelector('#tab-line .right')).color};
        }""")
        print(info)
        el = pg.locator("#line-eclHost")
        el.screenshot(path=os.path.join(BASE, "_probe520_头部_%s.png" % theme))
        pg.screenshot(path=os.path.join(BASE, "_probe520_整页_%s.png" % theme))
    pg.evaluate("THEME='light'; applyTheme();")

    print("\n=== 行数（桌面 1600，zoom 0.8~1.4）===")
    for z in [0.8, 1.0, 1.1, 1.2, 1.3, 1.4]:
        pg.evaluate("ZOOM=%s; applyZoom();" % z)
        pg.wait_for_timeout(200)
        print("  zoom=%s" % z, pg.evaluate("""() => {
          const bs=[...document.querySelectorAll('#line-mode .sec')];
          return {rows:new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top))).size,
                  h:new Set(bs.map(b=>Math.round(b.getBoundingClientRect().height))).size};}"""))
    b.close()
httpd.shutdown()
