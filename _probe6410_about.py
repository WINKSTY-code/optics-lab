# -*- coding: utf-8 -*-
import pathlib, json
from playwright.sync_api import sync_playwright
BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.10.html").resolve().as_uri()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":1440,"height":900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(2000)
    # 首启弹窗先走真实流程（不要先清遮罩，否则按钮不可见）
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName","E2E"); pg.fill("#stuNo","E2E"); pg.click("#stuAdd"); pg.wait_for_timeout(800)
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.classList.remove('is-closing');}); }""")
    pg.click("#signBtn"); pg.wait_for_timeout(900)
    print(json.dumps(pg.evaluate("""() => {
      const modal = document.querySelector('#aboutMask .modal');
      return [...modal.children].map(e => {
        const cs = getComputedStyle(e), r = e.getBoundingClientRect();
        return {tag:e.TagName||e.tagName, id:e.id, cls:e.className, attrs:[...e.attributes].map(a=>a.name),
                txt:(e.textContent||'').trim().slice(0,30),
                font:cs.fontSize, color:cs.color, weight:cs.fontWeight,
                w:Math.round(r.width), h:Math.round(r.height)};
      });
    }"""), ensure_ascii=False, indent=1))
    b.close()
