# -*- coding: utf-8 -*-
"""V6.9.5 e2e：真实 Chromium 走 AI 设置，断言 anthropic 下拉完整选项序列 + 截图取证。
遵循 §41：打开配置弹窗后绝不再 clear_masks；语言切换走「关弹窗→切→重开」。"""
import pathlib, sys
from playwright.sync_api import sync_playwright

D = pathlib.Path("光学交互实验室_AI_v6.9.5.html").resolve()
url = D.as_uri()
OUT = pathlib.Path(".")
fails = []

def ck(cond, msg):
    print(("OK  " if cond else "FAIL") + "  " + msg)
    if not cond: fails.append(msg)

def clear_masks(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing'); m.style.display=''; });""")

def dismiss_first_run(pg):
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd")
        pg.wait_for_timeout(800)

EXPECT = {
    "openai":    ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-6.1-sol", "gpt-5.6-sol", "gpt-5.6-luna", "__custom__"],
    "anthropic": ["claude-fable-5.1", "claude-opus-5.5", "claude-haiku-5.5", "claude-opus-5", "__custom__"],
    "zhipu":     ["GLM-5.3-FlashX", "GLM-5.3", "GLM-5.3-Flash", "GLM-4.5-Air", "__custom__"],
    "minimax":   ["MiniMax-M3", "MiniMax-M3.1-Flash-Preview", "MiniMax-M2.7", "__custom__"],
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    # 截图会等 document.fonts.ready，外链字体不可达必卡 30s → goto 前就 abort（§59③）
    pg.route("**/cdn.jsdelivr.net/**",   lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**",   lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("dialog", lambda d: d.dismiss())

    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    print("[调试] 首启窗可见 =", pg.is_visible("#stuName"))
    print("[调试] 当前遮罩 =", pg.evaluate(
        "() => [...document.querySelectorAll('.modal-mask')].map(m=>m.id+(m.classList.contains('show')?'(show)':''))"))
    dismiss_first_run(pg)
    clear_masks(pg)
    print("[调试] 清理后遮罩 =", pg.evaluate(
        "() => [...document.querySelectorAll('.modal-mask')].map(m=>m.id+(m.classList.contains('show')?'(show)':''))"))

    # 作品自带健康信号
    rb = pg.evaluate("(window.__rbErrors||[]).length")
    ck(rb == 0, "作品错误账本为空 (__rbErrors=%d)" % rb)
    ck(not pg.evaluate("!!document.getElementById('__rbOverlay')"), "启动失败浮层不存在")

    # 打开 AI 设置（顶栏「设置」下拉 → AI 设置）
    pg.click("#setBtn")
    pg.wait_for_timeout(500)
    pg.click("#aiCfgBtn")
    pg.wait_for_timeout(1000)
    ck(pg.is_visible("#aiProvider"), "AI 设置弹窗已打开（#aiProvider 可见）")

    # 逐个 provider 断言完整选项序列（§59⑦）
    for prov, exp in EXPECT.items():
        pg.select_option("#aiProvider", prov)
        pg.wait_for_timeout(500)
        r = pg.evaluate("""() => { const s=document.getElementById('aiModel');
            return { values:[...s.options].map(o=>o.value),
                     sel:s.options[s.selectedIndex].value }; }""")
        ck(r["values"] == exp, "%s 模型列表精确匹配 实得 %s" % (prov, r["values"]))

    # 取证：选中 claude-haiku-5.5 后截「模型」控件区域
    pg.select_option("#aiProvider", "anthropic")
    pg.wait_for_timeout(400)
    pg.select_option("#aiModel", "claude-haiku-5.5")
    pg.wait_for_timeout(600)
    box = pg.query_selector("#aiModel").bounding_box()
    clip = {"x": box["x"] - 40, "y": box["y"] - 76, "width": box["width"] + 80, "height": 170}
    pg.screenshot(path=str(OUT / "_v695_证据_anthropic_haiku55.png"), clip=clip)

    # 三语循环：关弹窗 → 切语言 → 重开弹窗（§41③）
    for lang, name in [("zht", "繁"), ("en", "英")]:
        pg.evaluate("() => window.closeModal && closeModal()")
        pg.wait_for_timeout(400)
        clear_masks(pg)     # 上一轮的弹窗；本轮断言在重新打开之后，不受此影响（§41① 的例外）
        # 菜单用 hidden 控制显隐；这里直接走 langBtn 自身的 click 监听（菜单显隐与本用例无关）
        pg.evaluate("() => document.getElementById('langBtn').click()")
        pg.wait_for_timeout(900)
        ck(pg.evaluate("LANG") == lang, "语言切到 %s (%s) 实得 %s" % (lang, name, pg.evaluate("LANG")))
        pg.click("#setBtn")
        pg.wait_for_timeout(400)
        pg.click("#aiCfgBtn")
        pg.wait_for_timeout(900)
        pg.select_option("#aiProvider", "anthropic"); pg.wait_for_timeout(400)
        pg.select_option("#aiModel", "claude-haiku-5.5"); pg.wait_for_timeout(500)
        bx = pg.query_selector("#aiModel").bounding_box()
        pg.screenshot(path=str(OUT / ("_v695_证据_anthropic_%s.png" % lang)),
                      clip={"x": bx["x"] - 40, "y": bx["y"] - 76, "width": bx["width"] + 80, "height": 170})
        pg.evaluate("() => window.closeModal && closeModal()")
        pg.wait_for_timeout(400)
    # 切回中文
    pg.evaluate("() => document.getElementById('langBtn').click()")
    pg.wait_for_timeout(800)
    ck(pg.evaluate("LANG") == "zh", "语言切回中文")

    # 更新日志首条（两级弹窗：关于 → 更新日志，§50）——先彻底关掉 AI 设置弹窗，否则遮罩压着日志弹窗
    pg.evaluate("() => window.closeModal && closeModal()")
    pg.wait_for_timeout(500)
    clear_masks(pg)
    pg.evaluate("() => { const b=document.getElementById('signBtn'); if(b) b.click(); }")
    pg.wait_for_timeout(1400)
    pg.evaluate("() => { const b=document.getElementById('aboutLog'); if(b) b.click(); }")
    pg.wait_for_timeout(1800)
    ck(not pg.evaluate("!!document.getElementById('aiCfgMask').classList.contains('show')"),
       "AI 设置遮罩已关闭，不再遮挡日志弹窗")
    log_first = pg.evaluate("() => { const it=document.querySelector('#logMask .log-item.cur');"
                            " return it ? it.innerText.replace(/\\s+/g,' ').trim() : null; }")
    ck(log_first is not None and "V6.9.5" in log_first and "claude-haiku-5.5" in log_first,
       "更新日志首条含 V6.9.5 与新模型  实得 %r" % log_first)
    mk = pg.query_selector("#logMask .log-modal").bounding_box()
    pg.screenshot(path=str(OUT / "_v695_证据_更新日志.png"),
                  clip={"x": mk["x"], "y": mk["y"], "width": mk["width"], "height": min(430, mk["height"])})

    noise = [e for e in errs if "favicon" not in e and "ERR_FAILED" not in e
             and "Failed to load resource" not in e and "ERR_BLOCKED" not in e]
    ck(len(noise) == 0, "控制台无真实错误  实得 %s" % noise[:3])
    b.close()

print("\n失败 %d 项" % len(fails))
raise SystemExit(1 if fails else 0)
