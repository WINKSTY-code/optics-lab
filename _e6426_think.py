# -*- coding: utf-8 -*-
"""V6.4.26 端到端验证：批作图题（AI 判卷）的思考模式是否跟随 AI 设置。

思路：
 ① 用可控 fetch 桩把判卷发出的**真实请求体**截下来，断言 thinking 字段随
    AI 设置里的「深度思考模式」开关变化（开=enabled / 关=disabled）；
 ② 用 AbortController 的 abort 时间戳证明判卷超时来自 window.AI_TIMEOUT_MS，
    而不是原来写死的 20s。
全程走真实 UI：点导航按钮 → 打开「判卷模型设置」→ 点「测试连接」（内部就是 callVisionModel）。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

DST = "光学交互实验室_AI_v6.4.26.html"
SHOT = "_shot_v6426.png"

OK, BAD = [], []


def ck(cond, msg):
    (OK if cond else BAD).append(msg)
    print(("  [PASS] " if cond else "  [FAIL] ") + msg)


SEED = r"""
window.__probe = { log: [] };
window.__mode = 'ok';
try {
  localStorage.setItem('ai_optics_v1_cfg', JSON.stringify(
    {provider:'zhipu', apikey:'sk-e2e', model:'', baseUrl:'', thinkMode:true}));
  localStorage.setItem('ai_optics_v1_judge', JSON.stringify({provider:'zhipu', model:'', baseUrl:''}));
  sessionStorage.setItem('ai_optics_v1_keyClearAsked', '1');
} catch(e) {}
(function(){
  var real = window.fetch.bind(window);
  window.fetch = function(u, o){
    var s = String(u || '');
    if(s.indexOf('chat/completions') < 0 && s.indexOf('/v1/messages') < 0) return real(u, o);
    var rec = { url: s, t0: performance.now(), aborted: null, body: (o && o.body) || null };
    rec.n = window.__probe.log.push(rec);
    if(window.__mode === 'hang'){
      return new Promise(function(res, rej){
        var sig = o && o.signal;
        if(sig && sig.addEventListener){
          sig.addEventListener('abort', function(){
            rec.aborted = performance.now();
            var e = new Error('The user aborted a request.'); e.name = 'AbortError'; rej(e);
          });
        }
      });
    }
    var payload = { choices: [{ message: { content: '{"ok":true}' }, finish_reason: 'stop' }], usage: { total_tokens: 12 } };
    return Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: {'Content-Type': 'application/json'} }));
  };
})();
"""

# 超时场景：把 window.AI_TIMEOUT_MS 钉成 3000（页面里的赋值会被 no-op setter 吃掉）
HANG = SEED + r"""
Object.defineProperty(window, 'AI_TIMEOUT_MS', { configurable: true, get: function(){ return 3000; }, set: function(){} });
window.__mode = 'hang';
"""


def clear_masks(pg):
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing');
      });
    }""")


def first_run(pg):
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.wait_for_timeout(600)
            pg.fill("#stuName", "E2E测试")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(700)
    except Exception as e:
        print("  [warn] 首启流程:", e)
    clear_masks(pg)


def open_judge_cfg(pg):
    pg.click('.tab-btn[data-tab="judge"]')
    pg.wait_for_timeout(700)
    clear_masks(pg)
    pg.wait_for_selector('#judgeCfgBtn', state='visible', timeout=8000)
    pg.click('#judgeCfgBtn')
    pg.wait_for_timeout(450)


def fire(pg):
    pg.click('#judgeCfgTest')
    pg.wait_for_timeout(1400)


def last_req(pg):
    return pg.evaluate("() => { const l = window.__probe.log; return l.length ? l[l.length-1] : null; }")


def body_of(r):
    return json.loads(r["body"]) if r else {}


def main():
    url = pathlib.Path(DST).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        ctx.add_init_script(SEED)
        pg = ctx.new_page()
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("dialog", lambda d: d.dismiss())
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(1700)
        first_run(pg)

        # ---------------------------------------------- 场景 1：AI 设置开 → 判卷开
        print("\n[场景 1] AI 设置「深度思考模式」= 开 → 判卷请求应带 thinking=enabled")
        ck(pg.evaluate("JSON.parse(localStorage.getItem('ai_optics_v1_cfg')).thinkMode === true") is True,
           "AI 设置 thinkMode=true（file:// 下 localStorage 可用）")
        ck(pg.evaluate("window.AI_TIMEOUT_MS") == 180000, "主链路 AI_TIMEOUT_MS 已挂到 window = 180000")
        open_judge_cfg(pg)
        note = pg.evaluate("""() => [...document.querySelectorAll('#judgeCfgMask .modal > p')]
                                     .map(e => e.textContent).join(' || ')""")
        ck("思考模式与顶部「⚙ AI 设置」的「深度思考模式」保持一致" in note,
           "判卷设置弹窗已写明「思考模式跟随 AI 设置」")
        pg.screenshot(path=SHOT)
        print("  [shot] " + SHOT)
        fire(pg)
        r1 = last_req(pg)
        ck(bool(r1), "判卷确实发出了 LLM 请求（链路通）")
        b1 = body_of(r1)
        ck("chat/completions" in (r1["url"] if r1 else ""), "打到 OpenAI 兼容端点")
        ck(b1.get("thinking", {}).get("type") == "enabled",
           "判卷请求体 thinking.type == enabled → %s" % b1.get("thinking"))
        ck(b1.get("model") == "glm-5.3-flash", "模型仍为判卷默认 glm-5.3-flash")
        ck(b1.get("max_tokens") == 32000, "额度仍走思考档 32000（未因开关而缩小）")
        clear_masks(pg)

        # ---------------------------------------------- 场景 2：在 AI 设置界面亲手关掉 → 判卷关
        print("\n[场景 2] 在 AI 设置界面取消勾选 → 判卷请求应改为 thinking=disabled")
        pg.click('#setBtn')
        pg.wait_for_timeout(300)
        pg.click('#aiCfgBtn')
        pg.wait_for_timeout(500)
        ck(pg.is_visible('#aiThinkMode'), "AI 设置里有「深度思考模式」复选框")
        ck(pg.is_checked('#aiThinkMode') is True, "复选框初始为勾选（与 thinkMode=true 一致）")
        pg.uncheck('#aiThinkMode')
        pg.click('#aiCfgSave')
        pg.wait_for_timeout(600)
        clear_masks(pg)
        ck(pg.evaluate("JSON.parse(localStorage.getItem('ai_optics_v1_cfg')).thinkMode === false") is True,
           "取消勾选并保存后 AI 设置 thinkMode=false")
        n0 = pg.evaluate("window.__probe.log.length")
        open_judge_cfg(pg)
        fire(pg)
        ck(pg.evaluate("window.__probe.log.length") > n0, "判卷再次发出请求")
        b2 = body_of(last_req(pg))
        ck(b2.get("thinking", {}).get("type") == "disabled",
           "判卷请求体 thinking.type == disabled → %s" % b2.get("thinking"))
        ck(b2.get("max_tokens") == 32000, "额度仍走思考档 32000（关思考也不截断判卷 JSON）")
        clear_masks(pg)

        # ---------------------------------------------- 场景 3：Anthropic 分支
        print("\n[场景 3] 判卷 Provider = Anthropic：开思考需 thinking + temperature=1")
        pg.evaluate("() => localStorage.setItem('ai_optics_v1_judge', JSON.stringify({provider:'anthropic', model:'', baseUrl:''}))")
        pg.evaluate("() => localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({provider:'zhipu', apikey:'sk-e2e', model:'', baseUrl:'', thinkMode:true}))")
        open_judge_cfg(pg)
        fire(pg)
        r3 = last_req(pg)
        b3 = body_of(r3)
        ck("/v1/messages" in (r3["url"] if r3 else ""), "打到 Anthropic 端点")
        ck(b3.get("thinking", {}).get("type") == "enabled", "anthropic 开思考 thinking=enabled → %s" % b3.get("thinking"))
        ck(b3.get("temperature") == 1, "anthropic 开思考时 temperature 强制为 1")
        clear_masks(pg)
        pg.evaluate("() => localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({provider:'zhipu', apikey:'sk-e2e', model:'', baseUrl:'', thinkMode:false}))")
        open_judge_cfg(pg)
        fire(pg)
        b4 = body_of(last_req(pg))
        ck(b4.get("thinking", {}).get("type") == "disabled", "anthropic 关思考 thinking=disabled")
        ck(b4.get("temperature") == 0.1, "anthropic 关思考时保留判卷自身 temperature(0.1)")
        clear_masks(pg)

        # ---------------------------------------------- 场景 4：健康度 / 回归基线
        print("\n[场景 4] 页面健康度与回归基线")
        ck(pg.evaluate("(window.__rbErrors||[]).length") == 0, "作品自带错误账本 __rbErrors 为空")
        ck(pg.evaluate("!!document.getElementById('__rbOverlay')") is False, "启动失败浮层不存在")
        ck(pg.evaluate("window.__APP_READY === true") is True, "__APP_READY 已置真")
        ck(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "导航按钮 11 个")
        ck(pg.evaluate("document.querySelectorAll('.panel').length") == 12, "面板 12 个")
        ck(pg.evaluate("document.querySelectorAll('canvas').length") == 11, "画布 11 个")
        ck(pg.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object'") is True, "MODULES / REPORT 仍在")
        real = [e for e in errs if not any(k in e for k in
                ("Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "favicon"))]
        ck(len(real) == 0, "控制台无真实错误 %s" % (real[:2] if real else ""))
        ctx.close()

        # ---------------------------------------------- 场景 5：超时来自 window
        print("\n[场景 5] 判卷超时读的是 window.AI_TIMEOUT_MS（把 window 钉成 3000ms 实测 abort 时刻）")
        ctx2 = b.new_context(viewport={"width": 1440, "height": 900})
        ctx2.add_init_script(HANG)
        pg2 = ctx2.new_page()
        pg2.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg2.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg2.on("dialog", lambda d: d.dismiss())
        pg2.goto(url, wait_until="domcontentloaded")
        pg2.wait_for_timeout(1600)
        first_run(pg2)
        ck(pg2.evaluate("window.__mode") == "hang", "桩已切到 hang 模式")
        ck(pg2.evaluate("window.AI_TIMEOUT_MS") == 3000, "window.AI_TIMEOUT_MS 已被钉成 3000")
        open_judge_cfg(pg2)
        pg2.click('#judgeCfgTest')
        pg2.wait_for_timeout(4200)
        info = pg2.evaluate("() => { const l = window.__probe.log; return { n: l.length, t0: l[0] && l[0].t0, ab: l[0] && l[0].aborted }; }")
        ck(info["n"] == 1, "悬挂请求只发 1 次（超时不重试）→ n=%s" % info["n"])
        if info.get("ab"):
            ms = round(info["ab"] - info["t0"])
            ck(2500 <= ms <= 3900, "abort 实测 %d ms ≈ window 值 3000（若仍写死 20s 会等到 20000）" % ms)
        else:
            ck(False, "请求未被 abort —— 说明超时没走 window 值")
        txt = pg2.evaluate("() => (document.getElementById('jcTestResult')||{}).textContent || ''")
        ck("3 秒未响应" in txt, "判卷超时文案用了实际超时值：%s" % txt.strip()[:90])
        ctx2.close()
        b.close()

    print("\n" + "=" * 66)
    print("PASS %d / FAIL %d" % (len(OK), len(BAD)))
    for m in BAD:
        print("  FAIL: " + m)
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
