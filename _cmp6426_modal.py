# -*- coding: utf-8 -*-
"""对照截图：v6.4.25 与 v6.4.26 的「判卷模型设置」弹窗（证明改动只多了一句说明，布局未动）"""
import pathlib
from playwright.sync_api import sync_playwright

SEED = r"""
try {
  localStorage.setItem('ai_optics_v1_cfg', JSON.stringify(
    {provider:'zhipu', apikey:'sk-e2e', model:'', baseUrl:'', thinkMode:true}));
  sessionStorage.setItem('ai_optics_v1_keyClearAsked', '1');
} catch(e) {}
"""


def shot(pg, url, out):
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.on("dialog", lambda d: d.dismiss())
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(1700)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.wait_for_timeout(600); pg.fill("#stuName", "E"); pg.fill("#stuNo", "E"); pg.click("#stuAdd"); pg.wait_for_timeout(700)
    pg.evaluate("() => document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.classList.remove('is-closing'); })")
    pg.click('.tab-btn[data-tab="judge"]')
    pg.wait_for_timeout(700)
    pg.evaluate("() => document.querySelectorAll('.modal-mask').forEach(m => { m.classList.remove('show'); m.classList.remove('is-closing'); })")
    pg.wait_for_selector('#judgeCfgBtn', state='visible', timeout=8000)
    pg.click('#judgeCfgBtn')
    pg.wait_for_timeout(600)
    box = pg.evaluate("""() => {
      const m = document.querySelector('#judgeCfgMask .modal');
      m.scrollTop = 0;
      const r = m.getBoundingClientRect();
      const f = m.querySelector('.fbox').getBoundingClientRect();
      return { modal: [Math.round(r.width), Math.round(r.height)],
               fbox: [Math.round(f.width), Math.round(f.height), Math.round(f.top - r.top)],
               pCount: m.querySelectorAll(':scope > p').length,
               noteWrap: [...m.querySelectorAll(':scope > p')].map(e => Math.round(e.getBoundingClientRect().height)) };
    }""")
    pg.locator('#judgeCfgMask .modal').screenshot(path=out)
    return box


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(SEED)
    pg = ctx.new_page()
    old = shot(pg, pathlib.Path("光学交互实验室_AI_v6.4.25.html").resolve().as_uri(), "_cmp6425_modal.png")
    new = shot(pg, pathlib.Path("光学交互实验室_AI_v6.4.26.html").resolve().as_uri(), "_cmp6426_modal.png")
    b.close()

print("v6.4.25:", old)
print("v6.4.26:", new)
print("弹窗宽高一致:", old["modal"] == new["modal"])
print(".fbox 相对弹窗顶边位移:", old["fbox"][2], "->", new["fbox"][2], "（差值=新增说明段高度）")
