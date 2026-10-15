# -*- coding: utf-8 -*-
"""V6.4.24 验证：AI 判卷（callVisionModel）的输出额度是否也按 Provider 分档，
   且取的是「判卷模型设置」里的 Provider（≠ 主 Provider）。

关键用例（能区分"正确实现"与"图省事写死 cfg.provider"）：
  · B：主=智谱、判卷=DeepSeek → 正确实现应给 8000；若误用主 Provider 会错给 32000。
  · A：主=DeepSeek、判卷=智谱 → 正确实现应给 32000；若误用主 Provider 会错给 8000。

用法：python _e6424_judge_max_tokens.py 光学交互实验室_AI_v6.4.24.html
"""
import pathlib, sys, json
from playwright.sync_api import sync_playwright

FILE = sys.argv[1]
url = pathlib.Path(FILE).resolve().as_uri()
PASS, FAIL = [], []

JUDGE_OBJ = {
    "scores": {}, "total": 80,
    "marks": [{"x": 0.5, "y": 0.5, "ok": True, "label": "入射点正确"}],
    "diagnosis": "画得不错，注意角度。", "suggestions": ["再检查一下反射角"],
    "errorTypes": [], "rootCause": "无明显错因，作图规范",
    "variant": {"question": "入射角 45° 时反射角是多少？", "answer": "45°"},
}


def envelope(content):
    return json.dumps({
        "id": "x", "model": "m", "object": "chat.completion",
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
    }, ensure_ascii=False)


PAYLOAD = envelope(json.dumps(JUDGE_OBJ, ensure_ascii=False))


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


def init_js(judge_provider, main_provider):
    return """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'%s', apikey:'sk-main', model:'', baseUrl:'', thinkMode:true }));
    localStorage.setItem('ai_optics_v1_judge', JSON.stringify({
      provider:'%s', apikey:'sk-judge', model:'', baseUrl:'' }));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}
  window.__reqBodies = [];
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var s = String(u||'');
    if(s.indexOf('chat/completions') < 0 && s.indexOf('/v1/messages') < 0)
      return orig ? orig(u, o) : Promise.reject(new Error('no fetch'));
    try{ window.__reqBodies.push({url:s, body:JSON.parse((o && o.body) || '{}')}); }catch(e){}
    return Promise.resolve(new Response(window.__PAYLOAD_TEXT, {status:200, headers:{'Content-Type':'application/json'}}));
  };
})();
""" % (main_provider, judge_provider)


def boot(b, judge_provider, main_provider):
    ctx = b.new_context(viewport={"width": 1600, "height": 1000})
    ctx.add_init_script("window.__PAYLOAD_TEXT = " + json.dumps(PAYLOAD) + ";")
    ctx.add_init_script(init_js(judge_provider, main_provider))
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2400)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "判卷额度"); pg.fill("#stuNo", "T04")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    return ctx, pg


def run_judge(pg):
    pg.click('.tab-btn[data-tab="judge"]')
    pg.wait_for_timeout(1200)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    # 只看作图题，选第一道
    pg.click('.jcat-btn[data-cat="trace"]')
    pg.wait_for_timeout(500)
    items = pg.query_selector_all(".jp-item")
    assert items, "题库为空"
    items[0].click()
    pg.wait_for_timeout(900)
    # 在画布上画一笔（触发 strokes）
    box = pg.locator("#cv-judge").bounding_box()
    x0 = box["x"] + box["width"] * 0.25
    y0 = box["y"] + box["height"] * 0.55
    pg.mouse.move(x0, y0)
    pg.mouse.down()
    for i in range(1, 12):
        pg.mouse.move(x0 + i * 14, y0 - i * 6)
    pg.mouse.up()
    pg.wait_for_timeout(300)
    # 提交判卷
    pg.click("#judgeSubmit")
    pg.wait_for_function("() => window.__reqBodies.length > 0", timeout=25000)
    pg.wait_for_timeout(1500)   # 等 3 并发都发出去
    return pg.evaluate("() => window.__reqBodies")


with sync_playwright() as p:
    b = p.chromium.launch()

    print("\n[用例A] 主=DeepSeek，判卷=智谱 → 判卷应取智谱档 32000（不能取主 Provider）")
    ctx, pg = boot(b, "zhipu", "deepseek")
    a = run_judge(pg); ctx.close()
    avals = sorted({r["body"].get("max_tokens") for r in a})
    print("     判卷请求 %d 次，max_tokens 取值=%s" % (len(a), avals))
    ck(len(a) == 3, "A 判卷发出 3 次并发请求（temperature 0.1/0.3/0.5）", len(a))
    ck(avals == [32000], "A 判卷按【判卷 Provider=智谱】取到 32000", avals)

    print("\n[用例B] 主=智谱，判卷=MiniMax → 判卷应取 8000（关键：证明读的是判卷配置）")
    ctx, pg = boot(b, "minimax", "zhipu")
    bb = run_judge(pg); ctx.close()
    bvals = sorted({r["body"].get("max_tokens") for r in bb})
    print("     判卷请求 %d 次，max_tokens 取值=%s" % (len(bb), bvals))
    ck(bvals == [8000], "B 判卷按【判卷 Provider=MiniMax】取到 8000（未误用主 Provider 的 32000）", bvals)
    bth = sorted({str(r["body"].get("thinking")) for r in bb})
    ck(bth == ["{'type': 'disabled'}"], "B 判卷对 MiniMax 仍显式关思考（未误改）", bth)

    print("\n[用例C] 判卷=Anthropic → 走 /v1/messages，额度 8000")
    ctx, pg = boot(b, "anthropic", "zhipu")
    c = run_judge(pg); ctx.close()
    cvals = sorted({r["body"].get("max_tokens") for r in c})
    cpaths = sorted({"/v1/messages" if "/v1/messages" in r["url"] else "chat/completions" for r in c})
    print("     判卷请求 %d 次，max_tokens=%s，端点=%s" % (len(c), cvals, cpaths))
    ck(cvals == [8000], "C Anthropic 判卷分支额度 8000", cvals)
    ck(cpaths == ["/v1/messages"], "C 确实走了 Anthropic 分支", cpaths)

    b.close()

print("\n" + "=" * 64)
print("%s 判卷额度分档：通过 %d / 失败 %d" % (FILE, len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 64)
