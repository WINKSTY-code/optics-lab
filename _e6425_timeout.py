# -*- coding: utf-8 -*-
"""V6.4.25 e2e：真实 Chromium 驱动「诊断」弹窗，换 window.fetch 为可控桩。
断言：
 1) 网络错误(TypeError) -> 仍重试，共 2 次请求
 2) 超时(AbortError)   -> 不再重试，仅 1 次请求
 3) 等待文案          -> 出现「可能需要 1-2 分钟」
 4) 超时错误文案      -> 出现「180 秒未响应」且不再出现「已自动重试 1 次」
 5) 真实悬挂请求       -> AbortController 在 ~180s 触发（验证常量确为 180000）
"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

HTML = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.25.html"
URL = "file:///" + HTML.replace("\\", "/")

STUB = r"""
window.__probe = { calls: 0, aborts: [] };
window.__mode = 'pass';
(function(){
  var real = window.fetch;
  window.fetch = function(url, opts){
    var m = window.__mode;
    var n = ++window.__probe.calls;
    if(m === 'hang'){
      var t0 = performance.now();
      return new Promise(function(res, rej){
        if(opts && opts.signal){
          opts.signal.addEventListener('abort', function(){
            window.__probe.aborts.push({call:n, ms: Math.round(performance.now()-t0)});
            var e; try{ e = new DOMException('aborted','AbortError'); }catch(_){ e = new Error('aborted'); e.name='AbortError'; }
            rej(e);
          });
        }
      });
    }
    if(m === 'abort'){ var e2 = new Error('aborted'); e2.name = 'AbortError'; return Promise.reject(e2); }
    if(m === 'neterr'){ return Promise.reject(new TypeError('Failed to fetch')); }
    return real.apply(this, arguments);
  };
})();
"""

CFG = ('{"provider":"zhipu","apikey":"sk-test-only","model":"GLM-5.3-Flash",'
       '"baseUrl":"","thinkMode":true}')

results = []
def check(tag, cond, detail=""):
    results.append((tag, cond, detail))
    print(("  ✅ " if cond else "  ❌ ") + tag + ("  | " + detail if detail else ""))

with sync_playwright() as p:
    br = p.chromium.launch(headless=True)
    ctx = br.new_context()
    ctx.add_init_script(STUB)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.evaluate("localStorage.setItem('ai_optics_v1_cfg', %s)" % repr(CFG))
    pg.reload(wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    # 进入页时可能自动弹出 AI 设置遮罩，会拦截点击 —— 先全部关掉
    pg.evaluate("document.querySelectorAll('.modal-mask.show')"
                ".forEach(function(m){ m.classList.remove('show'); });")
    pg.wait_for_timeout(300)

    print("=== V6.4.25 超时/重试 e2e ===")

    # ---- 场景 1：网络错误 -> 应重试（2 次） ----
    print("\n[1] 网络错误(TypeError) -> 期望重试，共 2 次请求")
    pg.evaluate("window.__probe.calls = 0; window.__mode = 'neterr';")
    pg.click("#topDiag"); pg.wait_for_timeout(600)
    pg.click("#aiDiagGo"); pg.wait_for_timeout(4000)
    calls = pg.evaluate("window.__probe.calls")
    txt = pg.inner_text("#aiDiagResult")
    check("网络错误仍重试（2 次请求）", calls == 2, "实际 %d 次" % calls)
    check("提示已重试", "重试" in txt, txt.strip().replace("\n", " ")[:90])

    # ---- 场景 2：超时(AbortError) -> 不应重试（1 次） ----
    print("\n[2] 超时(AbortError) -> 期望不重试，共 1 次请求")
    pg.evaluate("window.__probe.calls = 0; window.__mode = 'abort';")
    pg.click("#aiDiagGo"); pg.wait_for_timeout(3500)
    calls2 = pg.evaluate("window.__probe.calls")
    txt2 = pg.inner_text("#aiDiagResult")
    check("超时不再重试（1 次请求）", calls2 == 1, "实际 %d 次" % calls2)
    check("超时文案含 180 秒未响应", "180 秒未响应" in txt2, txt2.strip().replace("\n", " ")[:110])
    check("超时文案不再提「已自动重试」", "已自动重试" not in txt2, "")
    check("超时后仍降级到本地知识库", "本地知识库" in txt2 or "本地知識庫" in txt2, "")

    # ---- 场景 3：等待文案 ----
    print("\n[3] 等待文案 -> 期望出现「可能需要 1-2 分钟」")
    pg.evaluate("window.__probe.calls = 0; window.__mode = 'hang';")
    pg.click("#aiDiagGo"); pg.wait_for_timeout(1500)
    wait_txt = pg.inner_text("#aiDiagResult")
    check("等待时显示 1-2 分钟提示", "可能需要 1-2 分钟" in wait_txt,
          wait_txt.strip().replace("\n", " ")[:90])
    check("旧的「若未配置 API Key」已消失", "若未配置 API Key" not in wait_txt, "")

    # ---- 场景 4：真实悬挂 -> 量 AbortController 触发时刻（≈180s） ----
    print("\n[4] 真实悬挂请求 -> 量超时触发时刻（预计 ~180s，请稍候）")
    t0 = time.time()
    try:
        pg.wait_for_function("window.__probe.aborts.length > 0", timeout=220000)
    except Exception as e:
        print("  ⚠️ 等待超时异常:", str(e)[:120])
    elapsed = time.time() - t0
    aborts = pg.evaluate("window.__probe.aborts")
    calls4 = pg.evaluate("window.__probe.calls")
    if aborts:
        ms = aborts[0]["ms"]
        check("超时常量确为 180s（实测 %.1fs）" % (ms / 1000.0),
              175000 <= ms <= 195000, "abort@%d ms" % ms)
    else:
        check("捕获到 abort 事件", False, "未捕获，实际等待 %.1fs" % elapsed)
    check("悬挂场景仍只有 1 次请求（不重试）", calls4 == 1, "实际 %d 次" % calls4)

    br.close()

print("\n=== 汇总 ===")
ok = sum(1 for _, c, _ in results if c)
print(f"{ok}/{len(results)} 通过")
for tag, c, d in results:
    print(("  ✅ " if c else "  ❌ ") + tag + ("  | " + d if d else ""))
sys.exit(0 if ok == len(results) else 1)
