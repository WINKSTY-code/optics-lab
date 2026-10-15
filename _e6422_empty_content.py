# -*- coding: utf-8 -*-
"""复现 / 回归：智谱思考模型「思考吃光输出额度 → content 为空」时，页面到底显示了什么？

用法：
  python _e6422_empty_content.py 光学交互实验室_AI_v6.4.21.html          # 期望复现 bug
  python _e6422_empty_content.py 光学交互实验室_AI_v6.4.22.html fixed    # 期望已修好
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
FIXED = len(sys.argv) > 2 and sys.argv[2] == "fixed"
url = pathlib.Path(FILE).resolve().as_uri()
PAYLOAD = pathlib.Path("_payload_empty_content.json").read_text(encoding="utf-8")
PASS, FAIL = [], []


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label + (("  <" + str(extra) + ">") if extra and not cond else ""))
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


INIT = """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'zhipu', apikey:'sk-e2e', model:'glm-5.3-flash',
      baseUrl:'https://open.bigmodel.cn/api/coding/paas/v4', thinkMode:true }));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}
  window.__reqBodies = [];
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var s = String(u||'');
    if(s.indexOf('chat/completions') < 0 && s.indexOf('/v1/messages') < 0)
      return orig ? orig(u, o) : Promise.reject(new Error('no fetch'));
    try{ window.__reqBodies.push(JSON.parse((o && o.body) || '{}')); }catch(e){}
    return Promise.resolve(new Response(window.__PAYLOAD_TEXT, {status:200, headers:{'Content-Type':'application/json'}}));
  };
})();
"""


def boot(b):
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
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
        pg.fill("#stuName", "复现测试"); pg.fill("#stuNo", "T01")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    return ctx, pg


with sync_playwright() as p:
    b = p.chromium.launch()

    print("\n[诊断] 接口返回 200 + finish_reason=length + content='' 时的表现")
    ctx, pg = boot(b)
    pg.click("#topDiag"); pg.wait_for_timeout(500)
    pg.click("#aiDiagGo")
    pg.wait_for_function("""() => {
        const t = (document.getElementById('aiDiagResult')||{}).textContent || '';
        return t.length > 10;
    }""", timeout=30000)
    pg.wait_for_timeout(500)
    diag = pg.evaluate("() => document.getElementById('aiDiagResult').textContent")
    body = pg.evaluate("() => window.__reqBodies[0] || {}")
    print("     渲染长度 %d 字符；前 120 字：%s" % (len(diag), diag[:120].replace("\n", "⏎")))

    dumped = ('"reasoning_content"' in diag) or ("choices" in diag and "finish_reason" in diag)
    if FIXED:
        ck(not dumped, "正文区不再把整包 JSON 糊出来", diag[:160])
        ck("思考" in diag or "输出额度" in diag, "给出了「思考吃光额度」的明确说明", diag[:200])
        ck("本地知识库" in diag, "已回落本地知识库兜底（有内容可看）", diag[:260])
        ck("⚠️" in diag, "以告警样式呈现，不是静默空白")
    else:
        ck(dumped, "【复现】正文区确实把整包 JSON（含英文思考过程）糊了出来", diag[:200])

    print("\n[请求体] 本次实际发出的 max_tokens 与 thinking")
    print("     thinking =", body.get("thinking"), " max_tokens =", body.get("max_tokens"))
    if FIXED:
        ck(body.get("max_tokens", 0) >= 8000, "思考态的输出额度已加大到 ≥8000", body.get("max_tokens"))
    else:
        ck(body.get("max_tokens") == 2000, "【复现】原额度确实是 2000（思考与正文共享）", body.get("max_tokens"))
    ck(body.get("thinking") == {"type": "enabled"}, "思考模式仍按设置开启（未误改功能）", body.get("thinking"))
    ctx.close()

    print("\n[问 AI] 同一份响应下的表现")
    ctx, pg = boot(b)
    pg.click("#topChat"); pg.wait_for_timeout(400)
    pg.fill("#aiAskInput", "凸透镜成像规律是什么？")
    pg.click("#aiAskSubmit")
    pg.wait_for_function("""() => ((document.getElementById('aiAskResult')||{}).textContent||'').length > 10""",
                         timeout=30000)
    pg.wait_for_timeout(500)
    ask = pg.evaluate("() => document.getElementById('aiAskResult').textContent")
    print("     渲染长度 %d 字符；前 120 字：%s" % (len(ask), ask[:120].replace("\n", "⏎")))
    dumped2 = ('"reasoning_content"' in ask) or ("choices" in ask and "finish_reason" in ask)
    if FIXED:
        ck(not dumped2, "问 AI 也不再糊 JSON", ask[:160])
        ck("本地知识库" in ask or "⚠️" in ask, "问 AI 也走告警 + 本地兜底", ask[:200])
    else:
        ck(dumped2, "【复现】问 AI 同样糊 JSON", ask[:160])
    ctx.close()

    b.close()

print("\n" + "=" * 64)
print("%s：通过 %d / 失败 %d" % (FILE, len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 64)
