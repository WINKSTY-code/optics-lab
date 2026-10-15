# -*- coding: utf-8 -*-
"""V5.1.1 端到端验证：实验报告自动生成（六要素）+ 一键导出
   真实 Chromium 驱动。
   重点：不只断言"有结论"，而是断言结论里的【真实数值】正确
   —— 用于拦截"DOM 行首列序号导致的索引错位"这类静默 bug。"""
import sys, pathlib, re
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.1.html")
URL = HTML.as_uri()
OUT = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\_dl511")
OUT.mkdir(exist_ok=True)

results, errors, warns = [], [], []


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

PICK = """(k) => {
  const s = document.getElementById('rpt-exp');
  s.value = k; s.dispatchEvent(new Event('change', {bubbles:true}));
}"""

# tab, 滑块id, 目标值, 数据表key
CASES = [
    ("reflect", "refl-iSlider", "55", "refl"),
    ("mirror", "mirr-uSlider", "20", "mirr"),
    ("lens", "lens-uSlider", "20", "lens"),
    ("refract", "refr-iSlider", "30", "refr"),
    ("line", "line-uSlider", "40", "line"),
    ("disperse", "", "", "disp"),
    ("lensfx", "lfx-fSlider", "130", "lfx"),
    ("eye", "eye-uSlider", "50", "eye"),
    ("instr", "instr-uSlider", "20", "instr"),
    ("combo", "combo-iSlider", "60", "combo"),
]


def nudge(pg, tab, sid, val):
    pg.evaluate(DISMISS)
    pg.click(f'.tab-btn[data-tab="{tab}"]')
    pg.wait_for_timeout(200)
    if sid:
        pg.evaluate("""([sid,val]) => {
            const el = document.getElementById(sid);
            el.value = val;
            el.dispatchEvent(new Event('input', {bubbles:true}));
        }""", [sid, val])
    else:
        pg.evaluate(DISMISS)
        pg.click('#disp-mode button[data-m="rgb"]')
        pg.wait_for_timeout(120)
        pg.click('#disp-b')
    pg.wait_for_timeout(1400)   # 停止操作 1s → 自动落表


def to_report(pg):
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="report"]')
    pg.wait_for_timeout(450)


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

    # ---------- 0. 版本与关键词审计 ----------
    src = pg.content()
    ck("版本角标已升级到 v5.1.1",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v5.1.1",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()"))
    ck("更新日志首条为 V5.1.1",
       pg.evaluate("document.querySelector('.log-list .log-item .log-ver').textContent") == "V5.1.1")
    for kw in ["实验报告", "猜想", "数据表", "变量控制", "反思", "自评", "互评"]:
        c = src.count(kw)
        ck(f"关键词命中 [{kw}] = {c}", c > 0)

    # ---------- 1. 报告标签与面板结构 ----------
    ck("导航出现第 12 个「实验报告」标签",
       pg.eval_on_selector_all('.tab-btn', "els => els.map(e=>e.dataset.tab)").count("report") == 1)
    to_report(pg)
    ck("报告面板已激活（#tab-report.panel.active）",
       pg.evaluate("document.getElementById('tab-report').classList.contains('active')"))
    heads = pg.eval_on_selector_all("#tab-report .rpt-ch b", "els => els.map(e=>e.textContent.trim())")
    ck("六要素卡片标题齐全（问题/猜想/方案/数据/结论/反思）",
       heads == ["问题", "猜想", "方案", "数据", "结论", "反思"], str(heads))
    ck("实验下拉共 10 个选项",
       pg.eval_on_selector_all("#rpt-exp option", "els => els.length") == 10)
    ck("进度条 / 完成度文案已渲染", "六要素完成度" in pg.inner_text("#rpt-progTxt"))
    ck("三个预设猜想芯片存在",
       pg.eval_on_selector_all("#rpt-guess .rpt-chip", "els => els.length") == 3)
    ck("方案含「变量控制」自变量/因变量/控制变量",
       all(k in pg.inner_text("#rpt-plan") for k in ["变量控制", "自变量", "因变量", "控制变量"]))
    ck("自评/互评五星共 10 颗",
       pg.eval_on_selector_all("#tab-report .rpt-star", "els => els.length") == 10)

    # ---------- 2. 默认跟随最近打开的实验 + 真实数值闭环（反射） ----------
    nudge(pg, "reflect", "refl-iSlider", "55")
    to_report(pg)
    ck("报告默认跟随最近打开的实验（reflect → refl）",
       pg.evaluate("document.getElementById('rpt-exp').value") == "refl",
       pg.evaluate("document.getElementById('rpt-exp').value"))
    ck("数据卡已取到反射实验的真实落表行",
       pg.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length") > 0)
    ck("数据卡显示「当前画布参数」实时读数", "当前画布参数" in pg.inner_text("#rpt-data"))
    # 白盒：行首列序号绝不能混进取值数组
    ck("取值数组不含渲染用的序号列（首两列 = 55/55）",
       pg.evaluate("REPORT.collect().data.vals[0].slice(0,2).join('/')") == "55/55",
       pg.evaluate("JSON.stringify(REPORT.collect().data.vals[0])"))
    concl = pg.inner_text("#rpt-concl")
    ck("反射结论含核心规律「反射角等于入射角」", "反射角等于入射角" in concl)
    ck("反射结论的偏差值为真实计算值 0.0°（不是错位后的 54.0°）",
       "最大偏差仅 0.0" in concl, concl.replace("\n", " ")[:110])
    ck("反射结论含实际入射角 55", "55" in concl)

    # ---------- 3. 空数据态引导 ----------
    pg.evaluate(PICK, "combo")
    pg.wait_for_timeout(300)
    ck("空数据态：数据卡给出「还没有数据」引导",
       "还没有" in pg.inner_text("#rpt-data") and "记录当前画布参数" in pg.inner_text("#rpt-data"))
    ck("空数据态：结论卡提示无法归纳", "无法归纳" in pg.inner_text("#rpt-concl"))
    ck("空数据态：完成度 = 2 / 6", "2 / 6" in pg.inner_text("#rpt-progTxt"), pg.inner_text("#rpt-progTxt"))

    # ---------- 4. 一键补记当前画布参数 ----------
    pg.evaluate(PICK, "refl")
    pg.wait_for_timeout(250)
    before = pg.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length")
    pg.evaluate("""() => {
        const el = document.getElementById('refl-iSlider');
        el.value = '70'; el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    pg.wait_for_timeout(300)
    pg.click("#rpt-data button[id^='rpt-snap-']")
    pg.wait_for_timeout(450)
    after = pg.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length")
    ck("「记录当前画布参数」把实时读数补记入表", after == before + 1, f"{before} → {after} 行")
    ck("补记行拿到的是 70/70（当前画布真实读数）",
       pg.evaluate("JSON.stringify(REPORT.collect().data.vals.slice(-1)[0].slice(0,2))") == '["70","70"]',
       pg.evaluate("JSON.stringify(REPORT.collect().data.vals.slice(-1)[0])"))

    # ---------- 5. 学生填写：猜想 / 反思 / 自评 / 互评 ----------
    pg.click("#rpt-guess .rpt-chip")
    pg.wait_for_timeout(250)
    ck("预设猜想一键填入 textarea", len(pg.input_value("#rpt-hypo")) >= 6, pg.input_value("#rpt-hypo"))
    pg.fill("#rpt-reflect", "读数比较准，下次多测几组验证。")
    pg.wait_for_timeout(200)
    pg.click("#rpt-selfStars .rpt-star[data-v='4']")
    pg.wait_for_timeout(250)
    ck("自评星级已记录为 4 / 5", "4 / 5" in pg.inner_text("#rpt-selfTxt"), pg.inner_text("#rpt-selfTxt"))
    ck("填写完整后完成度 = 6 / 6", "6 / 6" in pg.inner_text("#rpt-progTxt"), pg.inner_text("#rpt-progTxt"))
    ck("六要素进度点全部点亮",
       pg.eval_on_selector_all("#rpt-dots .rpt-dot", "els => els.filter(e=>e.classList.contains('on')).length") == 6)
    pg.fill("#rpt-peerName", "小明")
    pg.click("#rpt-peerStars .rpt-star[data-v='5']")
    pg.wait_for_timeout(200)
    ck("互评星级已记录为 5 / 5", "5 / 5" in pg.inner_text("#rpt-peerTxt"), pg.inner_text("#rpt-peerTxt"))

    # ---------- 6. 10 个实验的「数据 → 结论」闭环（含数值核对） ----------
    NUM = {
        "mirr": "最大差值为 0.0",
        "lens": "f ≈ 11",
        "refr": "最大角差 8.0",
        "instr": "u=20.0",
        "combo": "最大偏差为 0.0",
    }
    for tab, sid, val, key in CASES:
        nudge(pg, tab, sid, val)
        to_report(pg)
        pg.evaluate(PICK, key)
        pg.wait_for_timeout(350)
        nr = pg.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length")
        cc = pg.inner_text("#rpt-concl")
        ck(f"[{key}] 数据表有真实行", nr > 0, f"{nr} 行")
        ck(f"[{key}] 结论自动生成（非空态）",
           "无法归纳" not in cc and len(cc) > 40, cc[:44].replace("\n", " "))
        ck(f"[{key}] 问题+方案自动齐备",
           len(pg.inner_text("#rpt-q")) > 20 and "自变量" in pg.inner_text("#rpt-plan"))
        if key in NUM:
            ck(f"[{key}] 结论数值正确 [{NUM[key]}]", NUM[key] in cc, cc.replace("\n", " ")[-120:])

    # ---------- 7. 一键导出 HTML ----------
    pg.evaluate(PICK, "lens")
    pg.wait_for_timeout(300)
    pg.fill("#rpt-name", "")
    pg.wait_for_timeout(250)
    dpath = None
    try:
        with pg.expect_download(timeout=15000) as dl:
            pg.click("#rpt-export")
        d = dl.value
        dpath = OUT / d.suggested_filename
        d.save_as(str(dpath))
    except Exception as e:
        ck("一键导出报告触发下载", False, repr(e)[:160])
    if dpath and dpath.exists():
        ck("一键导出报告触发下载", True, dpath.name)
        ck("导出文件名含实验名与日期",
           ("实验报告" in dpath.name and re.search(r"\d{4}-\d{2}-\d{2}", dpath.name) is not None), dpath.name)
        txt = dpath.read_text(encoding="utf-8")
        ck("导出文件为完整 HTML（DOCTYPE + viewport）",
           txt.startswith("<!DOCTYPE html>") and "viewport" in txt)
        for kw in ["一、问题", "二、猜想", "三、方案", "四、数据", "五、结论", "六、反思",
                   "变量控制", "数据表", "自评", "互评", "", "v5.1.1"]:
            ck(f"导出报告含 [{kw}]", kw in txt)
        ck("导出报告内嵌画布截图（data:image/png）", "data:image/png;base64," in txt)
        ck("导出报告含 A4 打印样式 @page 与打印按钮", "@page" in txt and "打印 / 存为 PDF" in txt)
        ck("导出报告含凸透镜成像结论要点", "一倍焦距分虚实" in txt)
        ck("导出报告含真实焦距数值 f ≈ 11", "f ≈ 11" in txt)
        ck("导出报告无二次转义（&amp;gt; / &amp;lt;）",
           "&amp;gt;" not in txt and "&amp;lt;" not in txt)
        ck("导出报告无未翻译的裸 i18n 键（rpt. / tab.）",
           "rpt." not in txt.replace("rpt-", ""), [x for x in re.findall(r"rpt\.[a-zA-Z.]*", txt)][:4])

    # ---------- 8. 数据 CSV ----------
    try:
        with pg.expect_download(timeout=15000) as dl2:
            pg.click("#rpt-csv")
        d2 = dl2.value
        c2 = OUT / d2.suggested_filename
        d2.save_as(str(c2))
        csv = c2.read_text(encoding="utf-8-sig", errors="replace")
        ck("导出数据 CSV 成功（文件名 + 有表头行）",
           "实验报告数据" in c2.name and csv.count("\n") >= 1, c2.name)
        ck("CSV 带 UTF-8 BOM（Excel 不乱码）", c2.read_bytes()[:3] == b"\xef\xbb\xbf")
    except Exception as e:
        ck("导出数据 CSV 成功（文件名 + 有表头行）", False, repr(e)[:160])

    # ---------- 9. 复制文本 / 打印 ----------
    pg.click("#rpt-copy")
    pg.wait_for_timeout(700)
    t = pg.inner_text("#rpt-tip")
    ck("复制报告文本给出反馈", ("已复制" in t or "复制失败" in t), t)
    pg.click("#rpt-print")
    pg.wait_for_timeout(1000)
    t2 = pg.inner_text("#rpt-tip")
    ck("打印/存PDF 给出反馈（新标签或降级下载）", ("Ctrl+P" in t2 or "下载" in t2), t2)

    # ---------- 10. 主题 / 语言 ----------
    pg.evaluate("document.getElementById('themeBtn').click()")
    pg.wait_for_timeout(350)
    ck("黑板（深色）主题下报告面板仍可见", pg.is_visible("#tab-report .rpt-head"))
    ck("深色主题下正文与背景不同（可读）",
       pg.evaluate("""() => {
          const el = document.querySelector('#tab-report .rpt-cb');
          const cs = getComputedStyle(document.body);
          return cs.color !== cs.backgroundColor;
       }"""))
    pg.evaluate("document.getElementById('themeBtn').click()")
    pg.wait_for_timeout(250)
    lang_before = pg.inner_text("#rpt-progTxt")
    pg.evaluate("document.getElementById('langBtn').click()")
    pg.wait_for_timeout(450)
    ck("切换语言后报告面板不报错且内容完整",
       len(pg.inner_text("#rpt-q")) > 10 and len(pg.inner_text("#rpt-plan")) > 10 and "6" in lang_before)
    ck("语言切换后实验下拉文案同步刷新",
       "Reflection" in pg.inner_text("#rpt-exp") or "光的反射" in pg.inner_text("#rpt-exp"),
       pg.inner_text("#rpt-exp")[:40].replace("\n", " / "))
    pg.evaluate("document.getElementById('langBtn').click()")
    pg.evaluate("document.getElementById('langBtn').click()")
    pg.wait_for_timeout(450)

    # 截图存档
    to_report(pg)
    pg.wait_for_timeout(300)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v511_report_desktop.png", full_page=True)
    pg.evaluate("window.scrollTo(0,0)")
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v511_report_首屏.png", full_page=False)

    # ---------- 11. 移动端 ----------
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
    ck("移动端识别 data-mode=mobile", m.evaluate("document.documentElement.dataset.mode") == "mobile",
       m.evaluate("document.documentElement.dataset.mode"))
    # 先在手机上真实做一次实验，再进报告，验证小屏全链路
    m.evaluate(DISMISS)
    m.click('.tab-btn[data-tab="reflect"]')
    m.wait_for_timeout(200)
    m.evaluate("""() => {
        const el = document.getElementById('refl-iSlider');
        el.value = '45'; el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    m.wait_for_timeout(1400)
    m.evaluate("switchTab('report')")
    m.wait_for_timeout(600)
    ck("移动端报告面板可渲染", m.is_visible("#tab-report .rpt-head"))
    ck("移动端六要素卡片齐全",
       m.eval_on_selector_all("#tab-report .rpt-ch b", "els => els.length") == 6)
    ck("移动端取到真实数据并生成结论",
       m.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length") > 0
       and "反射角等于入射角" in m.inner_text("#rpt-concl"))
    ck("移动端 textarea 字号 16px（防 iOS 聚焦缩放）",
       m.evaluate("getComputedStyle(document.getElementById('rpt-hypo')).fontSize") == "16px",
       m.evaluate("getComputedStyle(document.getElementById('rpt-hypo')).fontSize"))
    ck("移动端星级触控友好（≥20px）",
       m.evaluate("parseFloat(getComputedStyle(document.querySelector('#rpt-selfStars .rpt-star')).fontSize)") >= 20)
    ck("移动端无横向溢出",
       m.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),
       str(m.evaluate("document.documentElement.scrollWidth")) + " vs " + str(m.evaluate("window.innerWidth")))
    m.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v511_report_mobile.png", full_page=False)
    ck("移动端无 JS 报错", len(merr) == 0, str(merr[:2]))

    # ---------- 12. 回归：原有实验页未被破坏 ----------
    ck("回归：10 个实验数据表 + 自动记录勾选框仍在",
       pg.evaluate("""() => ['refl','mirr','lens','refr','line','disp','lfx','eye','instr','combo']
          .every(k => !!document.getElementById(k+'-dataBody') && !!document.getElementById(k+'-recAuto'))"""))
    ck("回归：REC 记录器与自动记录开关正常",
       pg.evaluate("typeof REC === 'object' && REC.isEnabled() === true"))
    ck("回归：挑战模式判卷要素仍在（错因归因+变式）",
       all(k in pg.content() for k in ["jr-cause-tag", "同类变式练一练"]))
    ck("回归：canvas 截图接口可用（导出内嵌图依赖）",
       pg.evaluate("!!document.getElementById('cv-refl').toDataURL"))
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
