# -*- coding: utf-8 -*-
import pathlib
from playwright.sync_api import sync_playwright
HTML = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v5.1.3.html")
DISMISS = """() => {
  try { localStorage.setItem('ai_optics_v1_hint_shown','1'); } catch(e){}
  document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.style.display=''; });
  ['hintBubble','welcomeHint'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display='none'; });
  if (window.speechSynthesis) speechSynthesis.cancel();
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width":1600,"height":1000})
    pg = ctx.new_page()
    pg.route("**://cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(HTML.as_uri(), wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
    pg.evaluate(DISMISS)
    info = pg.evaluate("""() => {
      const box = document.getElementById('refl-recBtn').parentNode;
      const cs = getComputedStyle(box);
      const btns = [...box.querySelectorAll('button')].map(b => {
        const r = b.getBoundingClientRect();
        return {id:b.id, txt:b.textContent.trim(), w:+r.width.toFixed(1), h:+r.height.toFixed(1), top:+r.top.toFixed(1)};
      });
      const rows = new Set(btns.map(x=>x.top));
      return {cls: box.className, parentChain: (()=>{let p=box,out=[];for(let i=0;i<4&&p;i++){out.push(p.tagName+'.'+p.className+':'+p.clientWidth);p=p.parentNode;}return out;})(),
              boxW:+box.clientWidth.toFixed(1), boxH:+box.clientHeight.toFixed(1), scrollW:+box.scrollWidth.toFixed(1),
              display:cs.display, flexWrap:cs.flexWrap, gap:cs.gap, padding:cs.padding, btns, rowCount:rows.size};
    }""")
    import json; print(json.dumps(info, ensure_ascii=False, indent=1))
    # 也打印记录行上方那一排(可能含 自动记录 勾选)
    pg.screenshot(path=r"C:\Users\Administrator\Desktop\AI光学参赛\_v513_probe_数据行.png")
    b.close()
