# -*- coding: utf-8 -*-
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
CAND = [
  ("C  实验报告 pad5x9(默认)", "",                                "实验报告", "Lab report"),
  ("C+ 实验报告 pad5x7",       "button.rpj{padding:5px 7px}",     "实验报告", "Lab report"),
  ("C++ 实验报告 pad5x6",      "button.rpj{padding:5px 6px}",     "实验报告", "Lab report"),
]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for vname, css, zh, en in CAND:
        line = f"{vname:26}"
        okall = True
        for vw in [1280, 1366, 1440, 1600, 1920]:
            ctx = b.new_context(viewport={"width":vw,"height":900}); pg = ctx.new_page()
            pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
            pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1100)
            pg.evaluate(DISMISS)
            if css: pg.add_style_tag(content=css)
            worst = 99
            for lab in [zh, en]:
                pg.evaluate("""(a) => { const [lab,keys]=a;
                    keys.forEach(k=>{const b=document.getElementById(k+'-rptBtn'); if(b) b.textContent=lab;}); }""",
                    [lab, KEYS])
                for tab,k in TABS:
                    pg.evaluate(DISMISS); pg.click(f'.tab-btn[data-tab="{tab}"]'); pg.wait_for_timeout(70)
                    d = pg.evaluate("""(k) => {
                      const box=document.getElementById(k+'-recBtn').parentNode;
                      const bs=[...box.querySelectorAll('button')];
                      const rows=new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top))).size;
                      const need=bs.reduce((a,b)=>a+b.getBoundingClientRect().width,0)+(bs.length-1)*parseFloat(getComputedStyle(box).gap||0);
                      return {rows, slack:+(box.clientWidth-need).toFixed(1)};
                    }""", k)
                    if d['rows'] > 1: okall = False
                    worst = min(worst, d['slack'])
            line += f" | {vw}:{'单行' if okall else '换行'} 余{worst:+.1f}"
            ctx.close()
        print(line + ("   ✅" if okall else "   ❌"))
    b.close()
