# -*- coding: utf-8 -*-
"""v6.4.13 综合验证：① 3D全屏按钮切页三场景 ② 凹透镜②号光线几何 ③ 截图留档"""
import sys
from playwright.sync_api import sync_playwright

F = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.13.html"
URL = "file:///" + F.replace("\\", "/")
OUT = r"C:\Users\Administrator\Desktop\AI光学参赛"
errors = []

def is_red(pg, x, y):
    return pg.evaluate(
        """([x,y]) => { const cv=document.getElementById('cv-lfx');
             if(x<0||y<0||x>=cv.width||y>=cv.height) return false;
             const d=cv.getContext('2d').getImageData(x,y,1,1).data;
             return (d[0]>200&&d[1]>=80&&d[1]<=145&&d[2]>=35&&d[2]<=105)||(d[0]>180&&d[1]>=35&&d[1]<=100&&d[2]<=60); }""",
        [x, y])

def col_red(pg, x, y0, y1):
    for y in range(y0, y1 + 1):
        if is_red(pg, x, y): return y
    return None

def fs_active(pg):
    return pg.evaluate("() => !!document.fullscreenElement || !!document.querySelector('.s3d-frame.is-fs')")

def enter_3d(pg, key, tab):
    pg.click('.tab-btn[data-tab="%s"]' % tab)
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
    pg.wait_for_timeout(1200)
    pg.evaluate("() => document.querySelectorAll('.modal-mask.show').forEach(m => m.classList.remove('show'))")
    print("启动完成，版本角标:", pg.text_content(".ver-badge").strip())

    # ================= 一、3D 全屏按钮 =================
    enter_3d(pg, "refl", "reflect")
    click_fsb(pg, "refl")
    t1 = fs_active(pg); exit_fs(pg)
    print("基线·首次进3D点全屏 →", t1)

    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(31500)                     # 触发静置回收（30s）
    pg.click('.tab-btn[data-tab="reflect"]')
    pg.wait_for_timeout(2000)
    onA = pg.evaluate("() => S3D.isOn('refl')")
    click_fsb(pg, "refl")
    t2 = fs_active(pg); exit_fs(pg)
    print("场景A·切走31s再切回 isOn =", onA, "→ 全屏生效:", t2)

    pg.click('.tab-btn[data-tab="lens"]'); pg.wait_for_timeout(2000)
    pg.click('.tab-btn[data-tab="reflect"]'); pg.wait_for_timeout(1200)
    click_fsb(pg, "refl")
    t3 = fs_active(pg); exit_fs(pg)
    print("场景B·快速切回 → 全屏生效:", t3)

    pg.click('.tab-btn[data-tab="lens"]'); pg.wait_for_timeout(400)
    enter_3d(pg, "lens", "lens")                   # 互斥回收路径
    pg.click('.tab-btn[data-tab="reflect"]'); pg.wait_for_timeout(1500)
    onC = pg.evaluate("() => S3D.isOn('refl')")
    click_fsb(pg, "refl")
    t4 = fs_active(pg); exit_fs(pg)
    print("场景C·互斥回收后切回 isOn =", onC, "→ 全屏生效:", t4)

    # ================= 二、凹透镜②号光线 =================
    pg.click('.tab-btn[data-tab="lensfx"]')
    pg.wait_for_timeout(600)
    pg.click('#lfx-type .sec[data-t="concave"]')
    pg.wait_for_timeout(500)
    geo = pg.evaluate("""() => {
      const cv = document.getElementById('cv-lfx');
      return { W: cv.width, H: cv.height, cx: cv.width/2, cy: cv.height/2 };
    }""")
    W, H, CX, CY = geo["W"], geo["H"], geo["cx"], geo["cy"]
    f = 100.0                                       # 默认焦距（页面加载默认值）
    inY2 = CY - 92
    Fpx = CX + f
    yHit = inY2 + (CY - inY2) * ((CX - 20) / (Fpx - 20))
    print("理论关键点: F'=(%d,%d) 透镜命中=(460,%.1f)" % (Fpx, CY, yHit))

    hit_inc = sum(1 for x in range(100, 421, 40) if col_red(pg, x, int(inY2 + (yHit - inY2) * (x - 20) / (CX - 20)) - 4, int(inY2 + (yHit - inY2) * (x - 20) / (CX - 20)) + 4))
    hit_ext = sum(1 for x in range(470, 556, 5) if col_red(pg, x, int(yHit + (CY - yHit) * (x - CX) / (Fpx - CX)) - 3, int(yHit + (CY - yHit) * (x - CX) / (Fpx - CX)) + 3))
    hit_out = sum(1 for x in range(640, 861, 20) if col_red(pg, x, int(yHit) - 3, int(yHit) + 3))
    old_cross = col_red(pg, CX - f, CY - 6, CY + 6)      # 旧错误画法会在此（左侧虚焦点处）穿轴
    print("②入射线采样命中 %d/9（实线应≥7）" % hit_inc)
    print("②延长虚线过F'采样命中 %d/18（虚线应≥8）" % hit_ext)
    print("②出射平行段采样命中 %d/12（实线应=12）" % hit_out)
    print("旧错误路径（左侧虚焦点处穿轴）残留红像素:", old_cross, "（应为 None）")
    pg.locator("#cv-lfx").screenshot(path=OUT + r"\\_chk6413\\凹透镜修正后.png")

    pg.click('#lfx-type .sec[data-t="convex"]')
    pg.wait_for_timeout(500)
    hit_c2 = sum(1 for x in range(100, 421, 40) if col_red(pg, x, int(CY - 92 + (CY - (CY - 92)) * (x - 20) / (CX - f - 20)) - 4, int(CY - 92 + (CY - (CY - 92)) * (x - 20) / (CX - f - 20)) + 4))
    print("凸透镜②过焦点回归采样命中 %d/9（应≥7，未受影响）" % hit_c2)
    pg.locator("#cv-lfx").screenshot(path=OUT + r"\\_chk6413\\凸透镜回归.png")

    b.close()

ok = (t1 and t2 and t3 and t4 and hit_inc >= 7 and hit_ext >= 8 and hit_out == 12
      and old_cross is None and hit_c2 >= 7 and not errors)
print("页面 JS 异常:", errors if errors else "无")
print("\n===== 综合验证结论:", "全部通过 ✅" if ok else "存在失败 ❌", "=====")
sys.exit(0 if ok else 1)
