# -*- coding: utf-8 -*-
"""V6.4.21 e2e：AI 请求单次超时 20s -> 45s

证明思路（不靠"感觉"，全部拿到毫秒级实测数字）：
  用 add_init_script 在页面脚本之前把 window.fetch 换成可控桩，
  桩只拦 LLM 请求，并用自己的 AbortController signal 监听 abort 时刻，
  于是每次尝试「开始 / 被超时掐断」的时间戳都能精确读到。

  T1 问 AI：桩延迟 25s 后返回 → 必须成功。
      ← 这一条直接推翻 20s：以前 20s 必被掐断（且重试再掐一次），现在能等到答案。
  T2 问 AI：桩永不返回 → 读 abort 时间戳，证明"单次 45s、重试 1 次、总 90s"。
  T3 诊断：桩永不返回 → 提示文案必须是「45 秒未响应」并落进本地知识库兜底。
  T4 诊断：桩延迟 25s 后返回 → 必须出 AI 报告，不再掉本地兜底。
"""
import pathlib, json
from playwright.sync_api import sync_playwright

FILE = "光学交互实验室_AI_v6.4.21.html"
url = pathlib.Path(FILE).resolve().as_uri()
PASS, FAIL = [], []


def ck(cond, label, extra=""):
    (PASS if cond else FAIL).append(label + (("  <" + str(extra) + ">") if extra and not cond else ""))
    print(("  OK   " if cond else "  FAIL ") + label + (("   " + str(extra)) if not cond else ""))


INIT = r"""
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({
      provider:'zhipu', apikey:'sk-e2e-stub', model:'glm-4.7-flash',
      baseUrl:'https://open.bigmodel.cn/api/paas/v4', thinkMode:false
    }));
    localStorage.setItem('ai_optics_v1_judge', JSON.stringify({
      provider:'zhipu', apikey:'sk-e2e-stub', model:'glm-4.7-flash',
      baseUrl:'https://open.bigmodel.cn/api/paas/v4'
    }));
    sessionStorage.setItem('ai_optics_v1_keyClearAsked','1');
  }catch(e){}

  window.__aiStub = { mode:'hang', delayMs:0 };
  window.__fetchLog = [];
  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(u, o){
    var s = String(u||'');
    var isLLM = s.indexOf('chat/completions') >= 0 || s.indexOf('/v1/messages') >= 0;
    if(!isLLM) return orig ? orig(u, o) : Promise.reject(new Error('no fetch'));
    var rec = { url:s, t0: performance.now(), aborted:null, ok:null };
    window.__fetchLog.push(rec);
    return new Promise(function(resolve, reject){
      var sig = o && o.signal;
      if(sig && sig.addEventListener){
        sig.addEventListener('abort', function(){
          rec.aborted = performance.now();
          var e = new Error('The user aborted a request.'); e.name = 'AbortError'; reject(e);
        });
      }
      var body = JSON.stringify({ choices:[{message:{content:'STUB-OK 这是桩返回的答案。'}}], usage:{total_tokens:7} });
      var mk = function(){ rec.ok = performance.now(); resolve(new Response(body, {status:200, headers:{'Content-Type':'application/json'}})); };
      var st = window.__aiStub || {};
      if(st.mode === 'ok') mk();
      else if(st.mode === 'delay') setTimeout(mk, st.delayMs || 25000);
      /* mode === 'hang'：永不 resolve，只等 signal 超时 abort */
    });
  };
})();
"""


def boot(b, stub):
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("dialog", lambda d: d.dismiss())        # 面板里的 prompt() 不能卡住
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600)
        pg.fill("#stuName", "超时测试"); pg.fill("#stuNo", "T99")
        pg.click("#stuAdd", timeout=15000); pg.wait_for_timeout(700)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m=>{
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.evaluate("(s) => { window.__aiStub = s; }", stub)
    return ctx, pg, errs


def hit_ask(pg, timeout_s):
    """问 AI：打开 → 提问 → 等结果落定"""
    pg.click("#topChat"); pg.wait_for_timeout(400)
    pg.fill("#aiAskInput", "光在真空中的传播速度是多少？")
    pg.click("#aiAskSubmit")
    pg.wait_for_function("""() => {
        const el = document.getElementById('aiAskResult');
        if(!el) return false;
        const t = el.textContent || '';
        return t.indexOf('STUB-OK') >= 0 || t.indexOf('45 秒') >= 0 || t.indexOf('⚠️') >= 0 || t.indexOf('失败') >= 0;
    }""", timeout=timeout_s * 1000)
    return pg.evaluate("() => document.getElementById('aiAskResult').textContent")


def hit_diag(pg, timeout_s):
    """诊断：走顶栏「诊断」按钮（与真实 UI 同一入口）→ 开始诊断 → 等结果落定"""
    pg.click("#topDiag"); pg.wait_for_timeout(500)
    pg.click("#aiDiagGo")
    pg.wait_for_function("""() => {
        const el = document.getElementById('aiDiagResult');
        if(!el) return false;
        const t = el.textContent || '';
        return t.indexOf('STUB-OK') >= 0 || t.indexOf('45 秒') >= 0 || t.indexOf('⚠️') >= 0;
    }""", timeout=timeout_s * 1000)
    return pg.evaluate("() => document.getElementById('aiDiagResult').textContent")


def fetch_log(pg):
    return pg.evaluate("() => window.__fetchLog.map(r => ({t0:r.t0, aborted:r.aborted, ok:r.ok}))")


with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------------- 静态回归（一页搞定） ----------------
    print("\n[A] 版本与回归基线")
    ctx, pg, errs = boot(b, {"mode": "ok", "delayMs": 0})
    ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本为空")
    ck(not pg.query_selector("#__rbOverlay"), "无启动失败浮层")
    ck(pg.evaluate("window.__APP_READY === true"), "APP_READY 已置真")
    ck(pg.inner_text(".ver-badge").strip() == "v6.4.21", "角标 = v6.4.21", pg.inner_text(".ver-badge"))
    bt = pg.get_attribute(".ver-badge", "title") or ""
    ck("V6.4.21" in bt and "45" in bt, "角标 title 已更新", bt[:70])
    ck(pg.evaluate("""() => [...document.querySelectorAll('.log-item .log-ver')][0].textContent === 'V6.4.21'"""),
       "更新日志首条 = V6.4.21")
    log1 = pg.evaluate("""() => document.querySelectorAll('.log-item')[0].querySelector('p').textContent""").strip()
    ck(len(log1) <= 20, "日志文案 ≤20 字", "%s (%d)" % (log1, len(log1)))
    ck(pg.evaluate("""() => document.querySelectorAll('.log-item.cur').length === 1"""), "cur 唯一")
    ck(pg.evaluate("""() => [...document.querySelectorAll('.log-item .log-ver')][1].textContent === 'V6.4.19'"""),
       "上一版 V6.4.19 条目保留")
    ck(pg.evaluate("() => document.querySelectorAll('.tab-btn').length === 11"), ".tab-btn = 11")
    ck(pg.evaluate("() => document.querySelectorAll('.panel').length === 12"), ".panel = 12")
    ck(pg.evaluate("() => document.querySelectorAll('canvas').length === 11"), "canvas = 11")
    ck(pg.evaluate("() => typeof MODULES==='object' && typeof REPORT==='object' && typeof S3D==='object'"),
       "MODULES / REPORT / S3D 仍在")
    ctx.close()

    # ---------------- T1 问 AI：延迟 25s 必须成功（推翻 20s） ----------------
    print("\n[T1] 问 AI · 桩延迟 25s 返回 → 必须成功（20s 时代必被掐断）")
    ctx, pg, errs = boot(b, {"mode": "delay", "delayMs": 25000})
    txt = hit_ask(pg, 60)
    lg = fetch_log(pg)
    ck("STUB-OK" in txt, "问 AI 拿到了 25s 后才返回的答案", txt[:90])
    ck("45 秒" not in txt, "没有出现超时提示")
    ck(len(lg) == 1, "只发了 1 次请求（没被掐断重试）", len(lg))
    ck(lg and lg[0]["aborted"] is None, "第 1 次尝试未被 abort", lg)
    ck(lg and lg[0]["ok"] and lg[0]["ok"] - lg[0]["t0"] >= 24000,
       "确实等满了约 25s 才返回", lg and round(lg[0]["ok"] - lg[0]["t0"]))
    ck(lg and lg[0]["ok"] - lg[0]["t0"] < 40000, "也没有超过 45s 才返回")
    ctx.close()

    # ---------------- T2 问 AI：永不返回 → 精确读 abort 时间戳 ----------------
    print("\n[T2] 问 AI · 桩永不返回 → 实测单次超时值（预期 45s × 2 次）")
    ctx, pg, errs = boot(b, {"mode": "hang", "delayMs": 0})
    txt = hit_ask(pg, 130)
    lg = fetch_log(pg)
    ck("45 秒" in txt, "提示文案已是「45 秒未响应」", txt[:110])
    ck("已自动重试 1 次" in txt, "文案保留「已自动重试 1 次」", txt[:110])
    ck(len(lg) == 2, "共 2 次尝试（= 重试 1 次）", len(lg))
    if len(lg) == 2:
        a1 = lg[0]["aborted"] - lg[0]["t0"]
        a2 = lg[1]["aborted"] - lg[1]["t0"]
        ck(43000 <= a1 <= 50000, "第 1 次尝试在约 45s 被掐断（实测 %d ms）" % round(a1), round(a1))
        ck(43000 <= a2 <= 50000, "第 2 次尝试同样约 45s（实测 %d ms）" % round(a2), round(a2))
        # 重试是紧接着发起的（两条记录首尾相接），总耗时因此 ≈ 45s × 2
        gap = lg[1]["t0"] - lg[0]["aborted"]
        total = lg[1]["aborted"] - lg[0]["t0"]
        ck(-50 <= gap <= 3000, "第 2 次紧接着第 1 次失败发起（间隔 %.0f ms）" % gap, round(gap))
        ck(88000 <= total <= 98000, "整体等待 ≈ 90s 才落兜底（实测 %d ms）" % round(total), round(total))
    ctx.close()

    # ---------------- T3 诊断：永不返回 → 45s 文案 + 本地兜底 ----------------
    print("\n[T3] 诊断 · 桩永不返回 → 45s 文案 + 落本地知识库兜底")
    ctx, pg, errs = boot(b, {"mode": "hang", "delayMs": 0})
    txt = hit_diag(pg, 130)
    lg = fetch_log(pg)
    ck("45 秒" in txt, "诊断侧同样是 45s 文案（同一条 callLLM 链路）", txt[:110])
    ck("本地知识库" in txt or "本地" in txt, "已落本地知识库兜底", txt[:150])
    ck(len(lg) == 2, "诊断也是 2 次尝试", len(lg))
    if len(lg) == 2:
        a1 = lg[0]["aborted"] - lg[0]["t0"]
        ck(43000 <= a1 <= 50000, "诊断单次尝试亦约 45s（实测 %d ms）" % round(a1), round(a1))
    ctx.close()

    # ---------------- T4 诊断：延迟 25s 返回 → 出 AI 报告 ----------------
    print("\n[T4] 诊断 · 桩延迟 25s 返回 → 必须出 AI 报告，不掉兜底")
    ctx, pg, errs = boot(b, {"mode": "delay", "delayMs": 25000})
    txt = hit_diag(pg, 60)
    lg = fetch_log(pg)
    ck("STUB-OK" in txt, "诊断拿到了 25s 后才返回的报告", txt[:90])
    ck("本地知识库" not in txt, "没有掉进本地知识库兜底")
    ck(len(lg) == 1 and lg[0]["aborted"] is None, "只发 1 次且未被 abort", len(lg))
    ctx.close()

    # ---------------- T5 立即成功（回归：正常路径没被改坏） ----------------
    print("\n[T5] 桩立即返回 → 正常路径回归")
    ctx, pg, errs = boot(b, {"mode": "ok", "delayMs": 0})
    txt = hit_ask(pg, 30)
    lg = fetch_log(pg)
    ck("STUB-OK" in txt, "秒回路径正常")
    ck(len(lg) == 1, "只发 1 次请求", len(lg))
    noise = [e for e in errs if not any(x in e for x in
             ("Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "favicon"))]
    ck(len(noise) == 0, "期间无真实控制台错误", noise[:3])
    ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本仍为空")
    ctx.close()

    b.close()

print("\n" + "=" * 64)
print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("  ✗", f)
print("=" * 64)
