# -*- coding: utf-8 -*-
"""V6.4.8 视觉取证：顶栏「修前 vs 修后」对照 + 窄屏 + 下拉展开。"""
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
OLD = (BASE / "光学交互实验室_AI_v6.4.7.html").resolve().as_uri()
NEW = (BASE / "光学交互实验室_AI_v6.4.8.html").resolve().as_uri()
OUT = []


def clear(pg):
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")


def shoot(url, w, h, path, crop_h=104, open_menu=False, wait=1600):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(wait)
        clear(pg)
        try:
            if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
                pg.fill("#stuName", "E2E"); pg.fill("#stuNo", "E2E")
                pg.click("#stuAdd"); pg.wait_for_timeout(700)
        except Exception:
            pass
        clear(pg)
        pg.wait_for_timeout(400)
        if open_menu:
            pg.click("#setBtn"); pg.wait_for_timeout(260)
        top = pg.evaluate("() => Math.max(0, document.querySelector('.topbar').getBoundingClientRect().top - 10)")
        pg.screenshot(path=str(path), clip={"x": 0, "y": top, "width": w,
                                           "height": min(crop_h, h - top)})
        b.close()
    return path


print("拍修前 …")
a = shoot(OLD, 1440, 900, BASE / "_v648_448_修前_1440.png")
print("拍修后 …")
b_ = shoot(NEW, 1440, 900, BASE / "_v648_448_修后_1440.png")
open_menu = shoot(NEW, 1440, 900, BASE / "_v648_修后_下拉展开_1440.png", crop_h=210, open_menu=True)
m1 = shoot(NEW, 820, 780, BASE / "_v648_修后_窄屏_820.png", crop_h=140)
m2 = shoot(NEW, 390, 780, BASE / "_v648_修后_手机_390.png", crop_h=140)

# 拼「修前 / 修后」对照（上下）
ia, ib = Image.open(a), Image.open(b_)
W = max(ia.width, ib.width)
LAB = 34
canvas = Image.new("RGB", (W, ia.height + ib.height + LAB + 12), "#101418")
dr = ImageDraw.Draw(canvas)
dr.rectangle([0, 0, W, LAB], fill="#7a2230")
dr.text((10, 9), "BEFORE  V6.4.7 — gap between the button cluster and Setup", fill="#ffffff")
canvas.paste(ia, (0, LAB))
y = LAB + ia.height + 6
dr.rectangle([0, y, W, y + LAB], fill="#1d5c37")
dr.text((10, y + 9), "AFTER  V6.4.8 — cluster flush right, Setup hugging it", fill="#ffffff")
canvas.paste(ib, (0, y + LAB))
cmp_path = BASE / "_v648_对照_修前vs修后.png"
canvas.save(cmp_path)
OUT += [cmp_path, open_menu, m1, m2]
print("OK:")
for p in OUT:
    print(" ", p.name, Image.open(p).size)
