# -*- coding: utf-8 -*-
"""
单个 3D 场景的独立验证（真实 Chromium）
用法：python _s3d_test.py refl|lens|mirror [--shots]
断言真实数值，不只断言"有界面"。
"""
import os
import sys
import pathlib
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
SCENES = {
    "refl": "3D_光的反射_可折转纸板.html",
    "lens": "3D_凸透镜成像.html",
    "mirror": "3D_平面镜成像_棋子.html",
}
PASS, FAIL = [], []


def a(cond, msg, extra=""):
    (PASS if cond else FAIL).append(msg)
    print(("  OK   " if cond else "  FAIL ") + msg + (("   << %s" % extra) if extra else ""))


def ro(pg, k):
    el = pg.locator("#ro-%s b" % k)
    return el.inner_text() if el.count() else None


def run(key, shots=False):
    fn = SCENES[key]
    url = (pathlib.Path(BASE) / fn).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                    "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append("%s: %s" % (m.type, m.text)) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)
        print("\n[%s] %s" % (key, fn))

        boot = pg.locator("#boot")
        err_txt = pg.evaluate("(document.querySelector('#boot .err')||{}).textContent || ''")
        a(err_txt == "", "场景初始化无失败提示", err_txt[:120])
        a(pg.evaluate("typeof S3D === 'object'"), "S3D 运行时已就绪")
        info = pg.evaluate("""() => {
          const c=document.getElementById('gl');
          let ctx=null; try{ ctx=c.getContext('webgl2')||c.getContext('webgl'); }catch(e){}
          return {three: typeof window.THREE, rev: (window.THREE&&THREE.REVISION)||'?',
                  w:c.width, h:c.height, gl: ctx? (ctx.isContextLost()?'lost':'live') : 'none',
                  objs: S3D.scene ? S3D.scene.children.length : -1,
                  cam: S3D.camera ? S3D.camera.position.toArray().map(v=>+v.toFixed(2)) : null,
                  labels: document.querySelectorAll('#labels .lb').length,
                  rows: document.querySelectorAll('#ro .row').length,
                  ctl: document.querySelectorAll('#ctl input,#ctl button').length};
        }""")
        a(info["three"] == "object", "three.js 就绪", "r%s" % info["rev"])
        a(info["gl"] == "live", "WebGL 上下文可用", info["gl"])
        a(info["w"] > 300 and info["h"] > 300, "画布按视口铺开", "%dx%d" % (info["w"], info["h"]))
        a(info["objs"] > 5, "场景对象已挂载", str(info["objs"]))
        a(info["labels"] >= 3, "三维空间标签已投影", str(info["labels"]))
        a(info["rows"] >= 3, "读数卡有数据行", str(info["rows"]))
        a(info["ctl"] >= 1, "底部控件已生成", str(info["ctl"]))

        if key == "refl":
            a(ro(pg, "i") == "40°" and ro(pg, "r") == "40°", "入射角=反射角=40°", "%s / %s" % (ro(pg, "i"), ro(pg, "r")))
            a(ro(pg, "hit") == "有光斑", "β=0 时 F 板上有光斑", ro(pg, "hit"))
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_refl_beta0.png"))
            pg.evaluate("""() => { const s=document.getElementById('fc-beta'); s.value=60;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(500)
            a(ro(pg, "beta") == "60°", "拖 β 到 60°", ro(pg, "beta"))
            a(ro(pg, "hit") == "看不到光斑", "β=60° 时 F 板上接不到光斑（三线共面的关键证据）", ro(pg, "hit"))
            a(pg.evaluate("S3D.scene.children.length") > 5, "折转后场景仍正常")
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_refl_beta60.png"))
            # 父页参数：i
            pg.evaluate("window.postMessage({t:'s3d:param', name:'i', value:70}, '*')")
            pg.wait_for_timeout(400)
            a(ro(pg, "i") == "70°" and ro(pg, "r") == "70°", "父页改入射角 → 3D 同步为 70°", "%s / %s" % (ro(pg, "i"), ro(pg, "r")))
            # 折转演示
            # 入射角也能在 3D 控制条里调（不必回到 2D）
            a(pg.locator("#fc-i").count() == 1, "3D 控制条里有入射角滑块")
            pg.evaluate("""() => { const s=document.getElementById('fc-i'); s.value=20;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(400)
            a(ro(pg, "i") == "20°" and ro(pg, "r") == "20°", "在 3D 里改入射角 → 读数同步 20°",
              "%s / %s" % (ro(pg, "i"), ro(pg, "r")))
            pg.click("#fc-demo")
            pg.wait_for_timeout(2600)
            beta_mid = float(ro(pg, "beta").replace("°", ""))
            a(beta_mid > 5, "折转演示让 β 自动变化", ro(pg, "beta"))
            pg.click("#fc-demo")
            # 视角工具
            pg.click("#tl-orbit"); pg.wait_for_timeout(900)
            a(pg.get_attribute("#tl-orbit", "aria-pressed") == "true", "自动环绕已开启")
            pg.click("#tl-side"); pg.wait_for_timeout(1200)
            cam = pg.evaluate("S3D.camera.position.toArray().map(v=>+v.toFixed(2))")
            a(abs(cam[2]) > 3 and abs(cam[0]) < 1.2, "正侧视：相机移到近乎正对镜面", str(cam))
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_refl_side.png"))

        if key == "lens":
            pg.screenshot(path=os.path.join(BASE, "_s3d_lens_默认.png"))
            a(ro(pg, "u") == "42.0 cm" and ro(pg, "f") == "11 cm", "初始 u=42 / f=11", "%s / %s" % (ro(pg, "u"), ro(pg, "f")))
            # u=42,f=11 → v=14.86, m=0.354
            a(ro(pg, "v") == "14.9 cm", "像距 v = uf/(u−f) = 14.9 cm", ro(pg, "v"))
            a(ro(pg, "m") == "0.35 倍", "放大率 m = v/u = 0.35", ro(pg, "m"))
            a("缩小" in ro(pg, "nat") and "倒立" in ro(pg, "nat") and "实像" in ro(pg, "nat"),
              "u > 2f：倒立缩小实像", ro(pg, "nat"))
            a(ro(pg, "use") == "照相机", "u > 2f 对应照相机", ro(pg, "use"))
            a(ro(pg, "scr") == "屏上有清晰的像", "光屏上有清晰的像", ro(pg, "scr"))

            def setu(val):
                pg.evaluate("""() => { const s=document.getElementById('fc-x'); }""")
                pg.evaluate("window.postMessage({t:'s3d:param', name:'u', value:%s}, '*')" % val)
                pg.wait_for_timeout(300)

            setu(22)   # u = 2f
            a(ro(pg, "m") == "1.00 倍" and "等大" in ro(pg, "nat"), "u = 2f：等大倒立实像", "%s / %s" % (ro(pg, "m"), ro(pg, "nat")))
            setu(11)   # u = f
            a(ro(pg, "v") == "∞" and "不成像" in ro(pg, "nat"), "u = f：不成像（出射光平行）", "%s / %s" % (ro(pg, "v"), ro(pg, "nat")))
            setu(6)    # u < f → 虚像
            a(ro(pg, "v") == "13.2 cm（虚像侧）", "u < f：像距为负 → 虚像侧 13.2 cm", ro(pg, "v"))
            a(ro(pg, "nat") == "正立 · 放大 · 虚像" and ro(pg, "scr") == "光屏接不到虚像",
              "u < f：正立放大虚像、光屏接不到", "%s / %s" % (ro(pg, "nat"), ro(pg, "scr")))
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_lens_虚像.png"))
            pg.click("#tl-side"); pg.wait_for_timeout(1200)
            setu(30)
            n_before = pg.evaluate("S3D.scene.children.length")
            pg.click("#fc-cone"); pg.wait_for_timeout(400)
            a(pg.get_attribute("#fc-cone", "aria-pressed") == "false", "光锥开关可关闭")
            a(pg.evaluate("S3D.scene.children.length") > 0, "关掉光锥后场景仍正常")
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_lens_无光锥.png"))
            pg.click("#fc-cone"); pg.wait_for_timeout(200)
            u_before = float(ro(pg, "u").replace(" cm", ""))
            pg.click("#fc-play"); pg.wait_for_timeout(1500)
            u2 = float(ro(pg, "u").replace(" cm", ""))
            a(abs(u2 - u_before) > 4, "物距扫描让 u 自动变化", "%s → %s" % (u_before, u2))
            pg.click("#fc-play")
            pg.click("#tl-side"); pg.wait_for_timeout(1400)
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_lens_正侧视.png"))
            a(pg.evaluate("S3D.scene.children.length") >= n_before, "切换过程场景未丢失对象")
            # 立体光锥：取样点必须落在透镜整个圆面上（有 |z|>0 的光线），否则只是个扇面
            nz = pg.evaluate("""() => { let n=0;
                S3D.scene.traverse(o=>{ if(o.isMesh&&o.geometry&&o.geometry.type==='CylinderGeometry'
                  && Math.abs(o.position.z) > 0.05) n++; }); return n; }""")
            a(nz >= 10, "光锥是立体锥（有 z≠0 的光线）而不是同一平面里的扇面", "z≠0 的光束段 %d" % nz)
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_lens_光锥.png"))

        if key == "mirror":
            pg.screenshot(path=os.path.join(BASE, "_s3d_mirror_默认.png"))
            # 棋子左右移动：物 / 像 / B 三者同步平移（像跟着物动）
            pos = lambda: pg.evaluate("""() => { const o=[];
                S3D.scene.traverse(x=>{ if(x.isMesh&&x.geometry&&x.geometry.type==='LatheGeometry')
                  o.push({x:+x.position.x.toFixed(3), z:+x.position.z.toFixed(3)}); }); return o; }""")
            p0 = pos()
            a(len(p0) == 3 and abs(p0[0]["z"]) < 1e-6, "初始：三枚棋子都在 z=0", str(p0))
            pg.evaluate("""() => { const s=document.getElementById('fc-z'); s.value=6;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(400)
            p1 = pos()
            a(all(abs(q["z"] - 0.36) < 0.02 for q in p1), "左右滑块 6cm → 三枚棋子同步移到 z=0.36", str(p1))
            a(abs(p1[0]["x"] + p1[1]["x"]) < 1e-6 and abs(p1[0]["x"] + p1[2]["x"]) < 1e-6,
              "左右移动不改变物像对称关系（物与像、物与 B 的 x 仍互为相反数）", str(p1))
            a(ro(pg, "z") == "6.0 cm", "读数卡显示左右位置", ro(pg, "z"))
            pg.evaluate("""() => { const s=document.getElementById('fc-z'); s.value=0;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }""")
            pg.wait_for_timeout(300)
            a(pg.evaluate("S3D.params.z") == 0, "复位到 z=0")
            if shots:
                pg.screenshot(path=os.path.join(BASE, "_s3d_mirror_左右.png"))

        a(not errs, "控制台无错误", " | ".join(errs[:3]))
        b.close()


if __name__ == "__main__":
    keys = [k for k in sys.argv[1:] if k in SCENES] or list(SCENES)
    shots = "--shots" in sys.argv
    for k in keys:
        run(k, shots)
    print("\n" + "=" * 60)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL: " + f)
    sys.exit(1 if FAIL else 0)
