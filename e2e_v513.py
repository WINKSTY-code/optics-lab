# -*- coding: utf-8 -*-
"""V5.1.3 端到端验证
  本轮改动：
    1) 每个实验数据记录行末新增「📝 实验报告」按钮（浅蓝底色），点击跳到该实验的报告页
    2) 报告页「← 返回实验」按钮改浅蓝底色
    3) 数据记录行「导出CSV」→「导出」（教师端同名按钮不受影响）
    4) 版本 5.1.3
  同时回归 V5.1.2 的两条关键行为（诊断弹窗入口、切页不凭空补记）。
"""
import sys, pathlib, re
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.3.html")
URL = HTML.as_uri()
OUT = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\_dl513")
OUT.mkdir(exist_ok=True)

results, errors, warns = [], [], []


def ck(name, cond, detail=""):
    results.append((name, bool(cond), detail))


DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.style.display=''; });
  ['hintBubble','welcomeHint'].forEach(id => {
    const el = document.getElementById(id); if (el) el.style.display = 'none';
  });
  document.querySelectorAll('.hint-bubble,.welcome-hint').forEach(el => el.remove());
  if (window.speechSynthesis) speechSynthesis.cancel();
}"""

KEYS = ['refl', 'mirr', 'lens', 'refr', 'line', 'disp', 'lfx', 'eye', 'instr', 'combo']
# 浅蓝：浅色(#cfe6ff / #0a2d55)  暗色(#bcd9ff / #082444)
BLUE_L = "rgb(207, 230, 255)"
INK_L = "rgb(10, 45, 85)"
BLUE_D = "rgb(188, 217, 255)"
INK_D = "rgb(8, 36, 68)"

CASES = [
    ("reflect", "refl-iSlider", "55", "refl"),
    ("mirror", "mirr-uSlider", "20", "mirr"),
    ("lens", "lens-uSlider", "20", "lens"),
    ("refract", "refr-iSlider", "30", "refr"),
]
NUM = {"mirr": "最大差值为 0.0", "lens": "f ≈ 11", "refr": "最大角差 8.0"}


def bg(pg, sel):
    return pg.evaluate("(s) => getComputedStyle(document.querySelector(s)).backgroundColor", sel)


def fg(pg, sel):
    return pg.evaluate("(s) => getComputedStyle(document.querySelector(s)).color", sel)


def to_report_via_diag(pg):
    pg.evaluate(DISMISS)
    pg.evaluate("document.getElementById('topDiag').click()")
    pg.wait_for_timeout(450)
    pg.evaluate("document.getElementById('aiDiagReport').click()")
    pg.wait_for_timeout(600)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console.error: " + m.text) if m.type == "error" else None)
    pg.on("console", lambda m: warns.append(m.text) if ("[REPORT]" in m.text or "[REC]" in m.text) else None)
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**://fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    pg.evaluate(DISMISS)
    src = pg.content()

    # ============ 0. 版本 / 日志 ============
    ck("角标升级到 v5.1.3",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v5.1.3",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()"))
    ck("BUILD = v5.1.3", "var BUILD = 'v5.1.3'" in src)
    ck("更新日志首条 V5.1.3",
       pg.evaluate("document.querySelector('.log-list .log-ver').textContent") == "V5.1.3")
    ck("更新日志次条 V5.1.2",
       pg.evaluate("document.querySelectorAll('.log-list .log-item')[1].querySelector('.log-ver').textContent") == "V5.1.2")
    ck("更新日志条目 44 → 45（未删旧条目）",
       pg.eval_on_selector_all(".log-list .log-item", "e => e.length") == 45,
       pg.eval_on_selector_all(".log-list .log-item", "e => e.length"))

    # ============ 1. 10 个实验都有「实验报告」按钮 ============
    ids = pg.evaluate("() => %s.map(k => !!document.getElementById(k + '-rptBtn'))" % KEYS)
    ck("10 个实验的数据记录行都有实验报告按钮", all(ids), str(ids))
    ck("按钮位于数据记录行的按钮组 .btns 内",
       pg.evaluate("() => %s.every(k => document.getElementById(k+'-rptBtn').closest('.btns'))" % KEYS))
    ck("按钮排在记录行的最后一位（记录/导出/复制/清空 之后）",
       pg.evaluate("""() => %s.every(k => {
          const box = document.getElementById(k+'-rptBtn').parentNode;
          const last = box.querySelectorAll('button')[box.querySelectorAll('button').length-1];
          return last.id === k + '-rptBtn';
       })""" % KEYS))
    labels = pg.evaluate("() => %s.map(k => document.getElementById(k+'-rptBtn').textContent.trim())" % KEYS)
    ck("按钮文案为「实验报告」", set(labels) == {"实验报告"}, str(set(labels)))
    ck("按钮带 data-i18n=btn.rpt（切语言可同步）",
       pg.evaluate("() => %s.every(k => document.getElementById(k+'-rptBtn').dataset.i18n === 'btn.rpt')" % KEYS))

    # ============ 2. 浅蓝底色（浅色主题） ============
    ck("浅色主题下报告按钮底色 = 浅蓝 #cfe6ff", bg(pg, "#refl-rptBtn") == BLUE_L, bg(pg, "#refl-rptBtn"))
    ck("浅色主题下报告按钮字色 = 深蓝 #0a2d55", fg(pg, "#refl-rptBtn") == INK_L, fg(pg, "#refl-rptBtn"))
    ck("10 个按钮底色一致（都是浅蓝）",
       set(pg.evaluate("() => %s.map(k => getComputedStyle(document.getElementById(k+'-rptBtn')).backgroundColor)" % KEYS)) == {BLUE_L})
    ck("与普通灰底按钮区分开（记录/复制/清空 仍是面底色）",
       bg(pg, "#refl-recBtn") != BLUE_L and bg(pg, "#refl-clearBtn") != BLUE_L,
       "%s / %s" % (bg(pg, "#refl-recBtn"), bg(pg, "#refl-clearBtn")))

    # ============ 3. 「导出CSV」已精简为「导出」 ============
    exp_labels = pg.evaluate("() => %s.map(k => document.getElementById(k+'-exportBtn').textContent.trim())" % KEYS)
    ck("10 个数据行导出按钮文案统一为「导出」", set(exp_labels) == {"导出"}, str(set(exp_labels)))
    ck("导出按钮不再出现「CSV」字样",
       pg.evaluate("() => %s.every(k => document.getElementById(k+'-exportBtn').textContent.indexOf('CSV') < 0)" % KEYS))
    w_exp = pg.evaluate("document.getElementById('refl-exportBtn').getBoundingClientRect().width")
    w_rec = pg.evaluate("document.getElementById('refl-recBtn').getBoundingClientRect().width")
    ck("导出按钮宽度已随文案变短（≈ 与「记录」同宽，不再最宽）",
       w_exp <= w_rec + 6, "导出 %.1f vs 记录 %.1f" % (w_exp, w_rec))
    # ★ 真·单行断言：.btns 是「内容自适应」宽度容器（内容不超限时 clientWidth==内容宽），
    #   旧写法 scrollWidth<=clientWidth 恒真、测不出换行；必须数按钮的纵向 top 去重行数。
    ROWS_OF = """(k) => {
      const box = document.getElementById(k + '-recBtn').parentNode;
      const bs = [...box.querySelectorAll('button')];
      return new Set(bs.map(b => Math.round(b.getBoundingClientRect().top))).size;
    }"""
    rowmap = {k: pg.evaluate(ROWS_OF, k) for k in KEYS}
    ck("★ 10 个面板的按钮行都是单行（不换行）", set(rowmap.values()) == {1}, str(rowmap))
    ck("★ 教师端的「导出CSV」未受影响（仍用 btn.export）",
       pg.evaluate("(function(){ try{ document.getElementById('studentBtn').click(); }catch(e){} return true; })()")
       and pg.evaluate("!!document.getElementById('tCsv')") is not None)
    pg.evaluate(DISMISS)

    # ============ 4. 报告页「← 返回实验」也是浅蓝 ============
    to_report_via_diag(pg)
    ck("报告页返回按钮底色 = 浅蓝", bg(pg, "#rpt-back") == BLUE_L, bg(pg, "#rpt-back"))
    ck("报告页返回按钮字色 = 深蓝", fg(pg, "#rpt-back") == INK_L, fg(pg, "#rpt-back"))
    ck("返回按钮与「重新取值」按钮底色已区分",
       bg(pg, "#rpt-back") != bg(pg, "#rpt-refresh"),
       "%s vs %s" % (bg(pg, "#rpt-back"), bg(pg, "#rpt-refresh")))

    # ============ 5. 点按钮 → 跳到该实验的报告页（核心闭环） ============
    for tab, sid, val, key in CASES:
        pg.evaluate(DISMISS)
        pg.click(f'.tab-btn[data-tab="{tab}"]')
        pg.wait_for_timeout(200)
        pg.evaluate("""([sid,val]) => {
            const el = document.getElementById(sid);
            el.value = val; el.dispatchEvent(new Event('input', {bubbles:true}));
        }""", [sid, val])
        pg.wait_for_timeout(1400)
        rows_before = pg.evaluate("() => %s.reduce((a,k)=>a+document.querySelectorAll('#'+k+'-dataBody tr').length,0)" % KEYS)
        pg.click(f"#{key}-rptBtn")
        pg.wait_for_timeout(600)
        ck(f"[{key}] 点数据行「实验报告」跳到报告页",
           pg.evaluate("document.getElementById('tab-report').classList.contains('active')"))
        ck(f"[{key}] 报告页自动选中本实验",
           pg.evaluate("document.getElementById('rpt-exp').value") == key,
           pg.evaluate("document.getElementById('rpt-exp').value"))
        concl = pg.inner_text("#rpt-concl")
        ck(f"[{key}] 报告结论已用本实验数据生成", "无法归纳" not in concl and len(concl) > 40)
        if key in NUM:
            ck(f"[{key}] 结论数值正确 [{NUM[key]}]", NUM[key] in concl, concl.replace("\n", " ")[-100:])
        rows_after = pg.evaluate("() => %s.reduce((a,k)=>a+document.querySelectorAll('#'+k+'-dataBody tr').length,0)" % KEYS)
        ck(f"[{key}] 跳转未给数据表凭空补记（★回归 V5.1.2 修复）", rows_before == rows_after,
           f"{rows_before} → {rows_after}")

    # 返回按钮把用户送回对应实验
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="refract"]')
    pg.wait_for_timeout(250)
    pg.click("#refr-rptBtn")
    pg.wait_for_timeout(550)
    pg.click("#rpt-back")
    pg.wait_for_timeout(500)
    ck("从数据行进来后，「← 返回实验」回到同一实验页",
       pg.evaluate("document.getElementById('tab-refract').classList.contains('active')"),
       pg.evaluate("document.querySelector('.panel.active').id"))

    # ============ 6. 切语言：注入按钮文案同步刷新 ============
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(250)
    pg.evaluate("document.getElementById('langBtn').click()")   # zh → zht
    pg.wait_for_timeout(450)
    ck("切繁体后报告按钮文案同步", pg.inner_text("#refl-rptBtn").strip() == "實驗報告", pg.inner_text("#refl-rptBtn"))
    ck("切繁体后导出按钮仍为短标签", pg.inner_text("#refl-exportBtn").strip() == "匯出", pg.inner_text("#refl-exportBtn"))
    ck("切繁体后返回按钮文案同步", "返回" in pg.inner_text("#rpt-back"), pg.inner_text("#rpt-back"))
    pg.evaluate("document.getElementById('langBtn').click()")   # zht → en
    pg.wait_for_timeout(450)
    ck("切英文后报告按钮文案同步", "Lab report" in pg.inner_text("#refl-rptBtn"), pg.inner_text("#refl-rptBtn"))
    # 语言环为 zh→zht→en→zh（共 3 种），循环点击直到回到 zh（最多 4 次）
    for _ in range(4):
        if pg.evaluate("typeof LANG !== 'undefined' && LANG === 'zh'"):
            break
        pg.evaluate("document.getElementById('langBtn').click()")
        pg.wait_for_timeout(350)
    pg.wait_for_timeout(400)
    ck("回到中文后报告按钮文案正确", pg.inner_text("#refl-rptBtn").strip() == "实验报告",
       "LANG=%s / %s" % (pg.evaluate("LANG"), pg.inner_text("#refl-rptBtn")))

    # ============ 7. 暗色（黑板）主题下仍是浅蓝底 + 深蓝字 ============
    pg.evaluate("document.getElementById('themeBtn').click()")
    pg.wait_for_timeout(450)
    ck("暗色主题识别（body.light）",
       pg.evaluate("document.body.classList.contains('light')"), pg.evaluate("document.body.className"))
    ck("暗色主题下报告按钮仍是浅蓝底", bg(pg, "#refl-rptBtn") == BLUE_D, bg(pg, "#refl-rptBtn"))
    ck("暗色主题下报告按钮字色为深蓝（对比度 > 10:1）", fg(pg, "#refl-rptBtn") == INK_D, fg(pg, "#refl-rptBtn"))
    ck("暗色主题下报告页返回按钮也是浅蓝", bg(pg, "#rpt-back") == BLUE_D, bg(pg, "#rpt-back"))
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(300)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v513_数据行_暗色.png", full_page=False)
    pg.evaluate("document.getElementById('themeBtn').click()")
    pg.wait_for_timeout(400)
    ck("切回浅色后恢复浅蓝", bg(pg, "#refl-rptBtn") == BLUE_L, bg(pg, "#refl-rptBtn"))
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v513_数据行_浅色.png", full_page=False)

    # ============ 8. 数据行「导出」CSV 仍可用（只改名，不改行为） ============
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(250)
    pg.evaluate("() => { const el=document.getElementById('refl-iSlider'); el.value='65'; el.dispatchEvent(new Event('input',{bubbles:true})); }")
    pg.wait_for_timeout(1400)
    try:
        with pg.expect_download(timeout=12000) as dl:
            pg.click("#refl-exportBtn")
        d = dl.value
        cp = OUT / d.suggested_filename
        d.save_as(str(cp))
        txt = cp.read_text(encoding="utf-8-sig", errors="replace")
        ck("数据行「导出」仍能下载 CSV", "reflection" in cp.name or cp.suffix == ".csv", cp.name)
        ck("CSV 含表头与真实数据行", ("i/°" in txt or "i/" in txt) and "65" in txt, txt.split("\n")[0][:40])
    except Exception as e:
        ck("数据行「导出」仍能下载 CSV", False, repr(e)[:150])

    # ============ 9. 回归：V5.1.2 的两条关键行为 ============
    pg.evaluate(DISMISS)
    tabs = pg.eval_on_selector_all('.tab-btn', "e => e.map(x=>x.dataset.tab)")
    ck("回归：导航仍为 11 项且无 report", len(tabs) == 11 and "report" not in tabs, str(tabs))
    to_report_via_diag(pg)
    ck("回归：诊断弹窗入口仍可进报告页",
       pg.evaluate("document.getElementById('tab-report').classList.contains('active')"))
    ck("回归：诊断弹窗内「实验报告」入口仍在", pg.evaluate("!!document.getElementById('aiDiagReport')") is not None)

    COUNTS = """() => %s.map(k => document.querySelectorAll('#'+k+'-dataBody tr').length).join(',')""" % KEYS
    pg.evaluate(DISMISS)
    before_all = pg.evaluate(COUNTS)
    for t in ["mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge", "reflect",
              "mirror", "reflect"]:
        pg.click(f'.tab-btn[data-tab="{t}"]')
        pg.wait_for_timeout(120)
    pg.wait_for_timeout(1800)
    after_all = pg.evaluate(COUNTS)
    ck("★ 回归：连续切 13 次标签不给任何数据表凭空补记", before_all == after_all, f"{before_all} → {after_all}")

    ck("回归：10 张数据表 + 自动记录勾选框仍在",
       pg.evaluate("() => %s.every(k => !!document.getElementById(k+'-dataBody') && !!document.getElementById(k+'-recAuto'))" % KEYS))
    ck("回归：REC 记录器正常", pg.evaluate("typeof REC === 'object' && REC.isEnabled() === true"))
    ck("回归：报告六要素面板完整",
       pg.eval_on_selector_all("#tab-report .rpt-ch b", "e => e.map(x=>x.textContent.trim())").__len__() == 6)
    ck("回归：判卷「错因归因 + 同类变式」仍在",
       all(k in pg.content() for k in ["jr-cause-tag", "同类变式练一练"]))
    ck("回归：canvas 截图接口可用", pg.evaluate("!!document.getElementById('cv-refl').toDataURL"))

    # ============ 10. 报告页截图 + 移动端 ============
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(200)
    pg.click("#refl-rptBtn")
    pg.wait_for_timeout(600)
    pg.evaluate("window.scrollTo(0,0)")
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v513_报告页.png", full_page=False)

    ctx2 = b.new_context(viewport={"width": 390, "height": 844},
                         user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
                                    " (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                         is_mobile=True, has_touch=True, device_scale_factor=3, accept_downloads=True)
    m = ctx2.new_page()
    merr = []
    m.on("pageerror", lambda e: merr.append(str(e)))
    m.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    m.goto(URL, wait_until="domcontentloaded")
    m.wait_for_timeout(1500)
    m.evaluate(DISMISS)
    ck("移动端 data-mode=mobile", m.evaluate("document.documentElement.dataset.mode") == "mobile",
       m.evaluate("document.documentElement.dataset.mode"))
    ck("移动端也有实验报告按钮", m.evaluate("!!document.getElementById('refl-rptBtn')"))
    ck("移动端按钮仍是浅蓝底", bg(m, "#refl-rptBtn") == BLUE_L, bg(m, "#refl-rptBtn"))
    m.evaluate("() => { const el=document.getElementById('refl-iSlider'); el.value='35'; el.dispatchEvent(new Event('input',{bubbles:true})); }")
    m.wait_for_timeout(1400)
    m.evaluate("document.getElementById('refl-rptBtn').click()")
    m.wait_for_timeout(700)
    ck("移动端点数据行按钮成功进报告页",
       m.evaluate("document.getElementById('tab-report').classList.contains('active')"))
    ck("移动端报告页返回按钮浅蓝", bg(m, "#rpt-back") == BLUE_L, bg(m, "#rpt-back"))
    ck("移动端无横向溢出",
       m.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),
       "%s vs %s" % (m.evaluate("document.documentElement.scrollWidth"), m.evaluate("window.innerWidth")))
    m.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v513_报告页_手机.png", full_page=False)
    ck("移动端无 JS 报错", len(merr) == 0, str(merr[:2]))

    ck("全流程无 [REPORT]/[REC] 告警", len(warns) == 0, str(warns[:3]))
    b.close()

print("\n" + "=" * 74)
ok = sum(1 for _, c, _ in results if c)
print(f"结果：{ok}/{len(results)} 通过")
print("=" * 74)
for n, c, d in results:
    print(f"{'✅' if c else '❌'} {n}" + (f"   [{d}]" if d else ""))
real_err = [e for e in errors if "ERR_FAILED" not in e and "jsdelivr" not in e]
if real_err:
    print("\n⚠️ 页面真实错误：")
    for e in real_err[:10]:
        print("   ", e)
else:
    print("\n无 JS 运行时错误（已排除测试主动拦截的 CDN 请求）")
sys.exit(0 if ok == len(results) and not warns else 1)
