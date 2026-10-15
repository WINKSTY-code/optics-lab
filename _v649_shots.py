# -*- coding: utf-8 -*-
"""V6.4.9 视觉取证：① 直线传播调节栏 修前/修后对照；② 物体颜色 4 组示例；③ 手机端。"""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
OLD = (BASE / "光学交互实验室_AI_v6.4.8.html").resolve().as_uri()
NEW = (BASE / "光学交互实验室_AI_v6.4.9.html").resolve().as_uri()


def prep(pg):
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


def make_pg(b, w, h):
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    return pg


with sync_playwright() as p:
    b = p.chromium.launch()

    # ① 直线传播：修前（调节栏在右侧栏）
    pg = make_pg(b, 1440, 900)
    pg.goto(OLD, wait_until="domcontentloaded"); prep(pg)
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(600)
    top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-line .stage').getBoundingClientRect().top - 8)")
    before = BASE / "_v649_修前_直线传播_1440.png"
    pg.screenshot(path=str(before), clip={"x": 0, "y": top, "width": 1440, "height": 560})
    pg.close()

    # ① 修后
    pg = make_pg(b, 1440, 900)
    pg.goto(NEW, wait_until="domcontentloaded"); prep(pg)
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(600)
    top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-line .stage').getBoundingClientRect().top - 8)")
    after = BASE / "_v649_修后_直线传播_1440.png"
    pg.screenshot(path=str(after), clip={"x": 0, "y": top, "width": 1440, "height": 560})
    pg.close()

    # ② 物体颜色 4 组示例
    combos = [("red", "green"), ("red", "white"), ("white", "green"), ("yellow", "blue")]
    tiles = []
    pg = make_pg(b, 1100, 900)
    pg.goto(NEW, wait_until="domcontentloaded"); prep(pg)
    pg.click('.tab-btn[data-tab="disperse"]'); pg.wait_for_timeout(500)
    pg.click('#disp-mode .sec[data-m="obj"]'); pg.wait_for_timeout(400)
    for i, (oc, lt) in enumerate(combos):
        pg.click('#disp-obj-color .sec[data-oc="%s"]' % oc)
        pg.click('#disp-light .sec[data-l="%s"]' % lt)
        pg.wait_for_timeout(320)
        f = BASE / ("_v649_物体颜色_%d_%s%s.png" % (i, oc, lt))
        top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-disperse .stage').getBoundingClientRect().top - 8)")
        pg.screenshot(path=str(f), clip={"x": 0, "y": top, "width": 1100, "height": 560})
        tiles.append((oc, lt, f))
    pg.close()

    # ③ 手机端
    pg = make_pg(b, 390, 900)
    pg.goto(NEW, wait_until="domcontentloaded"); prep(pg)
    pg.click('.tab-btn[data-tab="disperse"]'); pg.wait_for_timeout(500)
    pg.click('#disp-mode .sec[data-m="obj"]'); pg.wait_for_timeout(400)
    pg.click('#disp-obj-color .sec[data-oc="yellow"]')
    pg.click('#disp-light .sec[data-l="red"]'); pg.wait_for_timeout(400)
    top = pg.evaluate("() => Math.max(0, document.querySelector('#tab-disperse .stage').getBoundingClientRect().top - 8)")
    mob = BASE / "_v649_手机_物体颜色_390.png"
    pg.screenshot(path=str(mob), clip={"x": 0, "y": top, "width": 390, "height": 760})
    pg.close()
    b.close()

# 拼对照（上下）
ia, ib = Image.open(before), Image.open(after)
LAB = 34
cv = Image.new("RGB", (max(ia.width, ib.width), ia.height + ib.height + LAB * 2 + 12), "#101418")
dr = ImageDraw.Draw(cv)
dr.rectangle([0, 0, cv.width, LAB], fill="#7a2230")
dr.text((10, 9), "BEFORE  V6.4.8  — control bar sits in the right sidebar", fill="#fff")
cv.paste(ia, (0, LAB))
y = LAB + ia.height + 6
dr.rectangle([0, y, cv.width, y + LAB], fill="#1d5c37")
dr.text((10, y + 9), "AFTER  V6.4.9  — control bar moved under the canvas", fill="#fff")
cv.paste(ib, (0, y + LAB))
cmp_path = BASE / "_v649_对照_直线传播调节栏.png"
cv.save(cmp_path)

# 拼 4 例（2×2）
imgs = [Image.open(t[2]) for t in tiles]
w, h = imgs[0].size
grid = Image.new("RGB", (w * 2 + 12, h * 2 + 12), "#101418")
for i, im in enumerate(imgs):
    grid.paste(im, ((i % 2) * (w + 12), (i // 2) * (h + 12)))
dr2 = ImageDraw.Draw(grid)
zhoc = {'red': 'red object', 'green': 'green object', 'white': 'white object', 'yellow': 'yellow object'}
zhl = {'white': 'white light', 'red': 'red light', 'green': 'green light', 'blue': 'blue light'}
for i, (oc, lt, _) in enumerate(tiles):
    x = (i % 2) * (w + 12)
    y = (i // 2) * (h + 12)
    dr2.rectangle([x, y, x + w, y + 26], fill="#1b2430")
    dr2.text((x + 8, y + 7), "%s  +  %s" % (zhoc[oc], zhl[lt]), fill="#c8f04f")
grid_path = BASE / "_v649_物体颜色_四例.png"
grid.save(grid_path)

print("OK:")
for p_ in (cmp_path, grid_path, mob):
    print("  ", p_.name, Image.open(p_).size)
