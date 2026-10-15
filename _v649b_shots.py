# -*- coding: utf-8 -*-
"""V6.4.9 修正后取证：色散面板「棱镜/三原色」布局应与 V6.4.8 完全一致，
只有「物体颜色」模式多出（本该有的）控件组。"""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
NEW = (BASE / "光学交互实验室_AI_v6.4.9.html").resolve().as_uri()


def cap(pg, mode, out):
    pg.click('#disp-mode .sec[data-m="%s"]' % mode)
    pg.wait_for_timeout(400)
    top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-disperse .stage').getBoundingClientRect().top - 8)")
    pg.screenshot(path=str(out), clip={"x": 0, "y": top, "width": 1440, "height": 640})


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto(NEW, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.fill("#stuName", "E2E"); pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd"); pg.wait_for_timeout(700)
    except Exception:
        pass
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); })""")
    pg.click('.tab-btn[data-tab="disperse"]')
    pg.wait_for_timeout(500)
    for m in ("prism", "rgb", "obj"):
        cap(pg, m, BASE / ("_v649chk_649_%s.png" % m))
    b.close()

# 拼：上排 = 棱镜色散（648 | 649），下排 = 物体颜色（648 | 649）
rows = [("prism", "三棱镜色散 —— 布局应与 V6.4.8 完全一致"),
        ("obj", "物体颜色 —— 控件组修复后正常显示")]
tiles = {}
for m, _ in rows:
    tiles[m] = (Image.open(BASE / ("_v649chk_648_%s.png" % m)),
                Image.open(BASE / ("_v649chk_649_%s.png" % m)))
w, h = tiles["prism"][0].size
LAB, GAP = 30, 10
cv = Image.new("RGB", (w * 2 + GAP, (h + LAB) * 2 + GAP * 3), "#0f1319")
dr = ImageDraw.Draw(cv)
zh = {"648": "V6.4.8 (before)", "649": "V6.4.9 (after fix)"}
y = GAP
for m, title in rows:
    dr.rectangle([0, y, cv.width, y + LAB], fill="#1b2430")
    dr.text((10, y + 9), "%s   ——   left: V6.4.8   |   right: V6.4.9" % title, fill="#c8f04f")
    y += LAB
    a, bimg = tiles[m]
    # 左：若该模式在 648 下无内容也照常贴（保留真实对照）
    cv.paste(a, (0, y))
    cv.paste(bimg, (w + GAP, y))
    y += h + GAP
out = BASE / "_v649_色散对照_修前vs修正后.png"
cv.save(out)
print("OK:", out.name, cv.size)
