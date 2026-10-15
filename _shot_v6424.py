# -*- coding: utf-8 -*-
"""截取判卷结果区：修复前（v6.4.23 报 fetchWithRetry ReferenceError） vs 修复后（v6.4.24 正常判卷）。
用法：python _shot_v6424.py <html> <out.png>
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
OUT = sys.argv[2]
url = pathlib.Path(FILE).resolve().as_uri()

JUDGE_OBJ = {
    "scores": {"入射光线": {"score": 28}, "法线": {"score": 18}, "反射光线": {"score": 26}},
    "total": 82,
    "marks": [{"x": 0.32, "y": 0.46, "ok": True, "label": "入射点正确"},
              {"x": 0.60, "y": 0.42, "ok": False, "label": "反射角偏大"}],
    "diagnosis": "入射光线画得很规范！但反射角比入射角大了一点，再对照法线量一量。",
    "suggestions": ["先画法线虚线和角度标注，再画反射光线", "反射角始终等于入射角"],
    "errorTypes": ["角度偏差过大"],
    "rootCause": "错因属角度偏差过大——量角时把入射角当成了与镜面的夹角，应一律对法线度量。",
    "variant": {"question": "若入射角为 30°，反射角应为多少？", "answer": "30°"},
}
PAYLOAD = json.dumps({
    "id": "x", "model": "m", "object": "chat.completion",
    "choices": [{"index": 0, "finish_reason": "stop",
                 "message": {"role": "assistant", "content": json.dumps(JUDGE_OBJ, ensure_ascii=False)}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
}, ensure_ascii=False)

INIT = """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({provider:'zhipu',apikey:'sk-main',model:'',baseUrl:'',thinkMode:true}));
    localStorage.setItem('ai_optics_v1_judge', JSON.stringify({provider:'zhipu',apikey:'sk-judge',model:'',baseUrl:''}));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u,o){ var s=String(u||'');
    if(s.indexOf('chat/completions')<0 && s.indexOf('/v1/messages')<0) return orig?orig(u,o):Promise.reject(new Error('nf'));
    return Promise.resolve(new Response(window.__PAYLOAD_TEXT,{status:200,headers:{'Content-Type':'application/json'}})); };
})();
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    ctx.add_init_script("window.__PAYLOAD_TEXT = " + json.dumps(PAYLOAD) + ";")
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2400)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", ""); pg.fill("#stuNo", "01")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.classList.remove('is-closing');})""")
    pg.click('.tab-btn[data-tab="judge"]'); pg.wait_for_timeout(1300)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.classList.remove('is-closing');})""")
    pg.click('.jcat-btn[data-cat="trace"]'); pg.wait_for_timeout(500)
    pg.query_selector_all(".jp-item")[0].click(); pg.wait_for_timeout(900)
    box = pg.locator("#cv-judge").bounding_box()
    x0 = box["x"] + box["width"] * 0.25; y0 = box["y"] + box["height"] * 0.55
    pg.mouse.move(x0, y0); pg.mouse.down()
    for i in range(1, 14):
        pg.mouse.move(x0 + i * 14, y0 - i * 6)
    pg.mouse.up(); pg.wait_for_timeout(300)
    pg.click("#judgeSubmit")
    pg.wait_for_timeout(6000)
    txt = pg.evaluate("() => document.getElementById('judgeResult').textContent")
    print("判卷结果区文本：", txt[:160].replace("\n", " / "))
    pg.screenshot(path=OUT, full_page=False)
    print("saved", OUT)
    ctx.close(); b.close()
