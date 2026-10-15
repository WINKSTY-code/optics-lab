# -*- coding: utf-8 -*-
"""V6.4.23 验证：问 AI 与诊断发出的 max_tokens 是否按 Provider 分档。

要点：
  · 问 AI 与诊断共用 callLLM → 两者取值必须一致；
  · 智谱（有官方文档背书）→ 32000；未勾深度思考 → 800；其余厂商 → 8000 通用档；
  · 非智谱不能被放大（否则可能 HTTP 400 超限）。

用法：python _e6423_max_tokens.py 光学交互实验室_AI_v6.4.23.html
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
url = pathlib.Path(FILE).resolve().as_uri()
PASS, FAIL = [], []

OK_PAYLOAD = json.dumps({
    "id": "x", "model": "m", "object": "chat.completion",
    "choices": [{"index": 0, "finish_reason": "stop",
                 "message": {"role": "assistant", "content": "凸透镜成像规律：物距大于二倍焦距成倒立缩小的实像。"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
}, ensure_ascii=False)


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


def init_js(provider, think):
    return """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'%s', apikey:'sk-e2e', model:'x', baseUrl:'', thinkMode:%s }));
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
""" % (provider, "true" if think else "false")


def boot(b, provider, think):
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script("window.__PAYLOAD_TEXT = " + json.dumps(OK_PAYLOAD) + ";")
    ctx.add_init_script(init_js(provider, think))
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "额度测试"); pg.fill("#stuNo", "T03")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    return ctx, pg


def ask_chat(pg):
    pg.click("#topChat"); pg.wait_for_timeout(400)
    pg.fill("#aiAskInput", "凸透镜成像规律是什么？")
    pg.click("#aiAskSubmit")
    pg.wait_for_function("""() => ((document.getElementById('aiAskResult')||{}).textContent||'').length > 10""",
                         timeout=30000)
    pg.wait_for_timeout(400)
    return pg.evaluate("() => window.__reqBodies[0] || {}")


def run_diag(pg):
    pg.click("#topDiag"); pg.wait_for_timeout(500)
    pg.click("#aiDiagGo")
    pg.wait_for_function("""() => ((document.getElementById('aiDiagResult')||{}).textContent||'').length > 10""",
                         timeout=30000)
    pg.wait_for_timeout(400)
    return pg.evaluate("() => window.__reqBodies[0] || {}")


with sync_playwright() as p:
    b = p.chromium.launch()

    print("\n[用例A] 智谱 + 深度思考 → 问 AI")
    ctx, pg = boot(b, "zhipu", True)
    a = ask_chat(pg); ctx.close()
    print("     max_tokens=%s  thinking=%s" % (a.get("max_tokens"), a.get("thinking")))
    ck(a.get("max_tokens") == 32000, "A 智谱放大到 32000", a.get("max_tokens"))

    print("\n[用例B] 智谱 + 深度思考 → 诊断（应与 A 完全一致，证明同一链路）")
    ctx, pg = boot(b, "zhipu", True)
    bb = run_diag(pg); ctx.close()
    print("     max_tokens=%s" % bb.get("max_tokens"))
    ck(bb.get("max_tokens") == 32000, "B 诊断也是 32000（问AI/诊断同链路）", bb.get("max_tokens"))
    ck(bb.get("max_tokens") == a.get("max_tokens"), "B 与问 AI 取值一致")

    print("\n[用例C] 智谱 + 不勾深度思考 → 普通档 800")
    ctx, pg = boot(b, "zhipu", False)
    c = ask_chat(pg); ctx.close()
    print("     max_tokens=%s  thinking=%s" % (c.get("max_tokens"), c.get("thinking")))
    ck(c.get("max_tokens") == 800, "C 未勾思考回落到 800", c.get("max_tokens"))

    print("\n[用例D] DeepSeek + 深度思考 → 通用档 8000（未被放大，避免超 8192）")
    ctx, pg = boot(b, "deepseek", True)
    d = ask_chat(pg); ctx.close()
    print("     max_tokens=%s" % d.get("max_tokens"))
    ck(d.get("max_tokens") == 8000, "D DeepSeek 仍守 8000 通用档", d.get("max_tokens"))
    ck(d.get("max_tokens") <= 8192, "D 未超过 8192 硬上限")

    print("\n[用例E] OpenAI + 深度思考 → 通用档 8000")
    ctx, pg = boot(b, "openai", True)
    e = ask_chat(pg); ctx.close()
    print("     max_tokens=%s" % e.get("max_tokens"))
    ck(e.get("max_tokens") == 8000, "E 未知上限厂商守 8000（不盲目放大）", e.get("max_tokens"))

    b.close()

print("\n" + "=" * 64)
print("%s 额度分档：通过 %d / 失败 %d" % (FILE, len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 64)
