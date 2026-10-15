# -*- coding: utf-8 -*-
import pathlib, json
from playwright.sync_api import sync_playwright
HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.3.html")
DISMISS = """() => { try{localStorage.setItem('ai_optics_v1_hint_shown','1');}catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.style.display='';});
  ['hintBubble','welcomeHint'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='none';}); }"""
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width":1600,"height":1000}).new_page()
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1300)
    pg.evaluate(DISMISS)
    def show(tag):
        d = pg.evaluate("""() => {
          const box=document.getElementById('refl-recBtn').parentNode;
          const g=(n)=>+document.querySelector(n).getBoundingClientRect().width.toFixed(2);
          const cs=getComputedStyle(document.getElementById('refl-rptBtn'));
          return {boxW:box.clientWidth, scrollW:box.scrollWidth, gap:getComputedStyle(box).gap,
                  rec:g('#refl-recBtn'), exp:g('#refl-exportBtn'), rpt:g('#refl-rptBtn'),
                  rptTxt:document.getElementById('refl-rptBtn').textContent,
                  pad:cs.padding, fs:cs.fontSize, minW:cs.minWidth, flex:cs.flex, w:cs.width,
                  btnsMargin:getComputedStyle(document.getElementById('refl-rptBtn')).margin};
        }""")
        print(tag, json.dumps(d, ensure_ascii=False))
    show("初始(📝 实验报告):")
    pg.evaluate("() => { document.getElementById('refl-rptBtn').textContent='实验报告'; }")
    pg.wait_for_timeout(200); show("改无emoji  :")
    pg.evaluate("""() => { const s=document.createElement('style');
        s.textContent='button.rpj{padding:5px 7px}'; document.head.appendChild(s); }""")
    pg.wait_for_timeout(200); show("再 pad5x7 :")
    pg.evaluate("() => { document.getElementById('refl-rptBtn').textContent='报告'; }")
    pg.wait_for_timeout(200); show("改'报告'   :")
    b.close()
