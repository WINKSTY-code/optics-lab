# -*- coding: utf-8 -*-
"""V6.4.22 补充回归：确认 R5 改动没把「正常回答」路径改坏。
  用例 A 正常：content 有正文 + finish_reason='stop'  → 原样渲染，不加截断提示
  用例 B 截断：content 有正文 + finish_reason='length' → 正文后追加「被截断」提示
用法：python _e6422_normal.py 光学交互实验室_AI_v6.4.22.html
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
url = pathlib.Path(FILE).resolve().as_uri()
PASS, FAIL = [], []


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


def payload(content, fr):
    return json.dumps({
        "id": "x", "model": "glm-5.3-flash", "object": "chat.completion",
        "choices": [{"index": 0, "finish_reason": fr,
                     "message": {"role": "assistant", "content": content,
                                 "reasoning_content": "思考中……"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 120, "total_tokens": 130,
                  "completion_tokens_details": {"reasoning_tokens": 40}},
    }, ensure_ascii=False)


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

BODY = "凸透镜成像规律：物距大于二倍焦距时，成倒立、缩小的实像。"


def run(b, fr, label):
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("window.__PAYLOAD_TEXT = " + json.dumps(payload(BODY, fr)) + ";")
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "正常回归"); pg.fill("#stuNo", "T02")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click("#topChat"); pg.wait_for_timeout(400)
    pg.fill("#aiAskInput", "凸透镜成像规律是什么？")
    pg.click("#aiAskSubmit")
    pg.wait_for_function("""() => ((document.getElementById('aiAskResult')||{}).textContent||'').length > 10""",
                         timeout=30000)
    pg.wait_for_timeout(400)
    t = pg.evaluate("() => document.getElementById('aiAskResult').textContent")
    ctx.close()
    return t


with sync_playwright() as p:
    b = p.chromium.launch()

    print("\n[用例A] content 有正文 + finish_reason=stop")
    a = run(b, "stop", "stop")
    print("     渲染：%s" % a[:140].replace("\n", "⏎"))
    ck("凸透镜成像规律" in a, "A 正常正文原样渲染")
    ck("截断" not in a, "A 不误加「被截断」提示")
    ck("reasoning_content" not in a and "finish_reason" not in a, "A 不糊 JSON")

    print("\n[用例B] content 有正文 + finish_reason=length")
    bb = run(b, "length", "length")
    print("     渲染：%s" % bb[:180].replace("\n", "⏎"))
    ck("凸透镜成像规律" in bb, "B 正文保留（未因截断丢正文）")
    ck("截断" in bb, "B 追加了「被截断」提示")

    b.close()

print("\n" + "=" * 64)
print("%s 正常路径：通过 %d / 失败 %d" % (FILE, len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 64)
