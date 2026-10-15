# -*- coding: utf-8 -*-
"""V5.1.0 端到端功能验证（真实 Chromium）"""
import sys, time, pathlib
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.0.html")
URL = HTML.as_uri()

errors, results, recwarn = [], [], []
def ck(name, cond, detail=""):
    results.append((name, bool(cond), detail))

DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => m.classList.remove('show'));
  ['hintBubble','welcomeHint','aiCfgMask'].forEach(id => {
    const el = document.getElementById(id); if (el) el.style.display = 'none';
  });
  document.querySelectorAll('.hint-bubble,.welcome-hint').forEach(el => el.remove());
  if (window.speechSynthesis) speechSynthesis.cancel();
}"""

def goto_tab(pg, name):
    pg.evaluate(DISMISS)
    pg.evaluate(f"switchTab('{name}')")
    pg.wait_for_timeout(150)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console.error: " + m.text) if m.type == "error" else None)
    # 关键断言：取值函数若抛错，REC 会打 [REC] 警告——测试里必须为空
    pg.on("console", lambda m: recwarn.append(m.text) if "[REC]" in m.text else None)
    # 断网确定性：拦掉外部 CDN（字体/库），避免 file:// 下 load 事件被外网拖死
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**://fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    pg.evaluate(DISMISS)
    pg.wait_for_timeout(200)

    # 0) 设备模式 & 就绪
    mode = pg.evaluate("document.documentElement.dataset.mode")
    ck("桌面端识别为 desktop（零侵入前提）", mode == "desktop", f"data-mode={mode}")
    ck("REC 记录器已就绪", pg.evaluate("typeof window.REC === 'object' && typeof REC.commit === 'function'"))
    ck("自动记录默认勾选", pg.evaluate("REC.isEnabled() === true"))

    # 1) 10 个实验的数据表都存在且已注册
    for k in ["refl","mirr","lens","refr","line","disp","lfx","eye","instr","combo"]:
        has = pg.evaluate(f"!!document.getElementById('{k}-dataBody') && !!document.getElementById('{k}-recAuto')")
        ck(f"数据表+勾选框存在 [{k}]", has)

    # 2) 停止操作 1s 自动记录 —— 逐个实验实测
    #    tab: (滑块 id, 目标值, 表体 id)
    CASES = [
        ("line",   "line-uSlider",   "40", "line-dataBody"),
        ("disperse","",              "",   "disp-dataBody"),
        ("lensfx", "lfx-fSlider",    "130","lfx-dataBody"),
        ("eye",    "eye-uSlider",    "50", "eye-dataBody"),
        ("instr",  "instr-uSlider",  "20", "instr-dataBody"),
        ("combo",  "combo-iSlider",  "60", "combo-dataBody"),
        ("reflect","refl-iSlider",   "55", "refl-dataBody"),
        ("mirror", "mirr-uSlider",   "20", "mirr-dataBody"),
        ("lens",   "lens-uSlider",   "20", "lens-dataBody"),
        ("refract","refr-iSlider",   "30", "refr-dataBody"),
    ]
    for tab, sid, val, body in CASES:
        goto_tab(pg, tab)
        before = pg.eval_on_selector_all(f"#{body} tr", "els => els.length")
        if sid:
            pg.evaluate("""([sid,val]) => {
                const el = document.getElementById(sid);
                el.value = val;
                el.dispatchEvent(new Event('input', {bubbles:true}));
            }""", [sid, val])
        else:
            # 色散：切到「色光三原色」再关掉蓝光，产生一次 change
            pg.evaluate(DISMISS)
            pg.click('#disp-mode button[data-m="rgb"]')
            pg.wait_for_timeout(100)
            pg.click('#disp-b')
        pg.wait_for_timeout(1400)                      # 停止操作 → 等 1s 落表
        after = pg.eval_on_selector_all(f"#{body} tr", "els => els.length")
        ck(f"停止操作 1s 自动记录 [{tab}]", after > before, f"{before} → {after} 行")
        # 记录首行内容
        if after:
            row = pg.eval_on_selector_all(f"#{body} tr:first-child td", "els => els.map(e=>e.textContent.trim())")
            print(f"    [{tab}] 首行: {row}")

    # 3) 去重：同值重复触发不应新增
    goto_tab(pg, "line")
    n1 = pg.eval_on_selector_all("#line-dataBody tr", "els => els.length")
    pg.evaluate("""() => {
        const el = document.getElementById('line-uSlider');
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""")
    pg.wait_for_timeout(1400)
    n2 = pg.eval_on_selector_all("#line-dataBody tr", "els => els.length")
    ck("同参数重复操作自动去重", n1 == n2, f"{n1} → {n2} 行")

    # 4) 换值 → 应新增
    pg.evaluate("""() => {
        const el = document.getElementById('line-uSlider');
        el.value = '44';
        el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    pg.wait_for_timeout(1400)
    n3 = pg.eval_on_selector_all("#line-dataBody tr", "els => els.length")
    ck("参数变化后新增一行", n3 == n2 + 1, f"{n2} → {n3} 行")

    # 5) 取消勾选 → 不再自动记录
    pg.evaluate("document.getElementById('line-recAuto').click()")
    pg.wait_for_timeout(80)
    ck("取消勾选后 REC.isEnabled()=false", pg.evaluate("REC.isEnabled() === false"))
    pg.evaluate("""() => {
        const el = document.getElementById('line-uSlider');
        el.value = '33';
        el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    pg.wait_for_timeout(1400)
    n4 = pg.eval_on_selector_all("#line-dataBody tr", "els => els.length")
    ck("取消勾选后停止自动记录", n4 == n3, f"{n3} → {n4} 行")

    # 6) 重新勾选 → 恢复
    pg.evaluate("document.getElementById('line-recAuto').click()")
    pg.evaluate("""() => {
        const el = document.getElementById('line-vSlider');
        el.value = '38';
        el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    pg.wait_for_timeout(1400)
    n5 = pg.eval_on_selector_all("#line-dataBody tr", "els => els.length")
    ck("重新勾选后恢复自动记录", n5 == n4 + 1, f"{n4} → {n5} 行")

    # 7) 画布直接鼠标拖动 → 也应记录
    goto_tab(pg, "reflect")
    nb = pg.eval_on_selector_all("#refl-dataBody tr", "els => els.length")
    box = pg.locator("#cv-refl").bounding_box()
    pg.mouse.move(box["x"] + box["width"] * 0.34, box["y"] + box["height"] * 0.30)
    pg.mouse.down()
    pg.mouse.move(box["x"] + box["width"] * 0.52, box["y"] + box["height"] * 0.36, steps=12)
    pg.mouse.up()
    pg.wait_for_timeout(1500)
    na = pg.eval_on_selector_all("#refl-dataBody tr", "els => els.length")
    ck("画布鼠标拖动后自动记录", na > nb, f"{nb} → {na} 行")

    # 8) 判卷错因归因代码已就位
    src = pg.content()
    for kw in ['"errorTypes"', '"rootCause"', '"variant"', "jr-cause-tag", "同类变式练一练"]:
        ck(f"判卷错因归因要素 [{kw}]", kw in src)

    # 8b) 取值函数无异常（REC 告警必须为空）
    ck("10 个实验的取值函数全部无异常（无 [REC] 告警）", len(recwarn) == 0,
       f"告警 {len(recwarn)} 条: {recwarn[:3]}")

    # 9) 截图存档
    goto_tab(pg, "line")
    pg.wait_for_timeout(400)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v510_line_panel.png", full_page=False)
    goto_tab(pg, "reflect")
    pg.wait_for_timeout(400)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v510_reflect_panel.png", full_page=False)

    b.close()

print("\n" + "=" * 72)
ok = sum(1 for _, c, _ in results if c)
print(f"结果：{ok}/{len(results)} 通过")
print("=" * 72)
for n, c, d in results:
    print(f"{'✅' if c else '❌'} {n}" + (f"   [{d}]" if d else ""))
if errors:
    print("\n⚠️ 页面错误：")
    for e in errors[:12]:
        print("   ", e)
else:
    print("\n无 JS 运行时错误")
print("")
print("页面 console.error:", len(errors), "条（CDN 被测试主动拦截的属于预期）")
sys.exit(0 if ok == len(results) and not recwarn else 1)
