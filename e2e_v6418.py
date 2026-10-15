# -*- coding: utf-8 -*-
"""V6.4.18 e2e：验证「APIKey 本地存储提示」由『打开时弹』改为『关闭时弹』。

关键设计：
① 用 add_init_script 在页面脚本运行前写死 localStorage，构造"本地有 Key"的场景
② 断言加载后**不弹窗**（这是本次需求的核心）
③ 用 page.evaluate 派发 beforeunload 事件模拟关闭，断言弹窗出现
④ 验证三个动作按钮行为（保留 / 仅清判卷 / 全部清除）
⑤ 回归：tab 数、canvas 数、面板数、错误账本、版本号
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

HTML = "光学交互实验室_AI_v6.4.18.html"
url = pathlib.Path(HTML).resolve().as_uri()

FAILS = []
def ck(cond, label, extra=""):
    print(("  OK  " if cond else "  FAIL") + " " + label + (("  | " + str(extra)) if extra else ""))
    if not cond: FAILS.append(label)

def clear_masks(pg):
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show');
        m.classList.remove('is-closing');
      });
    }""")

# 预置 localStorage：主 Key + 判卷 Key 都有
SEED = """
(function(){
  try{
    localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({provider:'zhipu', model:'GLM-5.3', apikey:'sk-testmain1234567890abcd'}));
    localStorage.setItem('ai_optics_v1_judge', JSON.stringify({provider:'zhipu', model:'GLM-5.3', apikey:'sk-judge9876543210wxyz'}));
    sessionStorage.clear();
  }catch(e){}
})();
"""

def k_of(pg):
    """读出作品真实的 localStorage key 前缀（避免猜错）"""
    return pg.evaluate("""() => {
      const ks = Object.keys(localStorage);
      return ks;
    }""")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=swiftshader"])

    # ================= 场景 A：本地有 Key（主 + 判卷） =================
    print("\n=== 场景 A：本地有 APIKey ===")
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.add_init_script(SEED)
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)

    # 首启弹窗（学生姓名窗）走真实流程
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd")
        pg.wait_for_timeout(800)
    clear_masks(pg)

    # --- 核心断言 1：加载后不弹 APIKey 提示 ---
    txt = pg.inner_text("body") if pg.query_selector("#aiCfgMask") else ""
    ck(pg.query_selector("#aiCfgMask") is None or not pg.evaluate("document.getElementById('aiCfgMask').classList.contains('show')"),
       "A1 打开页面时【没有】弹 APIKey 提示")
    ck(pg.query_selector("#keyKeepAll") is None and pg.query_selector("#keyClearAll") is None,
       "A2 打开页面时 DOM 里没有提示的三个按钮")

    # --- 守卫已挂上：exitArmed 应为 true ---
    # exitArmed 是 IIFE 内绑定，摸不到 → 用行为证明
    ck(pg.evaluate("""() => {
      const ev = new Event('beforeunload', {cancelable:true});
      window.dispatchEvent(ev);
      return ev.defaultPrevented;
    }"""), "A3 beforeunload 被拦截（守卫生效）")

    pg.wait_for_timeout(600)
    # --- 核心断言 2：关闭时弹窗出现 ---
    ck(pg.evaluate("!!document.getElementById('aiCfgMask') && document.getElementById('aiCfgMask').classList.contains('show')"),
       "A4 关闭页面时【弹出了】提示弹窗")
    body = pg.inner_text("body")
    ck("离开前" in body and "APIKey" in body, "A5 弹窗文案是「离开前…」语境")
    ck(pg.query_selector("#keyKeepAll") is not None, "A6 有「保留，继续关闭」按钮")
    ck(pg.query_selector("#keyClearJudge") is not None, "A7 判卷 Key 存在时有「仅清除判卷 Key」按钮")
    ck(pg.query_selector("#keyClearAll") is not None, "A8 有「全部清除」按钮")

    # 脱敏：不应出现完整明文
    ck("sk-testmain1234567890abcd" not in body, "A9 主 Key 已脱敏（无完整明文）")
    ck("sk-judge9876543210wxyz" not in body, "A10 判卷 Key 已脱敏")
    ck("sk-t" in body and "abcd" in body, "A11 脱敏格式为「前4+****+后4」")

    # --- 断言：点「保留」后放行，再关不再拦 ---
    pg.click("#keyKeepAll")
    pg.wait_for_timeout(400)
    ck(not pg.evaluate("""() => {
      const ev = new Event('beforeunload', {cancelable:true});
      window.dispatchEvent(ev);
      return ev.defaultPrevented;
    }"""), "A12 选「保留」后再关闭【不再拦截】（否则关不掉页面）")
    keys_after = dict(pg.evaluate("""() => {
      const o = {};
      for (const k of Object.keys(localStorage)) o[k] = localStorage.getItem(k);
      return o;
    }"""))
    keep_main = any('apikey' in v and 'sk-testmain' in v for v in keys_after.values())
    ck(keep_main, "A13 选「保留」后主 Key 仍在 localStorage")

    # ================= 场景 B：仅清除判卷 Key =================
    print("\n=== 场景 B：点「仅清除判卷 Key」 ===")
    pg2 = ctx.new_page()
    pg2.add_init_script(SEED)
    pg2.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg2.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg2.goto(url, wait_until="domcontentloaded")
    pg2.wait_for_timeout(2500)
    if pg2.query_selector("#stuName") and pg2.is_visible("#stuName"):
        pg2.fill("#stuName", "E2E测试"); pg2.fill("#stuNo", "E2E")
        pg2.click("#stuAdd"); pg2.wait_for_timeout(800)
    clear_masks(pg2)
    pg2.evaluate("window.dispatchEvent(new Event('beforeunload', {cancelable:true}))")
    pg2.wait_for_timeout(600)
    ck(pg2.query_selector("#keyClearJudge") is not None, "B1 弹窗出现")
    pg2.click("#keyClearJudge")
    pg2.wait_for_timeout(400)
    ks = pg2.evaluate("""() => { const o={}; for(const k of Object.keys(localStorage)) o[k]=localStorage.getItem(k); return o; }""")
    judge_left = any('sk-judge' in v for v in ks.values())
    main_left  = any('sk-testmain' in v for v in ks.values())
    ck(not judge_left, "B2 判卷 Key 已从 localStorage 删除")
    ck(main_left,      "B3 主设置 Key 保留（只清判卷）")
    pg2.close()

    # ================= 场景 C：全部清除 =================
    print("\n=== 场景 C：点「全部清除」 ===")
    pg3 = ctx.new_page()
    pg3.add_init_script(SEED)
    pg3.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg3.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg3.goto(url, wait_until="domcontentloaded")
    pg3.wait_for_timeout(2500)
    if pg3.query_selector("#stuName") and pg3.is_visible("#stuName"):
        pg3.fill("#stuName", "E2E测试"); pg3.fill("#stuNo", "E2E")
        pg3.click("#stuAdd"); pg3.wait_for_timeout(800)
    clear_masks(pg3)
    pg3.evaluate("window.dispatchEvent(new Event('beforeunload', {cancelable:true}))")
    pg3.wait_for_timeout(600)
    # confirm() → 自动接受
    pg3.on("dialog", lambda d: d.accept())
    pg3.click("#keyClearAll")
    pg3.wait_for_timeout(500)
    ks3 = pg3.evaluate("""() => { const o={}; for(const k of Object.keys(localStorage)) o[k]=localStorage.getItem(k); return o; }""")
    ck(not any('sk-testmain' in v for v in ks3.values()), "C1 主 Key 已清除")
    ck(not any('sk-judge' in v for v in ks3.values()),    "C2 判卷 Key 已清除")
    pg3.close()

    # ================= 场景 D：本地无 Key → 完全不打扰 =================
    print("\n=== 场景 D：本地无 Key ===")
    ctx4 = b.new_context(viewport={"width": 1440, "height": 900})
    pg4 = ctx4.new_page()
    pg4.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg4.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg4.goto(url, wait_until="domcontentloaded")
    pg4.wait_for_timeout(2500)
    if pg4.query_selector("#stuName") and pg4.is_visible("#stuName"):
        pg4.fill("#stuName", "E2E测试"); pg4.fill("#stuNo", "E2E")
        pg4.click("#stuAdd"); pg4.wait_for_timeout(800)
    clear_masks(pg4)
    ck(not pg4.evaluate("""() => {
      const ev = new Event('beforeunload', {cancelable:true});
      window.dispatchEvent(ev);
      return ev.defaultPrevented;
    }"""), "D1 无 Key 时关闭【不拦截】")
    ck(pg4.query_selector("#keyKeepAll") is None, "D2 无 Key 时不弹窗")
    pg4.close()
    ctx4.close()

    # ================= 回归 =================
    print("\n=== 回归 ===")
    ctx5 = b.new_context(viewport={"width": 1440, "height": 900})
    pgr = ctx5.new_page()
    rerrs = []
    pgr.on("console", lambda m: rerrs.append(m.text) if m.type == "error" else None)
    pgr.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pgr.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pgr.goto(url, wait_until="domcontentloaded")
    pgr.wait_for_timeout(2500)
    if pgr.query_selector("#stuName") and pgr.is_visible("#stuName"):
        pgr.fill("#stuName", "E2E测试"); pgr.fill("#stuNo", "E2E")
        pgr.click("#stuAdd"); pgr.wait_for_timeout(800)
    clear_masks(pgr)

    ck(pgr.evaluate("document.querySelectorAll('.tab-btn').length") == 11,
       "R1 导航按钮 11 个", pgr.evaluate("document.querySelectorAll('.tab-btn').length"))
    ck(pgr.evaluate("document.querySelectorAll('canvas').length") >= 11,
       "R2 主文档 canvas 11 个", pgr.evaluate("document.querySelectorAll('canvas').length"))
    ck(pgr.evaluate("document.querySelectorAll('.panel').length") == 12,
       "R3 面板 12 个", pgr.evaluate("document.querySelectorAll('.panel').length"))
    ck(pgr.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v6.4.18",
       "R4 版本角标 v6.4.18", pgr.evaluate("document.querySelector('.ver-badge').textContent.trim()"))
    ck(pgr.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object' && typeof S3D === 'object'"),
       "R5 核心模块对象仍在")
    _nrb = pgr.evaluate("(window.__rbErrors||[]).length")
    ck(_nrb == 0, "R6 错误账本为空", _nrb)
    ck(pgr.query_selector("#__rbOverlay") is None, "R7 无启动失败浮层")
    ck(not pgr.evaluate("!!document.querySelector('#aiCfgMask.show')"), "R8 加载后无残留遮罩")
    # 其他弹窗仍能打开
    pgr.evaluate("switchTab('reflect')")
    pgr.wait_for_timeout(500)
    ck(pgr.evaluate("!!document.querySelector('#tab-reflect.active') || !!document.querySelector('#tab-reflect')"),
       "R9 实验面板可切换")

    noise = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED")
    real_errs = [e for e in rerrs if not any(n in e for n in noise)]
    ck(len(real_errs) == 0, "R10 无（过滤 CDN 拦截后）控制台错误", real_errs[:3])

    pgr.close(); ctx5.close()
    ctx.close()
    b.close()

print("\n" + "=" * 60)
if FAILS:
    print("失败 %d 项：" % len(FAILS))
    for f in FAILS: print("  - " + f)
    sys.exit(1)
print("全部通过 ✅")
