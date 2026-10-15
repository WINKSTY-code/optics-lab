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
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width":1600,"height":1000}).new_page()
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
    pg.evaluate(DISMISS)
    cs = pg.evaluate("""() => { const c=getComputedStyle(document.getElementById('refl-recBtn'));
        return {pad:c.padding, fs:c.fontSize, gapc:getComputedStyle(document.getElementById('refl-recBtn').parentNode).gap}; }""")
    print("按钮样式:", json.dumps(cs, ensure_ascii=False))
    print(f"{'key':7}{'面板宽':>8}{'按钮合计':>10}{'间隙':>7}{'总需':>9}{'余量':>9}  行数")
    for tab,k in TABS:
        pg.evaluate(DISMISS)
        pg.click(f'.tab-btn[data-tab="{tab}"]'); pg.wait_for_timeout(250)
        d = pg.evaluate("""(k) => {
          const box = document.getElementById(k+'-recBtn').parentNode;
          const bs=[...box.querySelectorAll('button')];
          const w=bs.reduce((a,b)=>a+b.getBoundingClientRect().width,0);
          const g=(bs.length-1)*parseFloat(getComputedStyle(box).gap||0);
          const rows=new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top))).size;
          return {boxW:+box.clientWidth.toFixed(1), w:+w.toFixed(1), g:+g.toFixed(1), rows,
                  rpt:+document.getElementById(k+'-rptBtn').getBoundingClientRect().width.toFixed(1)};
        }""", k)
        tot = d['w']+d['g']; slack = d['boxW']-tot
        print(f"{k:7}{d['boxW']:>8}{d['w']:>10}{d['g']:>7}{tot:>9.1f}{slack:>9.1f}  {d['rows']}  (报告钮{d['rpt']})")
    b.close()
