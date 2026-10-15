# -*- coding: utf-8 -*-
"""凹透镜/凸透镜画布截图（toDataURL，绕过字体加载等待）"""
import base64, io
from playwright.sync_api import sync_playwright

F = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.13.html"
OUT = r"C:\Users\Administrator\Desktop\AI光学参赛\_chk6413"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto("file:///" + F.replace("\\", "/"), wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_selector(".ver-badge", timeout=60000)
    pg.wait_for_timeout(1200)
    pg.evaluate("() => document.querySelectorAll('.modal-mask.show').forEach(m => m.classList.remove('show'))")
    pg.click('.tab-btn[data-tab="lensfx"]')
    pg.wait_for_timeout(600)
    for tag, btn, name in [("凹透镜", "concave", "凹透镜_修正后"), ("凸透镜", "convex", "凸透镜_回归")]:
        pg.click('#lfx-type .sec[data-t="%s"]' % btn)
        pg.wait_for_timeout(500)
        data = pg.evaluate("() => document.getElementById('cv-lfx').toDataURL('image/png')")
        io.open("%s\\%s.png" % (OUT, name), "wb").write(base64.b64decode(data.split(",", 1)[1]))
        print("已存:", name)
    b.close()
print("done")
