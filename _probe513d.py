# -*- coding: utf-8 -*-
"""变体探针：不落盘，运行时注入候选样式/文案，实测每个面板按钮行是否一行放下。"""
import pathlib, json
from playwright.sync_api import sync_playwright
HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.3.html")
DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.style.display=''; });
  ['hintBubble','welcomeHint'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display='none'; });
}"""
TABS = [('reflect','refl'),('mirror','mirr'),('lens','lens'),('refract','refr'),('line','line'),
        ('disperse','disp'),('lensfx','lfx'),('eye','eye'),('instr','instr'),('combo','combo')]
KEYS = [k for _,k in TABS]
VARIANTS = [
    ("A 📝实验报告 pad5x6",  "button.rpj{padding:5px 6px}",            "📝 实验报告"),
    ("B 📝实验报告 gap4",     ".data-head .btns{gap:4px}",              "📝 实验报告"),
    ("C 实验报告(无emoji)",   "",                                        "实验报告"),
    ("D 📝报告",             "",                                        "📝 报告"),
    ("E 报告(无emoji)",      "",                                        "报告"),
    ("F 📝实验报告 pad4+g5", "button.rpj{padding:5px 4px}.data-head .btns{gap:5px}", "📝 实验报告"),
]
EN = {"A 📝实验报告 pad5x6":"📝 Lab report","B 📝实验报告 gap4":"📝 Lab report",
      "C 实验报告(无emoji)":"Lab report","D 📝报告":"📝 Report","E 报告(无emoji)":"Report",
      "F 📝实验报告 pad4+g5":"📝 Lab report"}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for vname, css, zh in VARIANTS:
        ctx = b.new_context(viewport={"width":1600,"height":1000})
        pg = ctx.new_page()
        pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1200)
        pg.evaluate(DISMISS)
        if css:
            pg.add_style_tag(content=css)
        pg.evaluate("(zh) => { window.__vzh = zh; }", zh)
        worst = []
        for lang, lab in [("zh", zh), ("zht", zh), ("en", EN[vname])]:
            pg.evaluate("""(lab) => {
                __setRptLabel = lab;
                %s.forEach(k => { const b=document.getElementById(k+'-rptBtn'); if(b) b.textContent=lab; });
            }""" % json.dumps(KEYS), lab)
            for tab,k in TABS:
                pg.evaluate(DISMISS)
                pg.click(f'.tab-btn[data-tab="{tab}"]'); pg.wait_for_timeout(90)
                d = pg.evaluate("""(k) => {
                  const box=document.getElementById(k+'-recBtn').parentNode;
                  const bs=[...box.querySelectorAll('button')];
                  const rows=new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top))).size;
                  const need=bs.reduce((a,b)=>a+b.getBoundingClientRect().width,0)+(bs.length-1)*parseFloat(getComputedStyle(box).gap||0);
                  return {rows, boxW:+box.clientWidth.toFixed(1), need:+need.toFixed(1)};
                }""", k)
                worst.append((lang, k, d['rows'], d['boxW']-d['need']))
        maxrows = max(x[2] for x in worst)
        worstslack = min(x[3] for x in worst)
        bad = [f"{l}/{x[1]}" for l,x in zip([w[0] for w in worst], worst) if False]
        fail = sorted({f"{x[0]}/{x[1]}({x[2]}行,{x[3]:+.1f})" for x in worst if x[2] > 1})
        print(f"{vname:24} 最大行数={maxrows}  最小余量={worstslack:+6.1f}  " + ("✅ 全部单行" if maxrows==1 else "❌ " + " ".join(fail[:6])))
        ctx.close()
    b.close()
