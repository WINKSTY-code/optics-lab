# -*- coding: utf-8 -*-
import pathlib, json
from playwright.sync_api import sync_playwright
HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.3.html")
DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.style.display=''; });
  ['hintBubble','welcomeHint'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display='none'; });
}"""
KEYS = ['refl','mirr','lens','refr','line','disp','lfx','eye','instr','combo']
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width":1600,"height":1000}).new_page()
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
    pg.evaluate(DISMISS)
    d = pg.evaluate("""(KEYS) => {
      const cs = getComputedStyle(document.getElementById('refl-recBtn'));
      const out = {btnStyle:{pad:cs.padding, fs:cs.fontSize, br:cs.borderRadius, bs:cs.borderWidth, ff:cs.fontFamily},
                   panels:[]};
      KEYS.forEach(k=>{
        const el = document.getElementById(k+'-dataBody');
        if(!el) return;
        const box = document.getElementById(k+'-recBtn').parentNode;
        out.panels.push({key:k, boxW:+box.clientWidth.toFixed(1),
          need:+([...box.querySelectorAll('button')].reduce((a,b)=>a+b.getBoundingClientRect().width,0)).toFixed(1),
          gaps: (box.querySelectorAll('button').length-1)*parseFloat(getComputedStyle(box).gap||0),
          rows: new Set([...box.querySelectorAll('button')].map(b=>Math.round(b.getBoundingClientRect().top))).size});
      });
      return out;
    }""", KEYS)
    print(json.dumps(d, ensure_ascii=False, indent=1))
    b.close()
