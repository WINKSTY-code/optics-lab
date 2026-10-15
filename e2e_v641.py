# -*- coding: utf-8 -*-
"""V6.4.1 e2e：凸透镜 3D 物体三维全方向移动
断言真实数值（imgPlane/screenG 位置满足 -m 关系），不只是"有输出"。
用系统 Python 3.12（已装 playwright）。"""
import sys, math, pathlib

# 运行时：系统 Python 3.12（playwright + greenlet 齐全）；勿插入其它解释器的 site-packages
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
HTML = BASE + r"\光学交互实验室_AI_v6.4.1.html"

KY, KX, AY, OBJ_H, LENS_R = 0.19, 0.05, 1.45, 7.0, 1.45
RAIL_R = 2.6

def phys(u, f, oy, oz):
    """按场景实现重算期望状态（白盒基准）"""
    noImg = abs(u - f) < 0.6
    v = u * f / (u - f) if not noImg else float("nan")
    m = v / u
    real = (not noImg) and v > 0
    virt = (not noImg) and v < 0
    over = real and v > RAIL_R / KX
    vShow = min(v, RAIL_R / KX) if real else v
    yTip, zTip, yBase = KY * (OBJ_H + oy), KY * oz, KY * oy
    ih = max(0.08, abs(KY * OBJ_H * m))
    yImgBase = 0 if noImg else -m * yBase
    zImg = 0 if noImg else -m * zTip
    ip = {
        "x": (KX * vShow - 0.04) if real else (KX * v + 0.03),
        "y": (AY + yImgBase - ih / 2) if real else (AY + yImgBase + ih / 2),
        "z": zImg, "vis": (not noImg) and ((not over) or not real),
    }
    if noImg:
        ip["vis"] = False
    # 三条特殊光线出射段的口径判定（c3=true 时③为入射+出射 2 条）
    y3, z3 = yTip * f / (f - u), zTip * f / (f - u)
    c1 = yTip * yTip + zTip * zTip <= LENS_R * LENS_R
    c3 = y3 * y3 + z3 * z3 <= LENS_R * LENS_R
    nray = 1 + (1 if c1 else 0) + 2 + (2 if c3 else 1)   # ①入 ①出 ②入出 ③入(出)
    if virt:
        nray += 1                                          # ②虚线（Line，同在 rayG 组内）
        if c1:
            nray += 1                                      # ①虚线
    return dict(noImg=noImg, real=real, over=over, ip=ip, ih=ih, nray=nray,
                yImgBase=yImgBase, m=m, v=v, c1=c1, c3=c3)

RESULTS = []
def a(cond, msg, extra=""):
    RESULTS.append((bool(cond), msg, extra))
    print(("PASS " if cond else "FAIL ") + msg + (("  | " + str(extra)) if (extra and not cond) else ""))

JS_IP = """(() => {
  const ip = S3D.scene.children.find(o => o.isMesh && o.geometry && o.geometry.type === 'PlaneGeometry');
  return ip ? {x: ip.position.x, y: ip.position.y, z: ip.position.z, vis: ip.visible} : null;
})()"""
JS_SG = """(() => {
  const sg = S3D.scene.children.find(o => o.isGroup && o.children.some(c => c.isMesh && c.geometry && c.geometry.type === 'PlaneGeometry'));
  return sg ? {x: sg.position.x, y: sg.position.y, z: sg.position.z, vis: sg.visible} : null;
})()"""
JS_RAY = """(() => {
  const gs = S3D.scene.children.filter(o => o.isGroup && Math.abs(o.position.y - 1.45) < 0.02
    && o.children.length >= 3 && o.children.some(c => c.userData && c.userData.s3dBeam));
  return gs.map(g => g.children.length);
})()"""
JS_SET = """([name, val]) => {
  const el = document.getElementById('fc-' + name);
  if (!el) return false;
  el.value = val;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  return true;
}"""
JS_RO = "(k) => { const e = document.getElementById('ro-' + k); return e ? e.querySelector('b').textContent : null; }"

def near(x, y, tol=1e-6):
    return abs(x - y) <= tol

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(pathlib.Path(HTML).resolve().as_uri(), wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelectorAll('.modal-mask').forEach(e => e.classList.remove('show'))")
    pg.evaluate("document.querySelectorAll('.modal-mask').forEach(e => e.style.display = '')")

    # ---- A1 页面健康 ----
    a(pg.evaluate("(window.__rbErrors||[]).length") == 0, "A1 看门狗 __rbErrors 为空",
      pg.evaluate("(window.__rbErrors||[]).map(e=>e.kind+': '+String(e.detail).slice(0,90))"))
    a(pg.evaluate("document.querySelector('.ver-badge').textContent") == "v6.4.1", "A1 版本角标 v6.4.1")

    # ---- A2 更新日志精简（日志 DOM 恒在文档中，直接只读，不碰弹窗显隐） ----
    logs = pg.evaluate("""[...document.querySelectorAll('#logMask .log-item')].slice(0,13).map(it => ({
      v: it.querySelector('.log-ver').textContent,
      t: it.querySelector('p').textContent.trim(),
      cur: it.classList.contains('cur')}))""")
    a(logs[0]["v"] == "V6.4.1" and logs[0]["cur"] and logs[0]["t"] == "凸透镜3D实验实现物体三维全方向移动",
      "A2 首条 V6.4.1（用户指定文案）", logs[0])
    a(len(logs) == 13 and all(len(l["t"]) <= 30 for l in logs), "A2 前 13 条日志均 ≤30 字",
      [(l["v"], len(l["t"])) for l in logs])
    a(logs[1]["v"] == "V6.4.0" and logs[-1]["v"] == "V5.1.0", "A2 精简范围 V5.1.0~V6.4.0", [l["v"] for l in logs])

    # ---- 进入凸透镜 3D（按容器取 iframe）----
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(300)
    pg.click('.s3d-bar[data-s3d="lens"] button[data-m="3d"]')
    pg.wait_for_timeout(2200)
    el = pg.query_selector('.s3d-frame[data-s3d="lens"] .s3d-ifr')
    a(el is not None, "3D 框与 iframe 存在")
    fr = el.content_frame()
    a(fr.evaluate("!!window.S3D && !!S3D.scene"), "3D 场景已挂载")
    a(fr.evaluate("!!document.getElementById('fc-oy') && !!document.getElementById('fc-oz')"), "A3 新滑块 fc-oy / fc-oz 存在")
    a(fr.evaluate("S3D.params.oy") == 0 and fr.evaluate("S3D.params.oz") == 0, "A3 oy/oz 初始为 0")

    def snap():
        return dict(ip=fr.evaluate(JS_IP), sg=fr.evaluate(JS_SG), ray=fr.evaluate(JS_RAY),
                    off=fr.evaluate(JS_RO, "off"), scr=fr.evaluate(JS_RO, "scr"),
                    nat=fr.evaluate(JS_RO, "nat"), oy=fr.evaluate("S3D.params.oy"),
                    oz=fr.evaluate("S3D.params.oz"), u=fr.evaluate("S3D.params.u"))

    def expect_state(st, ph, tag, check_ray=True):
        ip, exp = st["ip"], ph["ip"]
        if ip["vis"]:
            # 场景固有行为：imgPlane 不可见时位置保持上一帧陈旧值（旧版同样），仅在可见时断言
            a(near(ip["x"], exp["x"]) and near(ip["y"], exp["y"]) and near(ip["z"], exp["z"]),
              tag + " imgPlane 位置满足 -m 白盒期望", (ip, exp))
        a(ip["vis"] == exp["vis"], tag + " imgPlane 可见性", (ip["vis"], exp["vis"]))
        sg = st["sg"]
        a(sg is not None and near(sg["z"], (-ph["m"] * KY * st["oz"]) if ph["real"] else 0.0) and near(sg["x"], KX * (min(ph["v"], RAIL_R / KX) if ph["real"] else RAIL_R / KX)),
          tag + " 光屏位置（z 跟随像侧移）", (sg, ph["m"]))
        a(sg["vis"] == ph["real"], tag + " 光屏可见性 = 是否实像", (sg["vis"], ph["real"]))
        if check_ray:
            a(st["ray"] and st["ray"][1] == ph["nray"], tag + " 三条特殊光线段数 = %d" % ph["nray"],
              (st["ray"], ph["nray"]))

    # ---- A4 默认退化（oy=oz=0 与旧版一致）----
    ph = phys(42, 11, 0, 0)
    st = snap()
    a(st["off"] == "在光轴上", "A4 读数 off=在光轴上", st["off"])
    a(st["scr"] == "屏上有清晰的像", "A4 读数 scr", st["scr"])
    expect_state(st, ph, "A4 默认态")

    # ---- A5 oy=+3, oz=+2：实像反向移动 ----
    fr.evaluate(JS_SET, ["oy", 3]); fr.evaluate(JS_SET, ["oz", 2])
    pg.wait_for_timeout(250)
    st = snap()
    a(st["oy"] == 3 and st["oz"] == 2, "A5 params 已生效", (st["oy"], st["oz"]))
    a(st["off"] == "上+3.0 · 侧+2.0 cm", "A5 读数 off 文本", st["off"])
    ph = phys(42, 11, 3, 2)
    expect_state(st, ph, "A5 偏移态")
    a(st["scr"] == "屏上有清晰的像", "A5 偏移不大时屏仍有像", st["scr"])
    pg.screenshot(path=BASE + r"\_e641_偏移态.png")

    # ---- A6 u=15, oy=+4, oz=+4：放大实像（v=41.25 在导轨内）+ 超口径截断 + 超屏提示 ----
    fr.evaluate(JS_SET, ["u", 15]); fr.evaluate(JS_SET, ["oy", 4]); fr.evaluate(JS_SET, ["oz", 4])
    pg.wait_for_timeout(250)
    ph = phys(15, 11, 4, 4)
    st = snap()
    a(not ph["over"], "A6 基准 v=41.25 未超导轨", ph["v"])
    expect_state(st, ph, "A6 放大实像")
    a(st["scr"] == "像超出光屏（屏太小）", "A6 超屏提示", st["scr"])
    a(not ph["c1"] and not ph["c3"], "A6 口径判定（①③出射均超口径）", (ph["c1"], ph["c3"]))
    fr.evaluate(JS_SET, ["u", 42]); fr.evaluate(JS_SET, ["oy", 0]); fr.evaluate(JS_SET, ["oz", 0])
    pg.wait_for_timeout(250)

    # ---- A7 虚像：u=8, oy=+2, oz=-2 ----
    fr.evaluate(JS_SET, ["u", 8]); fr.evaluate(JS_SET, ["oy", 2]); fr.evaluate(JS_SET, ["oz", -2])
    pg.wait_for_timeout(250)
    ph = phys(8, 11, 2, -2)
    st = snap()
    a(not ph["real"] and ph["v"] < 0, "A7 基准为虚像", ph["v"])
    expect_state(st, ph, "A7 虚像")
    a(st["scr"] == "光屏接不到虚像", "A7 scr 提示", st["scr"])
    a(st["nat"] == "正立 · 放大 · 虚像", "A7 像的性质不因离轴改变", st["nat"])
    fr.evaluate(JS_SET, ["u", 42]); fr.evaluate(JS_SET, ["oy", 0]); fr.evaluate(JS_SET, ["oz", 0])
    pg.wait_for_timeout(250)

    # ---- A8 场景内重置 ----
    fr.click("#tl-reset")
    pg.wait_for_timeout(300)
    st = snap()
    a(st["u"] == 42 and st["oy"] == 0 and st["oz"] == 0, "A8 重置后 u/oy/oz 归零", (st["u"], st["oy"], st["oz"]))
    ph = phys(42, 11, 0, 0)
    expect_state(st, ph, "A8 重置态", check_ray=False)

    # ---- A9 回写链路与白名单：3D 里拖 u → 父页滑块同步；oy/oz 不污染父页 ----
    fr.evaluate(JS_SET, ["u", 30])
    pg.wait_for_timeout(400)
    a(pg.evaluate("document.querySelector('#lens-uSlider').value") == "30", "A9 3D 拖 u 回写父页滑块",
      pg.evaluate("document.querySelector('#lens-uSlider').value"))
    fr.evaluate(JS_SET, ["u", 42])
    pg.wait_for_timeout(300)

    # ---- A10 回归：另一场景 3D 挂载 + 互斥回收 ----
    pg.click('.tab-btn[data-tab="mirror"]')
    pg.wait_for_timeout(300)
    pg.click('.s3d-bar[data-s3d="mirror"] button[data-m="3d"]')
    pg.wait_for_timeout(2200)
    mel = pg.query_selector('.s3d-frame[data-s3d="mirror"] .s3d-ifr')
    mfr = mel.content_frame() if mel else None
    a(mfr is not None and mfr.evaluate("!!window.S3D"), "A10 平面镜 3D 仍正常挂载")
    a(pg.evaluate("!!document.querySelector('.s3d-frame[data-s3d=\"lens\"] .s3d-ifr')"), "A10 lens 3D 框节点仍在")

    # ---- 噪声过滤后的控制台错误 ----
    real_errs = [e for e in errs if "favicon" not in e and "Failed to load resource" not in e
                 and "net::ERR_FAILED" not in e and "ERR_BLOCKED" not in e]
    a(len(real_errs) == 0, "控制台无真实错误", real_errs[:4])

    # ---- 截图 ----
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(300)
    pg.click('.s3d-bar[data-s3d="lens"] button[data-m="3d"]')
    pg.wait_for_timeout(2200)
    fr2 = pg.query_selector('.s3d-frame[data-s3d="lens"] .s3d-ifr').content_frame()
    fr2.evaluate(JS_SET, ["oy", 3]); fr2.evaluate(JS_SET, ["oz", 2])
    pg.wait_for_timeout(500)
    pg.screenshot(path=BASE + r"\_e641_默认复检.png")
    b.close()

fails = [r for r in RESULTS if not r[0]]
print("\n=== 结果: %d 项，失败 %d ===" % (len(RESULTS), len(fails)))
sys.exit(1 if fails else 0)
