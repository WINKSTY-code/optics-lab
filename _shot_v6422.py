# -*- coding: utf-8 -*-
"""截取 V6.4.22 修复效果：诊断面板遇到「思考吃光额度」时的呈现。
用法：python _shot_v6422.py 光学交互实验室_AI_v6.4.22.html
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "_v6422_修复效果.png"
url = pathlib.Path(FILE).resolve().as_uri()
PAYLOAD = pathlib.Path("_payload_empty_content.json").read_text(encoding="utf-8")

INIT = """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'zhipu', apikey:'sk-e2e', model:'glm-5.3-flash',
      baseUrl:'https://open.bigmodel.cn/api/coding/paas/v4', thinkMode:true }));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var s = String(u||'');
    if(s.indexOf('chat/completions') < 0 && s.indexOf('/v1/messages') < 0)
      return orig ? orig(u, o) : Promise.reject(new Error('no fetch'));
    return Promise.resolve(new Response(window.__PAYLOAD_TEXT, {status:200, headers:{'Content-Type':'application/json'}}));
  };
})();
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    ctx.add_init_script("window.__PAYLOAD_TEXT = " + json.dumps(PAYLOAD) + ";")
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", ""); pg.fill("#stuNo", "01")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click("#topDiag"); pg.wait_for_timeout(500)
    pg.click("#aiDiagGo")
    pg.wait_for_function("""() => ((document.getElementById('aiDiagResult')||{}).textContent||'').length > 10""",
                         timeout=30000)
    pg.wait_for_timeout(800)
    pg.screenshot(path=OUT, full_page=False)
    print("saved", OUT)
    ctx.close(); b.close()
