# -*- coding: utf-8 -*-
"""截图：① 打开页面（应无弹窗）② 关闭时弹窗（新增效果）"""
import pathlib
from playwright.sync_api import sync_playwright

DST = pathlib.Path("光学交互实验室_AI_v6.4.18.html").resolve().as_uri()
SRC = pathlib.Path("光学交互实验室_AI_v6.4.17 (1).html").resolve().as_uri()

SEED = """
(function(){ try{
  localStorage.setItem('ai_optics_v1_cfg', JSON.stringify({provider:'zhipu',model:'GLM-5.3',apikey:'sk-testmain1234567890abcd'}));
  localStorage.setItem('ai_optics_v1_judge', JSON.stringify({provider:'zhipu',model:'GLM-5.3',apikey:'sk-judge9876543210wxyz'}));
  sessionStorage.clear();
}catch(e){} })();
"""

def clear_masks(pg):
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")

def first_run(pg):
    pg.wait_for_timeout(2500)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "演示"); pg.fill("#stuNo", "01")
        pg.click("#stuAdd"); pg.wait_for_timeout(800)
    clear_masks(pg)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=swiftshader"])

    # 旧版：打开即弹（复现原行为，作对照）
    c1 = b.new_context(viewport={"width": 1360, "height": 860})
    p1 = c1.new_page()
    p1.add_init_script(SEED)
    p1.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    p1.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    p1.goto(SRC, wait_until="domcontentloaded")
    p1.wait_for_timeout(2500)
    if p1.query_selector("#stuName") and p1.is_visible("#stuName"):
        p1.fill("#stuName", "演示"); p1.fill("#stuNo", "01")
        p1.click("#stuAdd"); p1.wait_for_timeout(900)
    # 此时（旧版）应出现本地存储弹窗
    p1.screenshot(path="_v6418_旧版_打开即弹.png")
    print("旧版截图:", p1.evaluate("!!document.querySelector('#aiCfgMask.show')"))
    c1.close()

    # 新版：打开无弹窗
    c2 = b.new_context(viewport={"width": 1360, "height": 860})
    p2 = c2.new_page()
    p2.add_init_script(SEED)
    p2.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    p2.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    p2.goto(DST, wait_until="domcontentloaded")
    first_run(p2)
    p2.screenshot(path="_v6418_新版_打开无弹窗.png")
    print("新版打开时有无弹窗:", p2.evaluate("!!document.querySelector('#aiCfgMask.show')"))

    # 新版：关闭时弹窗（浅色 + 深色）
    p2.evaluate("window.dispatchEvent(new Event('beforeunload', {cancelable:true}))")
    p2.wait_for_timeout(700)
    p2.screenshot(path="_v6418_新版_关闭时弹窗.png")
    print("新版关闭时有无弹窗:", p2.evaluate("!!document.querySelector('#aiCfgMask.show')"))
    # 切深色再拍一张
    try:
        p2.evaluate("document.documentElement.classList.add('dark')")
        p2.wait_for_timeout(400)
        p2.screenshot(path="_v6418_新版_关闭时弹窗_深色.png")
    except Exception as e:
        print("deep shot skipped:", e)

    # 手机版
    c3 = b.new_context(viewport={"width": 390, "height": 844})
    p3 = c3.new_page()
    p3.add_init_script(SEED)
    p3.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    p3.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    p3.goto(DST, wait_until="domcontentloaded")
    first_run(p3)
    p3.evaluate("window.dispatchEvent(new Event('beforeunload', {cancelable:true}))")
    p3.wait_for_timeout(700)
    p3.screenshot(path="_v6418_新版_关闭时弹窗_手机390.png")
    # 横向溢出检测
    ov = p3.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("手机390横向溢出:", ov)
    c3.close()
    b.close()
print("done")
