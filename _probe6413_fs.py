# -*- coding: utf-8 -*-
"""v6.4.13 功能验证：切页回来后 3D 右下角全屏按钮必须可用"""
import sys, time
from playwright.sync_api import sync_playwright

URL = "file:///C:/Users/Administrator/Desktop/AI%E5%85%89%E5%AD%A6%E5%8F%82%E8%B5%9B/%E5%85%89%E5%AD%A6%E4%BA%A4%E4%BA%92%E5%AE%9E%E9%AA%8C%E5%AE%A4_AI_v6.4.13.html"
F = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.13.html"
URL = "file:///" + F.replace("\\", "/")

errors = []

def fs_active(pg):
    return pg.evaluate("() => !!document.fullscreenElement || !!document.querySelector('.s3d-frame.is-fs')")

def enter_3d(pg, key):
    pg.click('.tab-btn[data-tab="%s"]' % {"refl": "reflect", "lens": "lens"}[key])
    pg.wait_for_timeout(300)
    pg.click('.s3d-bar[data-s3d="%s"] .s3d-b[data-m="3d"]' % key)
    pg.wait_for_timeout(800)

def click_fsb(pg, key):
    pg.click('.s3d-bar[data-s3d="%s"] .s3d-fsb' % key)
    pg.wait_for_timeout(600)

def exit_fs(pg):
    pg.evaluate("() => { try{ document.exitFullscreen && document.exitFullscreen(); }catch(e){} }")
    pg.wait_for_timeout(400)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_selector(".ver-badge", timeout=60000)
    pg.wait_for_timeout(1500)
    print("启动完成，版本角标:", pg.text_content(".ver-badge").strip())

    # ---- 基线：首次进 3D，全屏可用 ----
    enter_3d(pg, "refl")
    print("进入3D后 S3D.isOn('refl') =", pg.evaluate("() => S3D.isOn('refl')"))
    click_fsb(pg, "refl")
    t1 = fs_active(pg)
    print("基线·点全屏按钮 → 全屏生效:", t1)
    exit_fs(pg)

    # ---- 场景A：切走 >= 31s（触发静置回收 unmount）再切回 ----
    pg.click('.tab-btn[data-tab="lens"]')
    print("已切到凸透镜页，等待 31s 触发静置回收……")
    pg.wait_for_timeout(31500)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(2000)
    on_after = pg.evaluate("() => S3D.isOn('refl')")
    print("切回后 S3D.isOn('refl') =", on_after, "（修复点：必须为 true）")
    click_fsb(pg, "refl")
    t2 = fs_active(pg)
    print("场景A·切回后点全屏按钮 → 全屏生效:", t2, "★本次修复目标")
    exit_fs(pg)

    # ---- 场景B：快速切换（<30s，不触发回收）回归 ----
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(2000)
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(1200)
    click_fsb(pg, "refl")
    t3 = fs_active(pg)
    print("场景B·快速切回后点全屏按钮 → 全屏生效:", t3)
    exit_fs(pg)

    # ---- 场景C：切走期间进了别的实验的3D（互斥回收路径）再切回 ----
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(400)
    enter_3d(pg, "lens")           # setMode('lens','3d') → reclaimOthers → unmount('refl')
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(1500)
    on_c = pg.evaluate("() => S3D.isOn('refl')")
    click_fsb(pg, "refl")
    t4 = fs_active(pg)
    print("场景C·互斥回收后切回 S3D.isOn('refl') =", on_c, "→ 全屏生效:", t4)
    exit_fs(pg)

    b.close()

print("页面 JS 异常:", errors if errors else "无")
ok = t1 and t2 and t3 and t4 and not errors
print("\n===== 验证结论:", "全部通过 ✅" if ok else "存在失败 ❌", "=====")
sys.exit(0 if ok else 1)
