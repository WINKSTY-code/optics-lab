# -*- coding: utf-8 -*-
"""
V6.4.5 端到端验证（真实 Chromium，file:// 协议）
覆盖：懒挂载 / 2D·3D 切换 / 3D 真实数值 / 右下角让位与不重叠 / 全屏（自己的 + 别人的）/
      切模式互斥 / 3D 态不落数据表 / 切页真的停 rAF / 既有功能回归 / 健康信号。
"""
import pathlib
import sys
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()
FAILS = []


def ck(cond, msg, extra=""):
    print("%s %s%s" % ("  OK  " if cond else "  FAIL", msg, ("  " + str(extra)) if extra else ""))
    if not cond:
        FAILS.append(msg)


def num(v):
    return float(v)


def clear_masks(pg):
    """清掉所有遮罩层。

    坑：#aiCfgMask 是 showModal() 动态创建的 id（不是类），且 .modal-mask 不在
    任何通用类名里。只写 `.aiCfgMask` / `.mask` 都选不中它 → 点击被拦截 30s 超时。
    """
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show');
        m.classList.remove('is-closing');   // .is-closing 是 display:flex !important，必须一起摘
      });
    }""")


def dismiss_first_run(pg):
    """全新 profile 无 localStorage → firstRunGate() 会在 400ms 后弹「学生姓名」窗
    （复用 #aiCfgMask）。走真实路径填完它，比硬删 show 更贴近真机。"""
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试")
        pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd")          # 内部会 alert()，Playwright 默认自动 dismiss（不能走 click() 包装，否则遮罩被清掉按钮就点不着了）
        pg.wait_for_timeout(700)
    clear_masks(pg)


def click(pg, sel, **kw):
    """先清遮罩再点，短超时快速失败。"""
    clear_masks(pg)
    kw.setdefault("timeout", 8000)
    pg.click(sel, **kw)
    pg.wait_for_timeout(150)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                    "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        # 拦掉外网 CDN，避免 file:// 下被拖死
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        dismiss_first_run(pg)

        print("\n== 0 启动健康 ==")
        ck(pg.evaluate("!document.getElementById('__rbOverlay')"), "启动失败浮层不存在")
        ck(pg.evaluate("window.__APP_READY === true"), "__APP_READY 已置真")
        ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本为空",
           pg.evaluate("(window.__rbErrors||[]).length"))
        ck(pg.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v6.4.5",
           "版本角标为 v6.4.5")

        print("\n== 1 直线传播页 · 影子形成默认 2D ==")
        pg.evaluate("switchTab('line')")
        pg.wait_for_timeout(400)
        ck(pg.is_visible('.s3d-bar[data-s3d="shadow"]'), "影子 3D 切换条可见")
        ck(not pg.is_visible('.s3d-bar[data-s3d="pinhole"]'), "小孔切换条此时隐藏")
        ck(pg.is_visible('#cv-line'), "2D 画布可见")
        ck(pg.evaluate("document.querySelector('.s3d-frame[data-s3d=\"shadow\"]').hidden"),
           "3D 框隐藏")

        geo = pg.evaluate("""() => {
          const st = document.querySelector('#tab-line .s3d-stage').getBoundingClientRect();
          const b  = document.querySelector('.s3d-bar[data-s3d="shadow"]').getBoundingClientRect();
          return { dx: st.right - b.right, dy: st.bottom - b.bottom, w: b.width, h: b.height,
                   srcdoc: document.querySelector('.s3d-frame[data-s3d="shadow"] .s3d-ifr').hasAttribute('srcdoc') };
        }""")
        ck(abs(geo["dx"] - 12) <= 2 and abs(geo["dy"] - 10) <= 2,
           "切换条贴在实验区右下角（右内边距 %.1f / 下内边距 %.1f）" % (geo["dx"], geo["dy"]))
        ck(not geo["srcdoc"], "未点 3D 前不挂载（懒挂载）")
        print("       切换条尺寸 %.0f×%.0f" % (geo["w"], geo["h"]))

        print("\n== 2 切到 3D案例 ==")
        click(pg, '.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(2500)
        ck(pg.evaluate("S3D.isOn('shadow')"), "S3D.isOn('shadow') 为真")
        ck(not pg.evaluate("document.querySelector('.s3d-frame[data-s3d=\"shadow\"]').hidden"),
           "3D 框可见")
        ck(pg.evaluate("document.getElementById('cv-line').style.display") == "none",
           "2D 画布已让位")
        ck(pg.evaluate("document.querySelector('.s3d-frame[data-s3d=\"shadow\"] .s3d-ifr')"
                       ".hasAttribute('srcdoc')"), "iframe 已注入 srcdoc")

        el = pg.query_selector('.s3d-frame[data-s3d="shadow"] .s3d-ifr')
        fr = el.content_frame()
        ck(fr is not None, "取到 3D 场景子文档")
        ck(fr.evaluate("document.body.className") == "embed", "子文档处于嵌入模式(body.embed)")
        ck(fr.evaluate("getComputedStyle(document.getElementById('btnFull')).display") == "none",
           "场景自带全屏按钮已隐藏（全屏交给父页）")

        # ---- 真实数值（白盒断言，不只看"有输出"）
        st = fr.evaluate("window.__demo.state()")
        ck(abs(num(st["KA"]) - 3.2 / (3.2 - 1.7)) < 1e-6, "K_A = H/(H−h_A) = %.5f" % st["KA"])
        ck(abs(num(st["KB"]) - 3.2 / (3.2 - 1.1)) < 1e-6, "K_B = H/(H−h_B) = %.5f" % st["KB"])
        ck(abs(num(st["crit"]) - 3.5) < 1e-6, "d 最小处 x_B = %.3f（两影尖端重合）" % st["crit"])
        fr.evaluate("window.__demo.seek(0.5)")
        pg.wait_for_timeout(250)
        st2 = fr.evaluate("window.__demo.state()")
        exp_d = abs((0.30 + 5.4 * 0.5) * (3.2 / 1.5) - (1.30 + 5.4 * 0.5) * (3.2 / 2.1))
        ck(abs(num(st2["calc"]["d"]) - exp_d) < 1e-3,
           "p=0.5 时 d = %.4f m（解析值 %.4f）" % (st2["calc"]["d"], exp_d))
        ck(fr.evaluate("window.__dbg.renderer.info.render.calls") > 0, "WebGL 真出图（draw calls %d）"
           % fr.evaluate("window.__dbg.renderer.info.render.calls"))
        ck(fr.evaluate("getComputedStyle(document.getElementById('err')).display") == "none",
           "场景内报错浮层未出现")

        # ---- 右下角让位 + 与父页切换条不重叠
        bar = pg.evaluate("""() => { const r = document.querySelector('.s3d-bar[data-s3d="shadow"]')
            .getBoundingClientRect(); return {l:r.left,t:r.top,r:r.right,b:r.bottom}; }""")
        frect = pg.evaluate("""() => { const r = document.querySelector('.s3d-frame[data-s3d="shadow"]')
            .getBoundingClientRect(); return {l:r.left,t:r.top}; }""")
        dock = fr.evaluate("""() => { const r = document.getElementById('dock').getBoundingClientRect();
            return {l:r.left,t:r.top,r:r.right,b:r.bottom}; }""")
        dl, dr = frect["l"] + dock["l"], frect["l"] + dock["r"]
        dt, db = frect["t"] + dock["t"], frect["t"] + dock["b"]
        overlap = not (dr <= bar["l"] or dl >= bar["r"] or db <= bar["t"] or dt >= bar["b"])
        ck(not overlap, "场景底部控制条与父页切换条不重叠（控制条右边界 %.0f / 切换条左边界 %.0f）"
           % (dr, bar["l"]))
        ck(dr <= frect["l"] + fr.evaluate("innerWidth") - 178 + 1,
           "控制条已为切换条让出 178px")
        pg.screenshot(path=str(BASE / "_v645_影子3D.png"))

        print("\n== 3 影子 3D 态不污染数据表 ==")
        ck(pg.is_visible('#line-s3dNote'), "数据面板提示角标已显示")
        n0 = pg.evaluate("document.querySelectorAll('#line-dataBody tr').length")
        pg.evaluate("""var s=document.getElementById('line-uSlider'); s.value=42;
                       s.dispatchEvent(new Event('input',{bubbles:true}));""")
        pg.wait_for_timeout(1900)
        n1 = pg.evaluate("document.querySelectorAll('#line-dataBody tr').length")
        ck(n1 == n0, "切 3D 后自动记录不落表（%d -> %d 行）" % (n0, n1))
        click(pg, '#line-recBtn')
        pg.wait_for_timeout(400)
        n2 = pg.evaluate("document.querySelectorAll('#line-dataBody tr').length")
        ck(n2 == n0, "手动点记录也不落表（%d -> %d 行）" % (n0, n2))

        print("\n== 4 切模式：两条切换条互斥、3D 收回 ==")
        click(pg, '#line-mode .sec[data-m="pinhole"]')
        pg.wait_for_timeout(500)
        ck(pg.is_visible('.s3d-bar[data-s3d="pinhole"]') and not pg.is_visible('.s3d-bar[data-s3d="shadow"]'),
           "小孔模式：只剩小孔切换条")
        ck(not pg.evaluate("S3D.isOn('shadow')"), "离开影子模式后 3D 已收回")
        ck(pg.is_visible('#cv-line'), "2D 画布已恢复")
        ck(not pg.is_visible('#line-s3dNote'), "提示角标已隐藏")
        click(pg, '#line-mode .sec[data-m="shadow"]')
        pg.wait_for_timeout(500)
        ck(pg.is_visible('.s3d-bar[data-s3d="shadow"]') and not pg.is_visible('.s3d-bar[data-s3d="pinhole"]'),
           "回到影子模式：只剩影子切换条（另一条没有被置回显示）")

        print("\n== 5 切到别的实验页：3D 真的停 rAF；切回来能醒 ==")
        click(pg, '.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(2200)
        el = pg.query_selector('.s3d-frame[data-s3d="shadow"] .s3d-ifr')
        fr = el.content_frame()
        ck(fr.evaluate("window.__demo.run()") is True, "3D 态下 rAF 在跑")
        # ★ 必须走【真实点击】切页：暂停逻辑挂在 .tab-btn 的 click 委托上
        #   （父页 S3D 层 11078 行）。用 evaluate("switchTab('lens')") 会绕过它，
        #   测出来的是假象 —— 用户点不动的东西不算数。
        click(pg, '.tab-btn[data-tab="lens"]')
        pg.wait_for_timeout(900)
        ck(fr.evaluate("window.__demo.run()") is False, "点 tab 切走后 rAF 已停（省电）")
        f1 = fr.evaluate("window.__dbg.renderer.info.render.frame")
        pg.wait_for_timeout(800)
        f2 = fr.evaluate("window.__dbg.renderer.info.render.frame")
        ck(f1 == f2, "切走后确实不再出帧（帧计数 %d → %d）" % (f1, f2))
        click(pg, '.tab-btn[data-tab="line"]')
        pg.wait_for_timeout(900)
        ck(fr.evaluate("window.__demo.run()") is True, "切回来 rAF 已恢复")
        f3 = fr.evaluate("window.__dbg.renderer.info.render.frame")
        pg.wait_for_timeout(800)
        f4 = fr.evaluate("window.__dbg.renderer.info.render.frame")
        ck(f4 > f3, "切回来后重新出帧（帧计数 %d → %d）" % (f3, f4))

        print("\n== 6 全屏：自己的能进能出，别人的不被误退 ==")
        click(pg, '.s3d-bar[data-s3d="shadow"] .s3d-fsb')
        pg.wait_for_timeout(700)
        ck(pg.evaluate("!!document.fullscreenElement && "
                       "document.fullscreenElement.classList.contains('s3d-frame')"),
           "自己的 3D 框进入全屏")
        ck(pg.evaluate("document.querySelector('.s3d-frame[data-s3d=\"shadow\"]').classList.contains('is-live')"),
           "全屏工具条已出现")
        click(pg, '.s3d-frame[data-s3d="shadow"] .s3d-exit')
        pg.wait_for_timeout(600)
        ck(not pg.evaluate("!!document.fullscreenElement"), "退出全屏成功")

        click(pg, '#fsBtn')
        pg.wait_for_timeout(600)
        ck(pg.evaluate("document.fullscreenElement === document.documentElement"),
           "作品自带全屏按钮进入网页全屏")
        click(pg, '.tab-btn[data-tab="line"]')
        pg.wait_for_timeout(400)
        click(pg, '.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(600)
        ck(pg.evaluate("document.fullscreenElement === document.documentElement"),
           "走我的入口后，别人的网页全屏仍在（跨模块不误退）★")
        click(pg, '#fsBtn')
        pg.wait_for_timeout(500)
        ck(not pg.evaluate("!!document.fullscreenElement"), "再次点击退出网页全屏")

        print("\n== 7 回归：既有实验与 3D 场景不受影响 ==")
        ck(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11,
           "导航仍 11 个实验（含 11 · 挑战模式）")
        ck(pg.evaluate("document.querySelectorAll('canvas').length") == 11,
           "主文档仍 11 个画布（10 个实验 + 挑战模式判卷画布）")
        ck(pg.evaluate("document.querySelectorAll('.panel').length") == 12, "面板仍 12 块")
        # MODULES 是 const（顶层词法绑定），不在 window 上 → 只能用标识符 typeof 判
        ck(pg.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object' "
                       "&& typeof S3D === 'object'"),
           "MODULES / REPORT / S3D 俱在")
        ck(pg.evaluate("Object.keys(S3D).length") >= 7, "S3D 对外接口完整")
        tabs = ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo"]
        ok = True
        for t in tabs:
            pg.evaluate("switchTab('%s')" % t)
            pg.wait_for_timeout(180)
            if not pg.evaluate("document.getElementById('tab-%s').classList.contains('active')" % t):
                ok = False
        ck(ok, "10 个实验页都能切过去（挑战模式另计）")
        # 既有 3D（光的反射）仍可切换
        pg.evaluate("switchTab('reflect')")
        pg.wait_for_timeout(300)
        click(pg, '.s3d-bar[data-s3d="refl"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(2200)
        ck(pg.evaluate("S3D.isOn('refl')") and
           pg.evaluate("document.querySelector('.s3d-frame[data-s3d=\"refl\"] .s3d-ifr').hasAttribute('srcdoc')"),
           "既有「光的反射」3D 照常工作（回归）")
        click(pg, '.s3d-bar[data-s3d="refl"] .s3d-b[data-m="2d"]')
        pg.wait_for_timeout(400)

        print("\n== 8 收尾健康 ==")
        noise = ("Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED", "favicon")
        real = [e for e in errs if not any(n in e for n in noise)]
        ck(not real, "控制台无真实错误", real[:3])
        ck(pg.evaluate("!document.getElementById('__rbOverlay')"), "全程未弹启动失败浮层")
        ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本仍为空")
        b.close()

    print("\n" + ("=" * 60))
    if FAILS:
        print("失败 %d 项：" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
