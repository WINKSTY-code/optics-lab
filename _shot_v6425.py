# -*- coding: utf-8 -*-
"""V6.4.25 自检截图：
 A 等待提示：诊断中…（可能需要 1-2 分钟）
 B 超时文案：请求超时（180 秒未响应）… 且不再出现「已自动重试」
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

HTML = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.25.html"
URL = "file:///" + HTML.replace("\\", "/")
OUT_A = r"C:\Users\Administrator\Desktop\AI光学参赛\自检_等待提示_V6425.png"
OUT_B = r"C:\Users\Administrator\Desktop\AI光学参赛\自检_超时180秒_V6425.png"

STUB = r"""
window.__mode = 'hang';
window.__probe = { calls: 0 };
(function(){
  var real = window.fetch;
  window.fetch = function(url, opts){
    window.__probe.calls++;
    var m = window.__mode;
    if(m === 'hang'){ return new Promise(function(){ }); }
    if(m === 'abort'){ var e = new Error('aborted'); e.name = 'AbortError'; return Promise.reject(e); }
    return real.apply(this, arguments);
  };
})();
"""
CFG = ('{"provider":"zhipu","apikey":"sk-test-only","model":"GLM-5.3-Flash",'
       '"baseUrl":"","thinkMode":true}')

with sync_playwright() as p:
    br = p.chromium.launch(headless=True)
    ctx = br.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=2)
    ctx.add_init_script(STUB)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.evaluate("localStorage.setItem('ai_optics_v1_cfg', %s)" % repr(CFG))
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('.modal-mask.show')"
                ".forEach(function(m){ m.classList.remove('show'); });")

    # A 等待提示
    pg.evaluate("window.__mode = 'hang'; window.__probe.calls = 0;")
    pg.click("#topDiag"); pg.wait_for_timeout(700)
    pg.click("#aiDiagGo"); pg.wait_for_timeout(1800)
    mask = pg.query_selector("#aiDiagMask")
    (mask or pg).screenshot(path=OUT_A)
    print("A 等待提示截图 ->", OUT_A)
    print("   #aiDiagResult =", pg.inner_text("#aiDiagResult").strip().replace("\n", " ")[:80])

    # B 超时文案（先重载：A 的悬挂请求不会结束，按钮会一直 disabled）
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    pg.evaluate("document.querySelectorAll('.modal-mask.show')"
                ".forEach(function(m){ m.classList.remove('show'); });")
    pg.evaluate("window.__mode = 'abort'; window.__probe.calls = 0;")
    pg.click("#topDiag"); pg.wait_for_timeout(700)
    pg.click("#aiDiagGo"); pg.wait_for_timeout(3500)
    (pg.query_selector("#aiDiagMask") or pg).screenshot(path=OUT_B)
    print("B 超时文案截图 ->", OUT_B)
    t = pg.inner_text("#aiDiagResult").strip().replace("\n", " ")
    print("   #aiDiagResult =", t[:150])
    print("   请求次数 =", pg.evaluate("window.__probe.calls"), "（超时应为 1）")
    br.close()
print("完成")
