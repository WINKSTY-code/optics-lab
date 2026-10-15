# -*- coding: utf-8 -*-
"""V6.4.21 截图：真实跑满超时后，用户看到的提示文案（非伪造，真等 90s）"""
import pathlib
from playwright.sync_api import sync_playwright

url = pathlib.Path("光学交互实验室_AI_v6.4.21.html").resolve().as_uri()
OUT = pathlib.Path("_shot6421")
INIT = r"""
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'zhipu', apikey:'sk-e2e-stub', model:'glm-4.7-flash',
      baseUrl:'https://open.bigmodel.cn/api/paas/v4', thinkMode:false }));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var s = String(u||'');
    if(s.indexOf('chat/completions') < 0 && s.indexOf('/v1/messages') < 0)
      return orig ? orig(u, o) : Promise.reject(new Error('no fetch'));
    return new Promise(function(resolve, reject){
      var sig = o && o.signal;
      if(sig && sig.addEventListener){
        sig.addEventListener('abort', function(){
          var e = new Error('The user aborted a request.'); e.name='AbortError'; reject(e);
        });
      }
      /* 永不 resolve：等真正的超时把它掐断 */
    });
  };
})();
"""


def boot(b):
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
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
    return ctx, pg


OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()

    # 诊断：真等 90s 后的兜底提示
    ctx, pg = boot(b)
    pg.click("#topDiag"); pg.wait_for_timeout(500)
    pg.click("#aiDiagGo")
    pg.wait_for_function("() => (document.getElementById('aiDiagResult')||{}).textContent"
                         " && document.getElementById('aiDiagResult').textContent.indexOf('45 秒')>=0",
                         timeout=140000)
    pg.wait_for_timeout(600)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(OUT / "诊断_45秒超时兜底.png"))
    print("诊断截图完成")
    ctx.close()

    # 问 AI：真等 90s 后的超时提示
    ctx, pg = boot(b)
    pg.click("#topChat"); pg.wait_for_timeout(500)
    pg.fill("#aiAskInput", "光在真空中的传播速度是多少？")
    pg.click("#aiAskSubmit")
    pg.wait_for_function("() => (document.getElementById('aiAskResult')||{}).textContent"
                         " && document.getElementById('aiAskResult').textContent.indexOf('45 秒')>=0",
                         timeout=140000)
    pg.wait_for_timeout(600)
    pg.locator("#aiCfgMask .modal").screenshot(path=str(OUT / "问AI_45秒超时提示.png"))
    print("问AI截图完成")
    ctx.close()
    b.close()

for f in sorted(OUT.glob("*.png")):
    print(f, f.stat().st_size, "B")
