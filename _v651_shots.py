# -*- coding: utf-8 -*-
"""补充截图：让新增的模型名在控件里可见（原生 select 在无头下无法展开，故直接选中新值）"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.5.1.html").resolve().as_uri()

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--allow-file-access-from-files"])
    pg = br.new_page(viewport={"width": 1220, "height": 880})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2000)
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        try:
            pg.wait_for_timeout(600)
            pg.fill("#stuName", "E2E"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd", timeout=4000)
            pg.wait_for_timeout(700)
        except Exception as e:
            print("  (首启学生窗未走通，直接清遮罩继续：%s)" % str(e).split("\n")[0][:80])
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")
    pg.click("#setBtn"); pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(500)

    # openai → gpt-6-luna
    pg.select_option("#aiProvider", "openai"); pg.wait_for_timeout(300)
    pg.select_option("#aiModel", "gpt-6-luna"); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('.modal').scrollTo && 0")
    pg.screenshot(path=str(BASE / "_v651_证据_openai_gpt-6-luna.png"), clip={"x": 340, "y": 90, "width": 400, "height": 480})

    # anthropic → claude-opus-5.5
    pg.select_option("#aiProvider", "anthropic"); pg.wait_for_timeout(300)
    pg.select_option("#aiModel", "claude-opus-5.5"); pg.wait_for_timeout(200)
    pg.screenshot(path=str(BASE / "_v651_证据_anthropic_opus-5.5.png"), clip={"x": 340, "y": 90, "width": 400, "height": 480})

    # 更新日志
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")
    pg.click("#signBtn"); pg.wait_for_timeout(1400)
    pg.click("#aboutLog"); pg.wait_for_timeout(1600)
    pg.screenshot(path=str(BASE / "_v651_证据_更新日志.png"), clip={"x": 200, "y": 40, "width": 840, "height": 560})
    print("shots done")
    br.close()
