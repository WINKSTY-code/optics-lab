# -*- coding: utf-8 -*-
"""
V5.2.0 端到端验证（真实 Chromium）
覆盖：三模式切换 / iframe 内 3D 场景真实加载与动画推进 / 全屏进出 /
      数据记录不污染（精确行数）/ 既有 11 个实验回归 / 三语切换 / 布局不换行 /
      file:// 双击打开同样可用
用法：python e2e_v520.py            （http 服务 + file:// 双通道）
"""
import functools
import http.server
import os
import pathlib
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
NAME = "光学交互实验室_AI_v5.2.0.html"
PORT = 8777

PASS, FAIL = [], []

# 测试自身拦截 CDN 字体造成的资源失败、以及 favicon，不算页面缺陷
IGNORE = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED")


def real_errs_of(errs):
    return [e for e in errs if not any(k in e for k in IGNORE)]


def a(cond, msg, extra=""):
    (PASS if cond else FAIL).append(msg)
    print(("  OK   " if cond else "  FAIL ") + msg + (("   << %s" % extra) if extra else ""))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    h = functools.partial(Handler, directory=BASE)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), h)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def new_content(p, url):
    b = p.chromium.launch(args=[
        "--use-gl=angle",
        "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader",
        "--ignore-gpu-blocklist",
    ])
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    return b, pg, errs


def clear_masks(pg):
    # 只清 class + inline display，绝不写死 display:none（会压过 .modal-mask.show）
    pg.evaluate("document.querySelectorAll('.modal-mask,.mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")


def demo_frame(pg):
    for f in pg.frames:
        if f.url == "about:srcdoc" or (f.name == "" and f != pg.main_frame and "srcdoc" in (f.url or "")):
            return f
    for f in pg.frames:
        if f != pg.main_frame:
            return f
    return None


def run_http(p):
    url = "http://127.0.0.1:%d/%s" % (PORT, NAME.replace(" ", "%20"))
    b, pg, errs = new_content(p, url)
    print("\n[A] http 通道  " + url)

    # ---------- 1. 版本与初始状态 ----------
    a(pg.locator(".ver-badge").inner_text().strip() == "v5.2.0", "版本角标 = v5.2.0")
    a(pg.evaluate("typeof MODULES.line === 'object'"), "MODULES.line 已注册")
    a(pg.locator("#line-eclHost").is_hidden(), "初始 3D 演示容器隐藏")
    a(pg.evaluate("!document.getElementById('line-eclIfr').hasAttribute('srcdoc')"),
      "初始未注入演示源码（懒挂载）")
    a(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "顶部实验标签仍为 11 个")

    clear_masks(pg)
    pg.click('.tab-btn[data-tab="line"]')
    pg.wait_for_timeout(400)
    a(pg.locator("#tab-line").get_attribute("class").find("active") >= 0, "已切到「直线传播」")

    # ---------- 2. 模式按钮：3 个 + 不换行 ----------
    n = pg.locator("#line-mode .sec").count()
    a(n == 3, "模式按钮数量 = 3", str(n))
    a(pg.locator('#line-mode .sec[data-m="eclipse"]').inner_text().strip() == "日食与月食",
      "第三个模式文案 = 日食与月食")

    rows = pg.evaluate("""() => {
      const bs=[...document.querySelectorAll('#line-mode .sec')];
      const box=document.getElementById('line-mode');
      return {tops:[...new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top)))],
              need:bs.reduce((s,b)=>s+b.getBoundingClientRect().width,0)+6*(bs.length-1),
              avail:box.parentNode.clientWidth};
    }""")
    a(len(rows["tops"]) == 1, "1440 视口：三个模式按钮同一行（几何行数=1）", str(rows))

    # ---------- 3. 切到 3D 模式 ----------
    pg.click('#line-mode .sec[data-m="eclipse"]')
    pg.wait_for_timeout(600)
    a(pg.evaluate("getComputedStyle(document.getElementById('cv-line')).display") == "none",
      "3D 模式下 2D 画布已隐藏")
    a(pg.locator("#line-eclHost").is_visible(), "3D 演示容器已显示")
    a(not pg.locator("#line-eclNote").is_hidden(), "数据面板提示「不参与数据记录」已出现")
    a(pg.evaluate("getComputedStyle(document.getElementById('line-reset')).display") == "none",
      "3D 模式下无关的「重置」按钮已隐藏")
    a(pg.evaluate("document.querySelectorAll('#tab-line .slider-g').length") == 4 and
      pg.evaluate("[...document.querySelectorAll('#tab-line .slider-g')].every(g=>getComputedStyle(g).display==='none')"),
      "3D 模式下参数滑块全部隐藏")
    verdict = pg.locator("#verdict-line").inner_text()
    a("日食" in verdict and "月食" in verdict and "直线" in verdict, "结论卡为日食/月食知识点", verdict[:40])
    a(pg.evaluate("!!document.getElementById('line-eclIfr').getAttribute('srcdoc')"), "已注入演示源码")

    # ---------- 4. iframe 内 3D 场景真实加载 ----------
    fr = demo_frame(pg)
    a(fr is not None, "找到 iframe 子文档")
    if fr is None:
        b.close()
        return
    fr.wait_for_selector("#gl", timeout=20000)
    title = fr.evaluate("document.title")
    a(title == "日食与月食 · 光的直线传播", "演示文档标题正确", title)
    info = fr.evaluate("""() => {
      const c=document.getElementById('gl');
      let ctx=null;
      try{ ctx=c.getContext('webgl2')||c.getContext('webgl'); }catch(e){}
      return { three: typeof window.THREE, w:c.width, h:c.height,
               gl: ctx ? (ctx.isContextLost()? 'lost':'live') : 'none',
               steps: document.querySelectorAll('#steps .step').length,
               tabs: document.querySelectorAll('#modes button').length,
               pip: !!document.getElementById('pipcv') };
    }""")
    a(info["three"] == "object", "演示内 three.js 已就绪", str(info["three"]))
    a(info["w"] > 200 and info["h"] > 200, "3D 画布已按容器尺寸铺开", "%dx%d" % (info["w"], info["h"]))
    a(info["gl"] == "live", "WebGL 上下文可用且未丢失", info["gl"])
    a(info["steps"] == 5 and info["tabs"] == 2, "食相 5 阶段 / 日食月食 2 标签就绪", str(info["steps"]))
    a(info["pip"], "观测窗（遮挡比例）存在")

    # 播放：时间轴真实推进（不是"看起来有界面"）
    before = fr.evaluate("document.getElementById('slider').getAttribute('aria-valuenow')")
    fr.click("#play")
    pg.wait_for_timeout(1800)
    after = fr.evaluate("document.getElementById('slider').getAttribute('aria-valuenow')")
    roff = fr.evaluate("document.getElementById('roff').textContent")
    a(float(after) > float(before), "点击播放后时间轴真实推进", "%s -> %s（月球偏移 %s）" % (before, after, roff))
    fr.click("#play")  # 暂停

    # 切到月食模式
    fr.click("#tab-moon")
    pg.wait_for_timeout(700)
    moon = fr.evaluate("""() => ({n:document.getElementById('blurb-name').textContent,
                                 steps:[...document.querySelectorAll('#steps .step .nm')].map(e=>e.textContent)})""")
    a("半影食始" in "".join(moon["steps"]), "切月食后阶段名同步（半影食始…半影食终）", str(moon["steps"]))

    pg.screenshot(path=os.path.join(BASE, "_v520_内嵌演示.png"))

    # ---------- 5. 全屏进出 ----------
    pg.click("#line-eclFs")
    pg.wait_for_timeout(900)
    fs = pg.evaluate("""() => {
      const f=document.getElementById('line-eclFrame');
      const bar=f.querySelector('.ecl-fsbar');
      return {native: !!(document.fullscreenElement||document.webkitFullscreenElement),
              live: f.classList.contains('ecl-live'),
              fb: f.classList.contains('ecl-fs'),
              barH: Math.round(bar.getBoundingClientRect().height),
              btn: document.getElementById('line-eclFs').textContent,
              ifrH: Math.round(document.getElementById('line-eclIfr').getBoundingClientRect().height),
              vh: window.innerHeight};
    }""")
    a(fs["live"], "进入全屏：容器进入 live 态", str(fs))
    a(fs["barH"] > 20, "全屏时顶部「退出全屏」工具条可见", str(fs["barH"]))
    a(fs["ifrH"] >= fs["vh"] - 120, "全屏时 3D 演示铺满视口高度", "%d / vh=%d" % (fs["ifrH"], fs["vh"]))
    a("退出全屏" in fs["btn"], "按钮文案切换为「退出全屏」", fs["btn"])
    pg.screenshot(path=os.path.join(BASE, "_v520_全屏.png"))

    pg.click("#line-eclExit")
    pg.wait_for_timeout(900)
    fs2 = pg.evaluate("""() => {
      const f=document.getElementById('line-eclFrame');
      return {native: !!(document.fullscreenElement||document.webkitFullscreenElement),
              live: f.classList.contains('ecl-live'), fb: f.classList.contains('ecl-fs'),
              btn: document.getElementById('line-eclFs').textContent};
    }""")
    a(not fs2["live"] and not fs2["fb"] and not fs2["native"], "退出全屏后状态完全复位", str(fs2))
    a("全屏演示" in fs2["btn"], "按钮文案复位为「全屏演示」", fs2["btn"])

    # ---------- 6. 数据记录：3D 模式绝不污染 ----------
    pg.evaluate("document.getElementById('line-dataBody').innerHTML=''")
    pg.click("#line-recBtn")
    pg.wait_for_timeout(1400)
    cnt = pg.locator("#line-dataBody tr").count()
    a(cnt == 0, "3D 模式下点「记录」不写入数据表（精确 0 行）", str(cnt))
    a(pg.evaluate("REC.snapshot('line')") is None, "3D 模式下 REC.snapshot('line') 返回 null")

    # 回到影子模式：自动记录仍精确 1 行
    pg.click('#line-mode .sec[data-m="shadow"]')
    pg.wait_for_timeout(500)
    a(pg.evaluate("getComputedStyle(document.getElementById('cv-line')).display") != "none",
      "切回影子形成：2D 画布恢复显示")
    a(pg.locator("#line-eclHost").is_hidden(), "切回影子形成：3D 演示容器收起")
    pg.evaluate("""() => { const s=document.getElementById('line-uSlider'); s.value=42; s.dispatchEvent(new Event('input',{bubbles:true})); }""")
    pg.wait_for_timeout(1500)
    rows = pg.evaluate("""() => [...document.querySelectorAll('#line-dataBody tr')].map(tr=>[...tr.children].map(td=>td.textContent))""")
    a(len(rows) == 1, "影子模式下拖动滑块 → 精确 1 行", str(len(rows)))
    if rows:
        a(rows[-1][1] == "影子形成" and rows[-1][2] == "42.0", "末行内容正确（模式/物距）", str(rows[-1]))
    a(pg.evaluate("JSON.stringify(REC.snapshot('line'))").find("42.0") > 0, "影子模式 snapshot 返回真实读数")

    # ---------- 7. 回归：11 个实验逐个切换 ----------
    tabs = ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"]
    ok_tabs = []
    for t in tabs:
        pg.click('.tab-btn[data-tab="%s"]' % t)
        pg.wait_for_timeout(160)
        act = pg.evaluate("document.querySelector('.panel.active').id")
        ok_tabs.append(act == "tab-" + t)
    a(all(ok_tabs), "11 个实验标签逐一切换均正常", str([t for t, o in zip(tabs, ok_tabs) if not o]))

    # ---------- 8. 三语切换 ----------
    clear_masks(pg)
    pg.click('.tab-btn[data-tab="line"]')
    pg.wait_for_timeout(300)
    seen = {}
    # LANG 循环是 zh -> zht -> en -> zh，不要写死点击次数，读到三种为止
    for _ in range(5):
        seen[pg.evaluate("LANG")] = pg.locator('#line-mode .sec[data-m="eclipse"]').inner_text().strip()
        if len(seen) == 3:
            break
        pg.click("#langBtn")
        pg.wait_for_timeout(600)
    for _ in range(5):
        if pg.evaluate("LANG") == "zh":
            break
        pg.click("#langBtn")
        pg.wait_for_timeout(600)
    a(seen.get("en") == "Eclipses" and seen.get("zht") == "日食與月食" and seen.get("zh") == "日食与月食",
      "三语模式下第三个按钮文案正确", str(seen))
    a(pg.evaluate("LANG") == "zh", "语言已回到中文", pg.evaluate("LANG"))

    # ---------- 9. 主题切换 ----------
    pg.click("#themeBtn")
    pg.wait_for_timeout(600)
    pg.click('#line-mode .sec[data-m="eclipse"]')
    pg.wait_for_timeout(500)
    a(pg.locator("#line-eclHost").is_visible(), "切黑板主题后 3D 演示仍正常显示")
    pg.screenshot(path=os.path.join(BASE, "_v520_黑板主题.png"))
    pg.click("#themeBtn")
    pg.wait_for_timeout(400)

    # ---------- 10. 报告页仍可取到数据 ----------
    a(pg.evaluate("typeof REPORT === 'object' && typeof REC.specOf('line') === 'object'"),
      "报告模块与 REC 规格仍可用（回归）")
    a(pg.evaluate("document.querySelectorAll('[data-i18n]').length") > 200, "i18n 绑定节点数量正常")

    # ---------- 11. 页面自身健康信号 ----------
    a(pg.evaluate("(window.__rbErrors||[]).length") == 0,
      "页面自带错误看门狗 __rbErrors 为空",
      str(pg.evaluate("(window.__rbErrors||[]).map(e=>e.kind+' '+e.detail.slice(0,90))")))
    a(not pg.evaluate("!!document.getElementById('__rbOverlay')"), "未弹出「初始化失败」浮层")
    real_errs = real_errs_of(errs)
    a(not real_errs, "控制台无错误", " | ".join(real_errs[:3]))
    b.close()


def run_file(p):
    pth = pathlib.Path(BASE) / NAME
    url = pth.resolve().as_uri()
    b, pg, errs = new_content(p, url)
    print("\n[B] file:// 通道（双击打开）")
    clear_masks(pg)
    pg.click('.tab-btn[data-tab="line"]')
    pg.wait_for_timeout(300)
    pg.click('#line-mode .sec[data-m="eclipse"]')
    pg.wait_for_timeout(1500)
    fr = demo_frame(pg)
    ok = False
    if fr:
        try:
            fr.wait_for_selector("#gl", timeout=20000)
            info = fr.evaluate("""() => ({t: typeof window.THREE, n:document.querySelectorAll('#steps .step').length,
                                          w:document.getElementById('gl').width})""")
            ok = info["t"] == "object" and info["n"] == 5 and info["w"] > 200
            print("     演示信息:", info)
        except Exception as e:
            print("     子文档探测失败:", e)
    a(ok, "file:// 下 srcdoc 内 3D 演示正常启动（离线双击可用）")
    a(pg.evaluate("(window.__rbErrors||[]).length") == 0, "file:// 下页面看门狗无异常",
      str(pg.evaluate("(window.__rbErrors||[]).map(e=>e.kind)")))
    real_errs = real_errs_of(errs)
    a(not real_errs, "file:// 通道控制台无错误", " | ".join(real_errs[:3]))
    pg.screenshot(path=os.path.join(BASE, "_v520_file协议.png"))
    b.close()


def run_viewports(p):
    print("\n[C] 模式按钮换行复扫（视口 × 字号缩放 A＋）")
    url = "http://127.0.0.1:%d/%s" % (PORT, NAME.replace(" ", "%20"))
    b = p.chromium.launch()
    bad = []
    for vw, vh in [(1280, 800), (1366, 768), (1440, 900), (1600, 900), (1920, 1080), (1024, 800), (768, 1024), (390, 844)]:
        pg = b.new_page(viewport={"width": vw, "height": vh})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(900)
        pg.evaluate("document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")
        pg.evaluate("window.switchTab && switchTab('line')")
        pg.wait_for_timeout(300)
        line = []
        for z in (0.8, 1.0, 1.1, 1.2, 1.3, 1.4):
            pg.evaluate("ZOOM=%s; applyZoom();" % z)
            pg.wait_for_timeout(180)
            g = pg.evaluate("""() => {
              const bs=[...document.querySelectorAll('#line-mode .sec')];
              return {rows:new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top))).size,
                      inner:[...new Set(bs.map(b=>Math.round(b.getBoundingClientRect().height)))].length};
            }""")
            line.append("%s:%d/%d" % (z, g["rows"], g["inner"]))
            # ≥768 视口下任何缩放都必须单行；按钮内部标签（inner）任何情况都不得折行
            if vw >= 768 and g["rows"] != 1:
                bad.append((vw, vh, z, g["rows"]))
            if g["inner"] != 1:
                bad.append((vw, vh, z, "标签内部折行"))
        print("     %4dx%-5d  %s   (rows/inner)" % (vw, vh, " ".join(line)))
        pg.close()
    a(not bad, "≥768 视口 × 全档字号下三个模式按钮均保持单行、标签不折行", str(bad[:4]))
    b.close()


if __name__ == "__main__":
    httpd = serve()
    try:
        with sync_playwright() as p:
            run_http(p)
            run_file(p)
            run_viewports(p)
    finally:
        httpd.shutdown()

    print("\n" + "=" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("  FAIL: " + f)
    sys.exit(1 if FAIL else 0)
