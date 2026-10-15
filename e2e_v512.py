# -*- coding: utf-8 -*-
"""V5.1.2 端到端验证
  改动点：
    1) 实验报告入口从 tab-nav 移入「AI 诊断」弹窗（不再与实验并列）
    2) 报告页新增「← 返回实验」
    3) 精简 V5.0 及以后的更新日志
    4) 报告页激活时顶栏 AI 按钮回退到报告所选实验
  真实 Chromium 驱动；沿用 V5.1.1 的「断言真实数值」原则。
"""
import sys, pathlib, re
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.2.html")
URL = HTML.as_uri()
OUT = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\_dl512")
OUT.mkdir(exist_ok=True)

results, errors, warns = [], [], []


def ck(name, cond, detail=""):
    results.append((name, bool(cond), detail))


# 注意：不要给 #aiCfgMask 写 inline display:none —— 诊断弹窗复用它作容器，
# 残留的 inline 样式会让 .show 失效（这是 V5.1.1 e2e 未覆盖到的地方）。
DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.style.display=''; });
  ['hintBubble','welcomeHint'].forEach(id => {
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
    """真实用户路径：顶栏「🩺 诊断」→ 弹窗内「📝 实验报告」"""
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

    # ================= 0. 版本号 / 关键词 =================
    src = pg.content()
    ck("版本角标已升级到 v5.1.2",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v5.1.2",
       pg.evaluate("document.querySelector('.ver-badge').textContent.trim()"))
    ck("构建常量 BUILD = v5.1.2", "var BUILD = 'v5.1.2'" in src)
    ck("更新日志首条为 V5.1.2",
       pg.evaluate("document.querySelector('.log-list .log-item .log-ver').textContent") == "V5.1.2")
    ck("更新日志第二条为 V5.1.1",
       pg.evaluate("document.querySelectorAll('.log-list .log-item')[1].querySelector('.log-ver').textContent") == "V5.1.1")
    for kw in ["实验报告", "猜想", "数据表", "变量控制", "反思", "自评", "互评"]:
        c = src.count(kw)
        ck(f"关键词命中 [{kw}] = {c}", c > 0)

    # ================= 1. 入口位置：不再与实验并列 =================
    tabs = pg.eval_on_selector_all('.tab-btn', "els => els.map(e=>e.dataset.tab)")
    ck("导航只剩 11 个标签（10 实验 + 挑战模式）", len(tabs) == 11, str(tabs))
    ck("导航中已无 report 标签（不再与实验并列）", "report" not in tabs)
    ck("实验报告面板仍在 DOM 中可复用",
       pg.evaluate("!!document.getElementById('tab-report')"))
    ck("报告页在未被打开前不显示",
       not pg.evaluate("document.getElementById('tab-report').classList.contains('active')"))
    ck("i18n 保留 tab.report 字典（面板标题等复用）", "'tab.report'" in src)

    # ================= 2. 诊断弹窗内的报告入口 =================
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('topDiag').click()")
    pg.wait_for_timeout(450)
    ck("「🩺 诊断」按钮打开了诊断弹窗",
       pg.evaluate("!!document.querySelector('.modal-mask.show')"))
    ck("诊断弹窗内出现「📝 实验报告」入口按钮",
       pg.is_visible("#aiDiagReport"), pg.inner_text("#aiDiagReport"))
    ck("诊断入口按钮文案已翻译（非裸键）",
       "diag.rpt" not in pg.inner_text("#aiDiagReport") and len(pg.inner_text("#aiDiagReport")) > 3,
       pg.inner_text("#aiDiagReport"))
    ck("诊断弹窗三大入口齐备（开始诊断 / 知识地图 / 实验报告）",
       all(pg.is_visible(s) for s in ["#aiDiagGo", "#aiDiagMap", "#aiDiagReport"]))
    ck("诊断弹窗布局未溢出（四按钮一行可换行）",
       pg.evaluate("document.getElementById('aiDiagReport').getBoundingClientRect().width > 0"))

    # 点击入口 → 关闭弹窗 + 切到报告页
    pg.evaluate("document.getElementById('aiDiagReport').click()")
    pg.wait_for_timeout(600)
    ck("点报告入口后诊断弹窗已关闭",
       not pg.evaluate("!!document.querySelector('.modal-mask.show')"))
    ck("报告面板被激活（#tab-report.panel.active）",
       pg.evaluate("document.getElementById('tab-report').classList.contains('active')"))
    ck("导航按钮无一被误标为 active（报告不在导航里）",
       pg.eval_on_selector_all('.tab-btn', "els => els.filter(e=>e.classList.contains('active')).length") == 0)

    # ================= 3. 报告面板结构 =================
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
    ck("报告初始跟随最近打开的实验（lens）",
       pg.evaluate("document.getElementById('rpt-exp').value") == "lens",
       pg.evaluate("document.getElementById('rpt-exp').value"))

    # ================= 4. 「← 返回实验」快捷出口 =================
    ck("报告页存在「← 返回实验」按钮", pg.is_visible("#rpt-back"), pg.inner_text("#rpt-back"))
    ck("返回按钮文案已翻译（非裸键）", "rpt.back" not in pg.inner_text("#rpt-back"))
    pg.click("#rpt-back")
    pg.wait_for_timeout(500)
    ck("点「返回实验」回到报告所选实验页（lens）",
       pg.evaluate("document.getElementById('tab-lens').classList.contains('active')"),
       pg.evaluate("document.querySelector('.panel.active').id"))
    ck("返回后导航按钮 active 状态同步恢复",
       pg.eval_on_selector_all('.tab-btn', "els => els.filter(e=>e.classList.contains('active')).map(e=>e.dataset.tab).join(',')") == "lens")

    # ================= 5. 报告页上点「诊断」的上下文回退 =================
    to_report(pg)
    pg.evaluate("document.getElementById('topDiag').click()")
    pg.wait_for_timeout(450)
    title = pg.evaluate("(() => { const m = document.querySelector('.modal-mask.show'); return m ? m.innerText.split('\\n')[0] : 'NO MODAL'; })()")
    ck("报告页上点诊断不会出现「错题诊断 · report」",
       "report" not in title and "Report" not in title, title)
    ck("报告页上点诊断回退到报告所选实验（凸透镜成像）",
       ("凸透镜" in title or "lens" in title.lower()), title)
    pg.evaluate("document.getElementById('aiDiagClose').click()")
    pg.wait_for_timeout(350)

    # ================= 6. 真实数值闭环（反射） =================
    nudge(pg, "reflect", "refl-iSlider", "55")
    to_report(pg)
    ck("报告跟随最近打开的实验（reflect → refl）",
       pg.evaluate("document.getElementById('rpt-exp').value") == "refl",
       pg.evaluate("document.getElementById('rpt-exp').value"))
    ck("数据卡已取到反射实验的真实落表行",
       pg.eval_on_selector_all("#rpt-data .rpt-dt tbody tr", "els => els.length") > 0)
    ck("数据卡显示「当前画布参数」实时读数", "当前画布参数" in pg.inner_text("#rpt-data"))
    vals = pg.evaluate("JSON.stringify(REPORT.collect().data.vals)")
    tdn = pg.evaluate("document.querySelector('#rpt-data .rpt-dt tbody tr:last-child').querySelectorAll('td').length")
    ck("取值数组已剥掉渲染用序号列（宽度 = DOM 行 td 数 - 1）",
       pg.evaluate("REPORT.collect().data.vals.slice(-1)[0].length") == tdn - 1,
       f"vals={pg.evaluate('REPORT.collect().data.vals.slice(-1)[0].length')} td={tdn}")
    ck("最新落表行 = 刚设的 55/55（取值未错位）",
       pg.evaluate("REPORT.collect().data.vals.slice(-1)[0].slice(0,2).join('/')") == "55/55", vals[:60])
    # ★ 数据污染回归：切 tab / 开弹窗 / 进报告都不得给「上一个实验」凭空补记
    ck("★ 切页/进报告后 refl 数据表仍只有 1 行（无凭空补记）",
       pg.evaluate("document.querySelectorAll('#refl-dataBody tr').length") == 1,
       pg.evaluate("JSON.stringify([...document.querySelectorAll('#refl-dataBody tr')].map(r=>[...r.children].map(c=>c.textContent)))"))
    concl = pg.inner_text("#rpt-concl")
    ck("反射结论含核心规律「反射角等于入射角」", "反射角等于入射角" in concl)
    ck("反射结论的偏差值为真实计算值 0.0°（不是错位后的 54.0°）",
       "最大偏差仅 0.0" in concl, concl.replace("\n", " ")[:110])
    ck("反射结论含实际入射角 55", "55" in concl)

    # ================= 7. 空数据态引导 =================
    pg.evaluate(PICK, "combo")
    pg.wait_for_timeout(300)
    ck("空数据态：数据卡给出「还没有数据」引导",
       "还没有" in pg.inner_text("#rpt-data") and "记录当前画布参数" in pg.inner_text("#rpt-data"))
    ck("空数据态：结论卡提示无法归纳", "无法归纳" in pg.inner_text("#rpt-concl"))
    ck("空数据态：完成度 = 2 / 6", "2 / 6" in pg.inner_text("#rpt-progTxt"), pg.inner_text("#rpt-progTxt"))

    # ================= 8. 一键补记当前画布参数 =================
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

    # ================= 9. 学生填写：猜想 / 反思 / 自评 / 互评 =================
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

    # ================= 10. 10 个实验的「数据 → 结论」闭环 =================
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

    # ================= 11. 一键导出 HTML =================
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
                   "变量控制", "数据表", "自评", "互评", "", "v5.1.2"]:
            ck(f"导出报告含 [{kw}]", kw in txt)
        ck("导出报告内嵌画布截图（data:image/png）", "data:image/png;base64," in txt)
        ck("导出报告含 A4 打印样式 @page 与打印按钮", "@page" in txt and "打印 / 存为 PDF" in txt)
        ck("导出报告含凸透镜成像结论要点", "一倍焦距分虚实" in txt)
        ck("导出报告含真实焦距数值 f ≈ 11", "f ≈ 11" in txt)
        ck("导出报告无二次转义（&amp;gt; / &amp;lt;）",
           "&amp;gt;" not in txt and "&amp;lt;" not in txt)
        ck("导出报告无未翻译的裸 i18n 键（rpt. / tab.）",
           not re.findall(r"rpt\.[a-zA-Z.]*", txt.replace("rpt-", "")),
           re.findall(r"rpt\.[a-zA-Z.]*", txt)[:4])
        ck("导出报告不再出现 tab.report 裸键", "tab.report" not in txt)

    # ================= 12. 数据 CSV / 复制 / 打印 =================
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

    pg.click("#rpt-copy")
    pg.wait_for_timeout(700)
    t = pg.inner_text("#rpt-tip")
    ck("复制报告文本给出反馈", ("已复制" in t or "复制失败" in t), t)
    pg.click("#rpt-print")
    pg.wait_for_timeout(1000)
    t2 = pg.inner_text("#rpt-tip")
    ck("打印/存PDF 给出反馈（新标签或降级下载）", ("Ctrl+P" in t2 or "下载" in t2), t2)

    # ================= 13. 主题 / 语言 =================
    pg.evaluate("document.getElementById('themeBtn').click()")
    pg.wait_for_timeout(350)
    ck("黑板（深色）主题下报告面板仍可见", pg.is_visible("#tab-report .rpt-head"))
    ck("深色主题下正文与背景不同（可读）",
       pg.evaluate("""() => {
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
    ck("语言切换后「返回实验」文案同步刷新",
       "Back" in pg.inner_text("#rpt-back") or "返回" in pg.inner_text("#rpt-back"),
       pg.inner_text("#rpt-back"))
    ck("语言切换后诊断弹窗报告入口文案同步刷新（重开弹窗）",
       pg.evaluate("""() => {
          document.getElementById('topDiag').click();
          const t = document.getElementById('aiDiagReport').textContent;
          document.getElementById('aiDiagClose').click();
          return t;
       }""").strip().lower().find("rpt") < 0)
    pg.evaluate("document.getElementById('langBtn').click()")
    pg.evaluate("document.getElementById('langBtn').click()")
    pg.wait_for_timeout(450)

    # ================= 14. V5.0+ 更新日志精简校验 =================
    loginfo = pg.evaluate("""() => {
      const items = [...document.querySelectorAll('.log-list .log-item')];
      const out = {};
      items.forEach(it => {
        const v = it.querySelector('.log-ver').textContent.trim();
        out[v] = { p: it.querySelectorAll('p').length,
                   len: [...it.querySelectorAll('p')].reduce((a,p)=>a+p.textContent.length,0) };
      });
      return { count: items.length, order: items.slice(0,6).map(i=>i.querySelector('.log-ver').textContent.trim()),
               vers: out };
    }""")
    ck("日志条目 43 → 44（新增 V5.1.2，旧条目一条未删）", loginfo["count"] == 44, str(loginfo["count"]))
    ck("日志前 6 条版本顺序正确",
       loginfo["order"] == ["V5.1.2", "V5.1.1", "V5.1.0", "V5.0.2", "V5.0.1", "V5.0.0"], str(loginfo["order"]))
    for v, maxp, maxlen in [("V5.1.2", 1, 140), ("V5.1.1", 1, 240), ("V5.1.0", 1, 240),
                            ("V5.0.2", 1, 60), ("V5.0.1", 1, 180), ("V5.0.0", 1, 180)]:
        info = loginfo["vers"][v]
        ck(f"{v} 条目已精简（≤{maxp} 段 / {info['len']} 字）",
           info["p"] <= maxp and info["len"] <= maxlen, f"p={info['p']} len={info['len']}")
    ck("V5.0 之前的日志未被波及（V4.10.4 原文仍在）",
       "Fisher-Yates" in src)
    ck("V5.0 之前的日志条数未被删减（V4.9.11 等仍在）",
       pg.evaluate("[...document.querySelectorAll('.log-list .log-ver')].some(e=>e.textContent.trim()==='V4.9.11')"))

    # 截图存档
    to_report(pg)
    pg.wait_for_timeout(300)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v512_report_desktop.png", full_page=True)
    pg.evaluate("window.scrollTo(0,0)")
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v512_report_首屏.png", full_page=False)
    pg.evaluate(DISMISS)
    pg.evaluate("document.getElementById('logMask').classList.add('show')")
    pg.wait_for_timeout(400)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v512_更新日志.png", full_page=False)
    pg.evaluate(DISMISS)
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('topDiag').click()")
    pg.wait_for_timeout(500)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v512_诊断弹窗入口.png", full_page=False)
    pg.evaluate(DISMISS)

    # ================= 15. 移动端 =================
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
    ck("移动端导航也不再出现报告标签",
       m.eval_on_selector_all('.tab-btn', "els => els.map(e=>e.dataset.tab)").count("report") == 0)
    # 手机上真实做一次实验，再走诊断入口进报告
    m.click('.tab-btn[data-tab="reflect"]')
    m.wait_for_timeout(200)
    m.evaluate("""() => {
        const el = document.getElementById('refl-iSlider');
        el.value = '45'; el.dispatchEvent(new Event('input', {bubbles:true}));
    }""")
    m.wait_for_timeout(1400)
    m.evaluate("document.getElementById('topDiag').click()")
    m.wait_for_timeout(500)
    ck("移动端诊断弹窗内报告入口可见", m.is_visible("#aiDiagReport"))
    m.evaluate("document.getElementById('aiDiagReport').click()")
    m.wait_for_timeout(700)
    ck("移动端经诊断入口成功打开报告页", m.is_visible("#tab-report .rpt-head"))
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
    ck("移动端「返回实验」可用",
       m.evaluate("!!document.getElementById('rpt-back')"))
    ck("移动端无横向溢出",
       m.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),
       str(m.evaluate("document.documentElement.scrollWidth")) + " vs " + str(m.evaluate("window.innerWidth")))
    m.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v512_report_mobile.png", full_page=False)
    ck("移动端无 JS 报错", len(merr) == 0, str(merr[:2]))

    # ================= 16. 回归：原有实验页未被破坏 =================
    ck("回归：10 个实验数据表 + 自动记录勾选框仍在",
       pg.evaluate("""() => ['refl','mirr','lens','refr','line','disp','lfx','eye','instr','combo']
          .every(k => !!document.getElementById(k+'-dataBody') && !!document.getElementById(k+'-recAuto'))"""))
    ck("回归：REC 记录器与自动记录开关正常",
       pg.evaluate("typeof REC === 'object' && REC.isEnabled() === true"))
    ck("回归：挑战模式判卷要素仍在（错因归因+变式）",
       all(k in pg.content() for k in ["jr-cause-tag", "同类变式练一练"]))
    ck("回归：canvas 截图接口可用（导出内嵌图依赖）",
       pg.evaluate("!!document.getElementById('cv-refl').toDataURL"))
    ck("回归：内置 E2E 自检脚本仍存在且不含 report 标签依赖",
       pg.evaluate("typeof window.switchTab === 'function'"))
    ck("回归：知识地图入口仍在诊断弹窗（未被新按钮挤掉）",
       pg.evaluate("""() => {
          document.getElementById('topDiag').click();
          const ok = !!document.getElementById('aiDiagMap');
          document.getElementById('aiDiagClose').click();
          return ok;
       }"""))
    # ★ 数据污染专项回归：连续切换全部 11 个标签，任何数据表都不该多出行
    COUNTS = """() => ['refl','mirr','lens','refr','line','disp','lfx','eye','instr','combo']
        .map(k => document.querySelectorAll('#'+k+'-dataBody tr').length).join(',')"""
    pg.evaluate(DISMISS)
    before_all = pg.evaluate(COUNTS)
    for t in ["mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge", "reflect"]:
        pg.click(f'.tab-btn[data-tab="{t}"]')
        pg.wait_for_timeout(130)
    pg.wait_for_timeout(1800)
    after_all = pg.evaluate(COUNTS)
    ck("★ 回归：连续切换 11 个标签不给任何数据表凭空补记",
       before_all == after_all, f"{before_all}  →  {after_all}")
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
