# -*- coding: utf-8 -*-
"""
V6.0.0 端到端验证（真实 Chromium）
覆盖：三个实验的 2D/3D 切换 / 切换按钮几何位置 / iframe 内 3D 真实加载 /
      父页滑块 → 3D 参数同步（跨文档断言真实数值）/ 3D 模式下数据记录照常 /
      全屏进出 / 切页暂停 / 既有 11 个实验与 V5.2.0 日食月食模式回归 /
      双协议（http + file://）/ 多视口
"""
import functools
import http.server
import os
import pathlib
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "光学交互实验室_AI_v6.1.0.html"
PORT = 8793
PASS, FAIL = [], []
IGNORE = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED")


def a(cond, msg, extra=""):
    (PASS if cond else FAIL).append(msg)
    print(("  OK   " if cond else "  FAIL ") + msg + (("   << %s" % extra) if extra else ""))


def real_errs_of(errs):
    return [e for e in errs if not any(k in e for k in IGNORE)]


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    httpd = socketserver.TCPServer(("127.0.0.1", PORT),
                                  functools.partial(Handler, directory=BASE))
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def boot(p, url, w=1440, h=950):
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": w, "height": h})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append("%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(1600)
    return b, pg, errs


def clear_masks(pg):
    pg.evaluate("document.querySelectorAll('.modal-mask,.mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")


def frame_of(pg, key=None):
    """按 3D 框取对应 iframe 的子文档（同一页有 3 个 iframe，必须按 key 定位）"""
    if key:
        el = pg.query_selector('.s3d-frame[data-s3d="%s"] .s3d-ifr' % key)
        if el:
            fr = el.content_frame()
            if fr is not None:
                return fr
    for f in pg.frames:
        if f != pg.main_frame and f.url == "about:srcdoc":
            return f
    return None


def aro(fr, k):
    el = fr.locator("#ro-%s b" % k)
    return el.inner_text() if el.count() else None


SCENES = [
    ("refl", "tab-reflect", "cv-refl",
     [("refl-iSlider", 65)], "i", "65°"),
    ("lens", "tab-lens", "cv-lens",
     [("lens-uSlider", 22)], "m", "1.00 倍"),
    ("mirror", "tab-mirror", "cv-mirr",
     [("mirr-uSlider", 20)], "u", "20.0 cm"),
]


def run(p, url):
    b, pg, errs = boot(p, url)
    print("\n[A] http 通道  " + url)
    a(pg.locator(".ver-badge").inner_text().strip() == "v6.1.0", "版本角标 = v6.1.0")
    a(pg.evaluate("typeof window.S3D === 'object'"), "3D 挂载层就绪")
    a(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "顶部实验标签仍为 11 个")
    a(pg.evaluate("document.querySelectorAll('.s3d-bar').length") == 3, "三处 2D/3D 切换条")
    a(pg.evaluate("document.querySelectorAll('.s3d-frame').length") == 3, "三处 3D 框")
    a(pg.evaluate("document.querySelectorAll('.s3d-ifr[src],.s3d-ifr[srcdoc]').length") == 0,
      "初始三处 iframe 均未注入源码（懒挂载）")

    for key, panel, cv, srclist, rok, rval in SCENES:
        print("\n[%s]" % key)
        clear_masks(pg)
        pg.click('.tab-btn[data-tab="%s"]' % panel[4:])
        pg.wait_for_timeout(400)
        a(pg.evaluate("document.querySelector('.panel.active').id") == panel, "已切到面板 " + panel)

        # 切换条几何：悬浮在 2D 画布区域内（右上角），不压到别的控件
        geo = pg.evaluate("""(k) => {
          const bar=document.querySelector('.s3d-bar[data-s3d="'+k+'"]');
          const cv=document.querySelector('.s3d-frame[data-s3d="'+k+'"]').parentNode.querySelector('canvas');
          const rb=bar.getBoundingClientRect(), rc=cv.getBoundingClientRect();
          return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                  right: Math.round(rc.right-rb.right), botGap: Math.round(rc.bottom-rb.bottom),
                  inLowerHalf: (rb.top + rb.bottom)/2 > (rc.top + rc.bottom)/2,
                  btns:[...bar.querySelectorAll('button[data-m]')].map(b=>b.textContent.trim()),
                  fs: !!bar.querySelector('.s3d-fsb')};
        }""", key)
        a(geo["inside"], "切换条悬浮在 2D 画布内（右下角）",
          "距右 %dpx 距下 %dpx" % (geo["right"], geo["botGap"]))
        a(geo["inLowerHalf"], "切换条位于画布下半部（右下角，不是右上角）", str(geo))
        a(geo["btns"] == ["2D", "3D"] and geo["fs"], "切换条为 2D ｜ 3D 两态（另含全屏键）", str(geo))

        # 切到 3D
        pg.click('.s3d-bar[data-s3d="%s"] button[data-m="3d"]' % key)
        pg.wait_for_timeout(500)
        vis = pg.evaluate("""(k) => {
          const f=document.querySelector('.s3d-frame[data-s3d="'+k+'"]');
          const cv=f.parentNode.querySelector('canvas');
          return {frame:!f.hidden, cv:getComputedStyle(cv).display, srcdoc: !!f.querySelector('.s3d-ifr').getAttribute('srcdoc'),
                  press:[...f.parentNode.querySelectorAll('.s3d-bar button[data-m]')].map(b=>b.getAttribute('aria-pressed'))};
        }""", key)
        a(vis["frame"] and vis["cv"] == "none", "3D 打开：2D 画布让位，3D 框显示", str(vis))
        a(vis["srcdoc"] and vis["press"] == ["false", "true"], "已注入 3D 源码且按钮态正确", str(vis["press"]))

        fr = frame_of(pg, key)
        a(fr is not None, "找到 3D 子文档")
        if fr is None:
            continue
        fr.wait_for_selector("#gl", timeout=20000)
        info = fr.evaluate("""() => {
          const c=document.getElementById('gl');
          let ctx=null; try{ ctx=c.getContext('webgl2')||c.getContext('webgl'); }catch(e){}
          return {three: (window.THREE&&THREE.REVISION)||'?', gl: ctx?(ctx.isContextLost()?'lost':'live'):'none',
                  w:c.width, h:c.height, rows:document.querySelectorAll('#ro .row').length,
                  labels:document.querySelectorAll('#labels .lb').length,
                  objs: S3D.scene ? S3D.scene.children.length : -1};
        }""")
        a(info["three"].startswith("14"), "子场景 three.js 就绪", "r%s" % info["three"])
        a(info["gl"] == "live" and info["w"] > 300, "WebGL 可用且画布已铺开", "%s %dx%d" % (info["gl"], info["w"], info["h"]))
        a(info["objs"] > 5 and info["rows"] >= 5, "场景对象与读数卡均就绪", str(info))

        # 父页滑块 → 3D 参数同步（跨文档断言真实数值）
        for sid, val in srclist:
            pg.evaluate("""(o) => { const s=document.getElementById(o.id); s.value=o.v;
                                     s.dispatchEvent(new Event('input',{bubbles:true})); }""",
                        {"id": sid, "v": val})
        pg.wait_for_timeout(900)
        a(aro(fr, rok) == rval, "父页滑块驱动 3D（%s → %s）" % (sid, rval), aro(fr, rok))

        # 场景内控件 → 父页滑块回写（V6.1.0 新增）
        if key == "refl":
            fr.evaluate("""() => { const s=document.getElementById('fc-i'); s.value=28;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(600)
            a(float(pg.evaluate("document.getElementById('refl-iSlider').value")) == 28,
              "3D 内改入射角 → 回写父页滑块 = 28", pg.evaluate("document.getElementById('refl-iSlider').value"))
            a(aro(fr, "i") == "28°", "3D 读数同步 28°", aro(fr, "i"))
        if key == "mirror":
            fr.evaluate("""() => { const s=document.getElementById('fc-z'); s.value=5;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(500)
            zz = fr.evaluate("""() => { const o=[];
                S3D.scene.traverse(x=>{ if(x.isMesh&&x.geometry&&x.geometry.type==='LatheGeometry')
                  o.push(+x.position.z.toFixed(3)); }); return o; }""")
            a(zz and abs(zz[0] - 0.3) < 0.02 and len(set(zz)) == 1,
              "3D 内左右移动棋子 → 物/像/B 同步（像跟着动）", str(zz))
            a(aro(fr, "z") == "5.0 cm", "读数卡显示左右位置", aro(fr, "z"))
        if key == "lens":
            nz = fr.evaluate("""() => { let n=0;
                S3D.scene.traverse(o=>{ if(o.isMesh&&o.geometry&&o.geometry.type==='CylinderGeometry'
                  && Math.abs(o.position.z) > 0.05) n++; }); return n; }""")
            a(nz >= 10, "光锥是立体锥（有 z≠0 的光线），不是同一平面里的扇面", "z≠0 光束段 %d" % nz)

        # 3D 模式下数据记录仍照常（参数就是同一套）
        pg.evaluate("document.getElementById('%s-dataBody').innerHTML=''" % {
            "refl": "refl", "lens": "lens", "mirror": "mirr"}[key])
        pg.evaluate("""(o) => { const s=document.getElementById(o.id); s.value=o.v;
                                 s.dispatchEvent(new Event('input',{bubbles:true})); }""",
                    {"id": srclist[0][0], "v": srclist[0][1] - 1})
        pg.wait_for_timeout(1500)
        n = pg.locator("#%s-dataBody tr" % {"refl": "refl", "lens": "lens", "mirror": "mirr"}[key]).count()
        a(n == 1, "3D 模式下拖动滑块仍精确记录 1 行", str(n))

        # 全屏（走真实的按钮路径）
        a(pg.locator('.s3d-bar[data-s3d="%s"] .s3d-fsb' % key).is_visible(), "3D 态下全屏按钮可见")
        pg.click('.s3d-bar[data-s3d="%s"] .s3d-fsb' % key)
        pg.wait_for_timeout(900)
        fsinfo = pg.evaluate("""(k) => { const f=document.querySelector('.s3d-frame[data-s3d="'+k+'"]');
          const bar=f.querySelector('.s3d-fsbar');
          return {live:f.classList.contains('is-live'), barH:Math.round(bar.getBoundingClientRect().height),
                  native:!!document.fullscreenElement, mine:(document.fullscreenElement||{}).className||''}; }""", key)
        if not fsinfo["native"]:
            # headless 下首次全屏请求偶发被拒 → 退掉回退层再点一次
            pg.click('.s3d-frame[data-s3d="%s"] .s3d-exit' % key)
            pg.wait_for_timeout(500)
            pg.click('.s3d-bar[data-s3d="%s"] .s3d-fsb' % key)
            pg.wait_for_timeout(900)
            fsinfo = pg.evaluate("""(k) => { const f=document.querySelector('.s3d-frame[data-s3d="'+k+'"]');
              const bar=f.querySelector('.s3d-fsbar');
              return {live:f.classList.contains('is-live'), barH:Math.round(bar.getBoundingClientRect().height),
                      native:!!document.fullscreenElement, mine:(document.fullscreenElement||{}).className||''}; }""", key)
        a(fsinfo["live"] and fsinfo["native"] and 's3d-frame' in fsinfo["mine"],
          "3D 可进入原生全屏（且全屏元素确实是 3D 框）", str(fsinfo))
        a(fsinfo["barH"] > 20, "全屏时顶部「退出全屏」工具条可见", str(fsinfo["barH"]))
        pg.click('.s3d-frame[data-s3d="%s"] .s3d-exit' % key)
        pg.wait_for_timeout(800)
        a(not pg.evaluate("!!document.fullscreenElement"), "点「退出全屏」已退出")

        # 切回 2D
        pg.click('.s3d-bar[data-s3d="%s"] button[data-m="2d"]' % key)
        pg.wait_for_timeout(400)
        a(not pg.locator('.s3d-bar[data-s3d="%s"] .s3d-fsb' % key).is_visible(), "切回 2D 后全屏按钮已隐藏")
        back = pg.evaluate("""(k) => { const f=document.querySelector('.s3d-frame[data-s3d="'+k+'"]');
          const cv=f.parentNode.querySelector('canvas');
          return {frame:f.hidden, cv:getComputedStyle(cv).display}; }""", key)
        a(back["frame"] and back["cv"] != "none", "切回 2D：画布恢复、3D 框收起", str(back))

    # ---------- 回归：V5.2.0 的日食月食 3D 模式仍可用 ----------
    print("\n[回归]")
    pg.click('.tab-btn[data-tab="line"]'); pg.wait_for_timeout(300)
    pg.click('#line-mode .sec[data-m="eclipse"]'); pg.wait_for_timeout(1200)
    a(pg.locator("#line-eclHost").is_visible(), "V5.2.0「日食与月食」3D 模式仍正常")
    ecel = pg.query_selector('#line-eclIfr')
    ec = ecel.content_frame() if ecel else None
    a(ec is not None and ec.evaluate("document.querySelectorAll('#steps .step').length") == 5,
      "日食场景仍能加载（5 阶段）")
    pg.click('#line-mode .sec[data-m="shadow"]'); pg.wait_for_timeout(300)

    # 🔥 全屏归属回归：实验室顶部自带的「全屏」是全屏 documentElement 的；
    #    点实验名【绝不能】把它退掉（V6.0.0 的 bug）
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m=>m.classList.remove('show')); }""")
    pg.click("#fsBtn")
    pg.wait_for_timeout(700)
    st1 = pg.evaluate("({fe: !!document.fullscreenElement, isHtml: document.fullscreenElement === document.documentElement})")
    a(st1["fe"] and st1["isHtml"], "点实验室自带的「全屏」→ 整个页面进入全屏", str(st1))
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(700)
    st2 = pg.evaluate("({fe: !!document.fullscreenElement, isHtml: document.fullscreenElement === document.documentElement})")
    a(st2["fe"] and st2["isHtml"], "★ 点实验名后网页全屏仍在（修复：不再误退 documentElement 全屏）", str(st2))
    pg.click("#fsBtn")
    pg.wait_for_timeout(600)
    a(not pg.evaluate("!!document.fullscreenElement"), "再点一次「全屏」可正常退出")

    ok_tabs = []
    for t in ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"]:
        pg.click('.tab-btn[data-tab="%s"]' % t)
        pg.wait_for_timeout(140)
        ok_tabs.append(pg.evaluate("document.querySelector('.panel.active').id") == "tab-" + t)
    a(all(ok_tabs), "11 个实验标签逐一切换均正常", str([t for t, o in zip(["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"], ok_tabs) if not o]))

    clear_masks(pg)
    pg.click('.tab-btn[data-tab="reflect"]'); pg.wait_for_timeout(300)
    seen = {}
    for _ in range(5):
        seen[pg.evaluate("LANG")] = pg.locator('.s3d-bar[data-s3d="refl"] button[data-m="3d"]').inner_text().strip()
        if len(seen) == 3:
            break
        pg.click("#langBtn"); pg.wait_for_timeout(600)
    for _ in range(5):
        if pg.evaluate("LANG") == "zh":
            break
        pg.click("#langBtn"); pg.wait_for_timeout(600)
    a(seen == {"zh": "3D", "zht": "3D", "en": "3D"}, "三语下切换按钮文案", str(seen))
    a(pg.evaluate("typeof REPORT === 'object' && typeof REC.specOf('line') === 'object'"), "报告模块与记录器未受影响")
    a(pg.evaluate("(window.__rbErrors||[]).length") == 0, "页面看门狗 __rbErrors 为空",
      str(pg.evaluate("(window.__rbErrors||[]).map(e=>e.kind+' '+e.detail.slice(0,80))")))
    a(not pg.evaluate("!!document.getElementById('__rbOverlay')"), "未弹出启动失败浮层")
    errs2 = real_errs_of(errs)
    a(not errs2, "控制台无错误", " | ".join(errs2[:3]))
    pg.screenshot(path=os.path.join(BASE, "_v600_集成_反射3D.png"))
    b.close()


def run_file(p):
    url = (pathlib.Path(BASE) / NAME).resolve().as_uri()
    b, pg, errs = boot(p, url)
    print("\n[B] file:// 通道（双击打开）")
    clear_masks(pg)
    pg.click('.tab-btn[data-tab="mirror"]'); pg.wait_for_timeout(300)
    pg.click('.s3d-bar[data-s3d="mirror"] button[data-m="3d"]'); pg.wait_for_timeout(1800)
    fr = frame_of(pg, "mirror")
    ok = False
    if fr:
        try:
            fr.wait_for_selector("#gl", timeout=20000)
            inf = fr.evaluate("""() => ({t: typeof window.THREE, gl: (()=>{let c=document.getElementById('gl');
                let x=null; try{x=c.getContext('webgl2')||c.getContext('webgl');}catch(e){}
                return x?(x.isContextLost()?'lost':'live'):'none';})(),
                rows:document.querySelectorAll('#ro .row').length})""")
            ok = inf["t"] == "object" and inf["gl"] == "live" and inf["rows"] >= 5
            print("     ", inf)
        except Exception as e:
            print("      子文档探测失败:", e)
    a(ok, "file:// 下 3D 场景正常启动（离线双击可用）")
    a(pg.evaluate("(window.__rbErrors||[]).length") == 0, "file:// 下看门狗无异常")
    a(not real_errs_of(errs), "file:// 通道控制台无错误", " | ".join(real_errs_of(errs)[:3]))
    pg.screenshot(path=os.path.join(BASE, "_v600_file协议_平面镜3D.png"))
    b.close()


def run_viewports(p):
    url = "http://127.0.0.1:%d/%s" % (PORT, NAME.replace(" ", "%20"))
    print("\n[C] 视口 × 字号复扫（切换条不越界、不压画布）")
    b = p.chromium.launch()
    bad = []
    for vw, vh in [(1280, 800), (1440, 900), (1920, 1080), (1024, 800), (768, 1024), (390, 844)]:
        pg = b.new_page(viewport={"width": vw, "height": vh})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(900)
        pg.evaluate("document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")
        line = []
        for z in (0.8, 1.0, 1.4):
            pg.evaluate("window.ZOOM=%s; window.applyZoom&&applyZoom();" % z)
            pg.evaluate("window.switchTab && switchTab('reflect')")
            pg.wait_for_timeout(260)
            g = pg.evaluate("""() => {
              const bar=document.querySelector('.s3d-bar[data-s3d="refl"]');
              const cv=bar.parentNode.querySelector('canvas');
              const rb=bar.getBoundingClientRect(), rc=cv.getBoundingClientRect();
              return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                      inLowerHalf: (rb.top + rb.bottom)/2 > (rc.top + rc.bottom)/2,
                      rows:new Set([...bar.querySelectorAll('button')]
                             .filter(b=>b.getBoundingClientRect().width>0)   /* 隐藏键 rect 全 0，不能计入 */
                             .map(b=>Math.round(b.getBoundingClientRect().top))).size};
            }""")
            if not g["inLowerHalf"]: bad.append((vw, vh, z, "不在右下角"))
            line.append("%s:%s%s" % (z, "in" if g["inside"] else "OUT", g["rows"]))
            if not g["inside"] or g["rows"] != 1:
                bad.append((vw, vh, z, g))
        print("     %4dx%-5d  %s" % (vw, vh, " ".join(line)))
        pg.close()
    a(not bad, "所有视口 × 字号下切换条都在画布内、保持单行", str(bad[:3]))
    b.close()


if __name__ == "__main__":
    httpd = serve()
    try:
        with sync_playwright() as p:
            run(p, "http://127.0.0.1:%d/%s" % (PORT, NAME.replace(" ", "%20")))
            run_file(p)
            run_viewports(p)
    finally:
        httpd.shutdown()
    print("\n" + "=" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL: " + f)
    sys.exit(1 if FAIL else 0)
