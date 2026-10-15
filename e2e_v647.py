# -*- coding: utf-8 -*-
"""
V6.4.7 端到端验证（真实 Chromium，file:// 协议）—— 在 V6.4.6 全部用例上叠加：
  ⑥ 3D 凸透镜：可移动透镜（上下 / 左右）+ 底栏「一行三个」
覆盖：① 设置下拉（能开能关 / 不被 .topbar-right 裁剪 / 五个入口原样保留 / 四个功能不变）
      ② 小孔成像 2D 新增物距：可调（像高比真值）+ 可扫描（帧推进）+ 进数据表
      ③ 回归：tab·画布·面板基线、影子模式分组不变、3D 案例仍在
      ④ 跨模块不干扰：走自己的入口不动作品自带的全屏
      ⑤ 顶栏在 8 档视口宽度下「设置」按钮都在视口内
      ⑥ 3D 凸透镜场景（iframe 内）：底栏 3×3、透镜滑杆可用、透镜与像真的移动了
"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.7.html").as_uri()
FAILS = []


def ck(cond, msg, extra=""):
    print("%s %s%s" % ("  OK  " if cond else "  FAIL", msg, ("  " + str(extra)) if extra else ""))
    if not cond:
        FAILS.append(msg)


# ---- 子文档（3D 场景 iframe）里用的探针 ----
GRID_JS = """() => {
  const bad = [], b = document.getElementById('ctlBody'), c = document.getElementById('ctl');
  if (!b || !c) return {bad:['no #ctlBody'], n:0, rows:0, cols:''};
  const r = c.getBoundingClientRect();
  if (r.left < -1 || r.right > window.innerWidth + 1) bad.push('ctl 越界');
  if (r.bottom > window.innerHeight + 1) bad.push('ctl 底越界');
  if (r.height > window.innerHeight * 0.6) bad.push('ctl 过高 ' + r.height);
  if (b.scrollWidth > b.clientWidth + 2) bad.push('ctlBody 横向溢出 ' + b.scrollWidth + '>' + b.clientWidth);
  [...b.children].forEach((el, i) => {
    const q = el.getBoundingClientRect();
    if (!q.width) return;
    if (q.right > window.innerWidth + 1 || q.left < -1) bad.push('控件' + i + ' 越界');
    if (q.width < 38) bad.push('控件' + i + ' 过窄 ' + q.width.toFixed(0));
  });
  const tops = [...b.children].map(e => e.getBoundingClientRect().top).sort((x, y) => x - y);
  let rows = 0, cur = -1e9;
  tops.forEach(t => { if (t - cur > 12) { rows++; cur = t; } });
  return {bad: bad, n: b.children.length, rows: rows, disp: getComputedStyle(b).display,
          cols: getComputedStyle(b).gridTemplateColumns};
}"""

LB_JS = """(t) => {
  const els = [...document.querySelectorAll('#labels .lb')];
  const el = els.find(e => e.textContent.trim() === t);
  if (!el || getComputedStyle(el).display === 'none') return null;
  const r = el.getBoundingClientRect();
  return {x: +r.x.toFixed(2), y: +r.y.toFixed(2)};
}"""

SET_JS = """(a) => {
  const s = document.getElementById('fc-' + a[0]);
  if (!s) return 'no-el';
  s.value = String(a[1]);
  s.dispatchEvent(new Event('input', {bubbles: true}));
  return s.value;
}"""


def clear_masks(pg):
    """清遮罩。

    坑：#aiCfgMask 是 showModal() 动态创建的 **id**（不是类），且 .modal-mask 不在任何
    通用类名里；且退场态 .is-closing 是 display:flex !important，必须一起摘。
    """
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show');
        m.classList.remove('is-closing');
      });
    }""")


def dismiss_first_run(pg):
    """全新 profile → 加载后 400ms 弹「学生姓名」窗（复用 #aiCfgMask）。走真实流程填完它。"""
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试")
        pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd")          # 内部 alert()，Playwright 默认自动 dismiss
        pg.wait_for_timeout(700)
    clear_masks(pg)


def click(pg, sel, **kw):
    clear_masks(pg)
    kw.setdefault("timeout", 8000)
    pg.click(sel, **kw)
    pg.wait_for_timeout(160)


def menu_geo(pg):
    """菜单几何 + 是否被祖先裁剪（getBoundingClientRect 不受裁剪影响，
    唯一可靠判据是 elementFromPoint 打中的是不是菜单自己）。"""
    return pg.evaluate("""() => {
      const m = document.getElementById('setMenu');
      const r = m.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
      return {
        hidden: m.hidden, w: r.width, h: r.height,
        left: r.left, right: r.right, top: r.top, bottom: r.bottom,
        vw: window.innerWidth, vh: window.innerHeight,
        hitInside: !!(hit && m.contains(hit)),
        hitEl: hit ? (hit.id || hit.className || hit.tagName) : null
      };
    }""")


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                    "--enable-unsafe-swiftshader"])
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        dismiss_first_run(pg)

        # ================================================== 0 启动健康
        print("\n== 0 启动健康 ==")
        ck(pg.evaluate("!document.getElementById('__rbOverlay')"), "启动失败浮层不存在")
        ck(pg.evaluate("window.__APP_READY === true"), "__APP_READY 已置真")
        ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本为空",
           pg.evaluate("(window.__rbErrors||[]).length"))
        ck(pg.evaluate("document.querySelector('.ver-badge').textContent.trim()") == "v6.4.7",
           "版本角标为 v6.4.7")

        # ================================================== 1 设置下拉结构
        print("\n== 1 设置下拉：结构与位置 ==")
        ck(pg.evaluate("document.getElementById('setWrap').closest('.topbar-right') === null"),
           "设置下拉挂在 .topbar-right 之外（不会被滚动容器裁掉）")
        ck(pg.evaluate("document.getElementById('setWrap').parentNode.classList.contains('topbar')"),
           "设置下拉是 .topbar 的直接子元素")
        ck(pg.evaluate("document.querySelectorAll('.topbar-right #aiCfgBtn').length === 0"),
           "AI 设置按钮已不在 .topbar-right 内")
        ck(pg.evaluate("document.querySelectorAll('.set-menu #aiCfgBtn,.set-menu #zoomOut,"
                       ".set-menu #zoomIn,.set-menu #langBtn,.set-menu #themeBtn').length === 5"),
           "下拉内五个入口 id 原样保留")
        ck(pg.evaluate("document.getElementById('setWrap').children.length === 2"),
           "设置容器内只有「设置按钮 + 菜单」两层")
        # 注入的两个按钮组必须仍在 topbar-right 里（锚点改对了）
        ck(pg.evaluate("!!document.querySelector('.topbar-right #studentBtn')"),
           "学生按钮仍在顶栏（没掉进下拉）")
        ck(pg.evaluate("!!document.querySelector('.topbar-right #topTts') && "
                       "!!document.querySelector('.topbar-right #topChat') && "
                       "!!document.querySelector('.topbar-right #topDiag')"),
           "朗读/问AI/诊断三个按钮仍在顶栏（没掉进下拉）")
        ck(pg.evaluate("document.getElementById('topTts').closest('.set-menu') === null"),
           "AI 按钮组不在下拉菜单内")

        g0 = menu_geo(pg)
        ck(g0["hidden"], "初始为收起态")
        ck(pg.get_attribute("#setBtn", "aria-expanded") == "false", "aria-expanded=false")
        ck(pg.inner_text("#setBtn").strip() == "设置", "设置按钮文案为「设置」")

        # ================================================== 2 开合
        print("\n== 2 设置下拉：开合 ==")
        click(pg, "#setBtn")
        g1 = menu_geo(pg)
        ck(not g1["hidden"], "点击后展开")
        ck(pg.get_attribute("#setBtn", "aria-expanded") == "true", "aria-expanded=true")
        ck(g1["w"] > 60 and g1["h"] > 80, "菜单有真实尺寸", "%dx%d" % (g1["w"], g1["h"]))
        ck(g1["hitInside"], "★ 菜单中心点打中的是菜单自己（未被祖先裁剪）", g1["hitEl"])
        ck(g1["bottom"] <= g1["vh"], "菜单未超出视口底部", "bottom=%.0f vh=%.0f" % (g1["bottom"], g1["vh"]))
        ck(g1["left"] >= 0 and g1["right"] <= g1["vw"], "菜单左右都在视口内",
           "left=%.0f right=%.0f vw=%.0f" % (g1["left"], g1["right"], g1["vw"]))
        for sel, name in [("#aiCfgBtn", "AI 设置"), ("#zoomOut", "A−"), ("#zoomIn", "A＋"),
                          ("#langBtn", "语言"), ("#themeBtn", "背景色")]:
            ck(pg.is_visible(sel), "展开后 %s 按钮可见" % name)
        ck(pg.evaluate("""() => {
              const r = document.getElementById('setBtn').getBoundingClientRect();
              return r.top >= 0 && r.bottom <= window.innerHeight;
            }"""), "设置按钮在视口内")

        click(pg, ".title")                       # 点外部
        ck(menu_geo(pg)["hidden"], "点击外部关闭")
        click(pg, "#setBtn")
        ck(not menu_geo(pg)["hidden"], "再次点击展开")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(160)
        ck(menu_geo(pg)["hidden"], "Esc 关闭")

        # ================================================== 3 四个功能不变
        print("\n== 3 四个入口功能不变 ==")
        click(pg, "#setBtn")
        # --- 3.1 背景色
        t0 = pg.inner_text("#themeBtn").strip()
        dark0 = pg.evaluate("document.body.classList.contains('light')")
        click(pg, "#themeBtn")
        t1 = pg.inner_text("#themeBtn").strip()
        dark1 = pg.evaluate("document.body.classList.contains('light')")
        ck(dark1 != dark0, "背景色：body.light 状态翻转", "%s → %s" % (dark0, dark1))
        ck(t1 != t0, "背景色：按钮文案随主题切换", "%s → %s" % (t0, t1))
        click(pg, "#themeBtn")
        ck(pg.evaluate("document.body.classList.contains('light')") == dark0, "背景色：可切回")
        ck(not menu_geo(pg)["hidden"], "点背景色后菜单保持展开（便于连点）")

        # --- 3.2 字号
        ck(pg.inner_text("#zoomIn").strip() == "A＋", "字号：初始 A＋ 无百分比",
           pg.inner_text("#zoomIn").strip())
        click(pg, "#zoomIn")
        ck(pg.evaluate("document.body.style.zoom") == "1.1", "字号：A＋ → body.zoom=1.1",
           pg.evaluate("document.body.style.zoom"))
        ck(pg.inner_text("#zoomIn").strip() == "A＋ 110%", "字号：A＋ 文案带百分比",
           pg.inner_text("#zoomIn").strip())
        click(pg, "#zoomOut")
        ck(pg.evaluate("document.body.style.zoom") == "1", "字号：A− 回到 1.0")
        ck(pg.inner_text("#zoomOut").strip() == "A−" and pg.inner_text("#zoomIn").strip() == "A＋",
           "字号：回到 100% 时两个按钮都不带百分比")
        click(pg, "#zoomOut")
        ck(pg.evaluate("document.body.style.zoom") == "0.9", "字号：A− → body.zoom=0.9")
        ck(pg.inner_text("#zoomOut").strip() == "A− 90%", "字号：A− 文案带百分比")
        click(pg, "#zoomIn")
        ck(pg.evaluate("document.body.style.zoom") == "1", "字号：恢复 100%")

        # --- 3.3 语言（读 LANG 循环点，别写死次数）
        lb0 = pg.inner_text("#langBtn").strip()
        click(pg, "#langBtn")
        lb1 = pg.inner_text("#langBtn").strip()
        ck(lb1 != lb0, "语言：按钮文案变化", "%s → %s" % (lb0, lb1))
        ck(pg.inner_text("#setBtn").strip() != "设置",
           "语言：设置按钮文案跟随切换", pg.inner_text("#setBtn").strip())
        ck(pg.evaluate("document.documentElement.lang") in ("en", "zh-Hant"),
           "语言：<html lang> 同步", pg.evaluate("document.documentElement.lang"))
        for _ in range(5):
            if pg.inner_text("#langBtn").strip() == "中文":
                break
            click(pg, "#langBtn")
        ck(pg.inner_text("#langBtn").strip() == "中文", "语言：可循环回简体中文")
        ck(pg.evaluate("document.documentElement.lang") == "zh-Hans", "语言：<html lang> 回到 zh-Hans")
        ck(pg.inner_text("#setBtn").strip() == "设置", "语言：设置按钮文案回到「设置」")

        # --- 3.4 AI 设置
        click(pg, "#aiCfgBtn")
        ck(pg.evaluate("!!document.getElementById('aiCfgMask') && "
                       "document.getElementById('aiCfgMask').classList.contains('show')"),
           "AI 设置：配置弹窗打开")
        ck(menu_geo(pg)["hidden"], "AI 设置：打开弹窗后菜单自动收起")
        ck(pg.is_visible("#aiCfgMask .modal"), "AI 设置：弹窗内容可见")
        ck(pg.query_selector("#aiCfgSave") is not None, "AI 设置：保存按钮在弹窗内")
        clear_masks(pg)
        pg.wait_for_timeout(200)

        # ================================================== 4 小孔成像物距
        print("\n== 4 小孔成像 2D：新增物距调节 + 扫描 ==")
        click(pg, '.tab-btn[data-tab="line"]')
        # 影子形成：物距 + 物体位置（新加的模式匹配不能把原有分组弄坏）
        ck(pg.is_visible("#line-uSlider"), "影子形成：物距仍可见")
        ck(pg.is_visible("#line-objSlider"), "影子形成：物体位置仍可见")
        ck(not pg.is_visible("#line-vSlider"), "影子形成：像距仍隐藏")
        ck(not pg.is_visible("#line-holeSlider"), "影子形成：孔大小仍隐藏")

        click(pg, '#line-mode [data-m="pinhole"]')
        ck(pg.is_visible("#line-uSlider"), "★ 小孔成像：新增的物距滑块可见")
        ck(pg.is_visible("#line-uPlay"), "★ 小孔成像：新增的物距扫描按钮可见")
        ck(pg.is_visible("#line-vSlider"), "小孔成像：像距仍可见")
        ck(pg.is_visible("#line-holeSlider"), "小孔成像：孔大小仍可见")
        ck(not pg.is_visible("#line-objSlider"), "小孔成像：物体位置（影子专属）仍隐藏")

        # 物距 = 30 → 像高比 v/u = 1.00
        pg.evaluate("""() => {
          const s = document.getElementById('line-uSlider');
          s.value = 30; s.dispatchEvent(new Event('input'));
        }""")
        pg.wait_for_timeout(200)
        v30 = pg.inner_text("#verdict-line")
        ck("1.00" in v30, "物距 30 时结论卡像高比 = 1.00", v30.replace("\n", " ")[:70])
        ck(pg.inner_text("#line-uVal").strip() == "30.0", "物距读数联动", pg.inner_text("#line-uVal"))

        # 物距 = 15 → 像高比 v/u = 2.00（真数值断言，不是"有输出"）
        pg.evaluate("""() => {
          const s = document.getElementById('line-uSlider');
          s.value = 15; s.dispatchEvent(new Event('input'));
        }""")
        pg.wait_for_timeout(200)
        v15 = pg.inner_text("#verdict-line")
        ck("2.00" in v15, "★ 物距改 15 后结论卡像高比 = 2.00（真数值）", v15.replace("\n", " ")[:70])
        ck("1.00" not in v15, "旧值 1.00 已不再出现")
        ck(pg.evaluate("document.getElementById('line-uSlider').value") == "15",
           "滑块 DOM 值 = 15（白盒）")

        # 物距扫描
        click(pg, "#line-uPlay")
        ck("playing" in (pg.get_attribute("#line-uPlay", "class") or ""), "物距扫描：进入播放态")
        ck(pg.inner_text("#line-uPlay").strip() != "", "物距扫描：按钮文案切换",
           pg.inner_text("#line-uPlay").strip())
        pg.wait_for_timeout(900)
        scan_val = float(pg.evaluate("document.getElementById('line-uSlider').value"))
        ck(scan_val > 15.0, "★ 物距扫描：滑块被真实推进", "15 → %.1f" % scan_val)
        ck("2.00" not in pg.inner_text("#verdict-line"), "物距扫描：结论卡跟随刷新")
        click(pg, "#line-uPlay")
        ck("playing" not in (pg.get_attribute("#line-uPlay", "class") or ""), "物距扫描：可停下")

        # 回到 15 并进数据表
        pg.evaluate("""() => {
          const s = document.getElementById('line-uSlider');
          s.value = 15; s.dispatchEvent(new Event('input'));
        }""")
        pg.wait_for_timeout(1600)                      # 让自动记录的 debounce 先落定
        pg.evaluate("document.getElementById('line-recAuto').checked = false")
        n0 = pg.evaluate("document.querySelectorAll('#line-dataBody tr').length")
        click(pg, "#line-recBtn")
        pg.wait_for_timeout(250)
        n1 = pg.evaluate("document.querySelectorAll('#line-dataBody tr').length")
        ck(n1 == n0 + 1, "手动记录：行数 +1", "%d → %d" % (n0, n1))
        row = pg.evaluate("""() => {
          const tr = document.querySelectorAll('#line-dataBody tr');
          return Array.from(tr[tr.length - 1].children).map(td => td.textContent.trim());
        }""")
        print("     末行 =", row)
        ck(len(row) == 6 and row[1] == "小孔成像", "末行：模式列 = 小孔成像", row)
        ck(row[2] == "15.0", "★ 末行：u/cm 列记录了新物距 15.0", row[2])
        ck(row[3] == "30.0", "末行：v/cm 列 = 30.0", row[3])
        ck("2.00" in row[5], "末行：像高比 v/u = 2.00", row[5])

        # ================================================== 5 回归
        print("\n== 5 回归：既有能力仍在 ==")
        ck(pg.evaluate("document.querySelectorAll('.tab-btn').length") == 11, "11 个 tab 按钮",
           pg.evaluate("document.querySelectorAll('.tab-btn').length"))
        ck(pg.evaluate("document.querySelectorAll('canvas').length") == 11, "11 个画布",
           pg.evaluate("document.querySelectorAll('canvas').length"))
        ck(pg.evaluate("document.querySelectorAll('.panel').length") == 12, "12 个面板",
           pg.evaluate("document.querySelectorAll('.panel').length"))
        ck(pg.evaluate("typeof MODULES === 'object' && typeof REPORT === 'object' && "
                       "typeof S3D === 'object'"), "MODULES / REPORT / S3D 俱在")
        click(pg, '.tab-btn[data-tab="pinhole"]') if False else None
        click(pg, '#line-mode [data-m="shadow"]')
        ck(pg.is_visible("#line-uSlider") and pg.is_visible("#line-objSlider"),
           "切回影子形成：分组恢复正常")
        ck(not pg.is_visible("#line-vSlider"), "切回影子形成：像距重新隐藏")
        ck(pg.is_visible('.s3d-bar[data-s3d="shadow"]'), "影子形成：3D案例切换条仍在")
        click(pg, '#line-mode [data-m="pinhole"]')
        ck(pg.is_visible('.s3d-bar[data-s3d="pinhole"]'), "小孔成像：3D案例切换条仍在")
        ck(not pg.is_visible('.s3d-bar[data-s3d="shadow"]'), "小孔成像：影子切换条已收起")
        ok_tabs = pg.evaluate("""() => {
          const names = ['reflect','mirror','lens','refract','line','disperse',
                         'lensfx','eye','instr','combo','judge'];
          return names.every(function(n){
            const p = document.getElementById('tab-' + n);
            if (!p) return false;
            return !!p.querySelector('canvas') || n === 'judge';
          });
        }""")
        ck(ok_tabs, "11 个实验页各有画布接口")

        # ================================================== 6 跨模块不干扰
        print("\n== 6 跨模块不干扰（自己的入口不动别人的全屏）==")
        clear_masks(pg)
        pg.click("#fsBtn")
        pg.wait_for_timeout(300)
        ck(pg.evaluate("document.fullscreenElement === document.documentElement"),
           "作品自带全屏按钮生效")
        click(pg, "#setBtn")
        pg.wait_for_timeout(200)
        ck(pg.evaluate("document.fullscreenElement === document.documentElement"),
           "★ 打开设置下拉后，作品自带的全屏仍在")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(200)
        if pg.evaluate("!!document.fullscreenElement"):
            pg.click("#fsBtn")
            pg.wait_for_timeout(300)
        ck(not pg.evaluate("!!document.fullscreenElement"), "退出全屏")

        # ================================================== 7 视口宽度复扫
        print("\n== 7 顶栏在 6 档视口下：设置按钮与展开菜单都在视口内 ==")
        for w in (1440, 1280, 1100, 900, 700, 560, 390, 360):
            pg.set_viewport_size({"width": w, "height": 900})
            pg.wait_for_timeout(350)
            # 先收起，点开，再量菜单真实边界
            if not menu_geo(pg)["hidden"]:
                click(pg, "#setBtn")
            click(pg, "#setBtn")
            g = menu_geo(pg)
            ck(not g["hidden"], "视口 %dpx：菜单能打开" % w)
            btn = pg.evaluate("""() => {
              const b = document.getElementById('setBtn').getBoundingClientRect();
              const tr = document.querySelector('.topbar-right').getBoundingClientRect();
              return { l: b.left, r: b.right, w: b.width,
                       vb: document.documentElement.scrollWidth - window.innerWidth,
                       mode: document.documentElement.dataset.mode };
            }""")
            ck(btn["w"] > 0 and btn["l"] >= 0 and btn["r"] <= w,
               "视口 %dpx：设置按钮完整在视口内（%s）" % (w, btn["mode"]),
               "left=%.0f right=%.0f" % (btn["l"], btn["r"]))
            ck(g["w"] > 0 and g["left"] >= 0 and g["right"] <= w,
               "★ 视口 %dpx：展开菜单完整在视口内" % w,
               "left=%.0f right=%.0f vw=%d" % (g["left"], g["right"], w))
            ck(g["bottom"] <= 900, "视口 %dpx：菜单未超出底部" % w, "bottom=%.0f" % g["bottom"])
            ck(g["hitInside"], "视口 %dpx：菜单未被裁剪" % w, g["hitEl"])
            ck(btn["vb"] <= 1, "视口 %dpx：页面无横向溢出" % w, "overflow=%d" % btn["vb"])
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(120)
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(300)

        # 收起态下再确认一次菜单能被打开（避免宽度复扫留下副作用）
        click(pg, "#setBtn")
        ck(not menu_geo(pg)["hidden"], "复扫后设置下拉仍可正常打开")
        pg.keyboard.press("Escape")

        # ================================================== 7.6 V6.4.7 · 3D 凸透镜
        print("\n== 7.6 V6.4.7：3D 凸透镜可移透镜 + 底栏一行三个 ==")
        clear_masks(pg)
        click(pg, '.tab-btn[data-tab="lens"]')
        pg.wait_for_timeout(500)
        ck(pg.is_visible('.s3d-bar[data-s3d="lens"]'), "透镜页 2D/3D 切换条可见")
        click(pg, '.s3d-bar[data-s3d="lens"] .s3d-b[data-m="3d"]')
        pg.wait_for_timeout(700)
        ck(pg.evaluate("!!(window.S3D && S3D.isOn('lens'))"), "已切到 3D 态")
        ck(pg.is_visible('.s3d-frame[data-s3d="lens"]'), "3D 容器可见")
        fe = pg.query_selector('.s3d-frame[data-s3d="lens"] iframe.s3d-ifr')
        ck(fe is not None, "3D 场景 iframe 已挂载（懒注入 srcdoc）")
        fr = fe.content_frame() if fe else None
        ck(fr is not None, "可进入子文档（跨文档只有 Playwright 能读）")

        if fr:
            fr.wait_for_function(
                "()=>{var b=document.getElementById('boot');"
                "return !!b && (b.style.display==='none'||b.classList.contains('done'));}",
                timeout=60000)
            pg.wait_for_timeout(900)

            # --- 底栏布局：一行三个
            g = fr.evaluate(GRID_JS)
            ck(g["disp"] == "grid", "底栏 #ctlBody 为 grid", g["disp"])
            ck(g["n"] == 9, "底栏 9 个控件（6 滑杆 + 2 开关 + 1 扫描）", g["n"])
            ck(len(str(g["cols"]).split(" ")) == 3, "★ 一行放三个（三列栅格）", g["cols"])
            ck(g["rows"] == 3, "★ 排成 3 行（不再竖直堆叠）", g["rows"])
            ck(not g["bad"], "控件无越界 / 无横向溢出", g["bad"])

            labs = fr.evaluate("()=>[...document.querySelectorAll('#ctlBody > .f > span')].map(e=>e.textContent)")
            ck(labs == ["物距 u", "焦距 f", "物体上下", "物体左右", "透镜上下", "透镜左右"],
               "★ 六个滑杆标签与顺序（新增透镜上下/左右）", labs)
            ck(fr.evaluate("()=>!!document.getElementById('fc-ly') && !!document.getElementById('fc-lz')"),
               "透镜上下 / 左右滑杆存在")
            ck(fr.evaluate("()=>!!document.getElementById('fc-play')"), "▶ 物距扫描按钮仍在")

            # --- 物理正确性（正侧视，u=42 f=11 → m≈0.355）
            fr.click("#tl-side")
            pg.wait_for_timeout(1800)
            L0 = fr.evaluate(LB_JS, "凸透镜")
            I0 = fr.evaluate(LB_JS, "实像")
            ck(L0 and I0, "子场景 3D 标签可取到", (L0, I0))
            fr.evaluate(SET_JS, ["ly", 3])
            pg.wait_for_timeout(420)
            ck(fr.inner_text("#fv-ly").strip().startswith("3.0"), "透镜上下读数 = 3.0 cm",
               fr.inner_text("#fv-ly").strip())
            ck("上+3.0" in fr.inner_text("#ro-loff"), "读数卡「透镜偏移」联动",
               fr.inner_text("#ro-loff").replace("\n", " "))
            ck("上-3.0" in fr.inner_text("#ro-off"), "★ 物相对光轴变成 上-3.0（读数改为相对透镜光轴）",
               fr.inner_text("#ro-off").replace("\n", " "))
            L1 = fr.evaluate(LB_JS, "凸透镜")
            I1 = fr.evaluate(LB_JS, "实像")
            dL, dI = L0["y"] - L1["y"], I0["y"] - I1["y"]
            print("     透镜位移 %.1fpx | 像位移 %.1fpx" % (dL, dI))
            ck(dL > 6, "★ 透镜在 3D 里真的上移了", "dy=%.1f" % dL)
            ck(dI > dL * 1.12, "★ 像同向偏移、且位移更大（(1+m) 因子）",
               "像 %.1f vs 镜 %.1f" % (dI, dL))

            fr.evaluate(SET_JS, ["lz", 2])
            pg.wait_for_timeout(400)
            ck("侧+2.0" in fr.inner_text("#ro-loff"), "透镜左右 2.0 cm 生效",
               fr.inner_text("#ro-loff").replace("\n", " "))
            pg.screenshot(path=str(BASE / "_v647_3D凸透镜_透镜偏移.png"))

            # --- 归零 → 恢复；老功能不受影响
            for nm in ("ly", "lz", "oy", "oz"):
                fr.evaluate(SET_JS, [nm, 0])
            pg.wait_for_timeout(420)
            ck("居中" in fr.inner_text("#ro-loff"), "归零后回到「居中（与中轴共轴）」",
               fr.inner_text("#ro-loff").replace("\n", " "))
            ck("在光轴上" in fr.inner_text("#ro-off"), "归零后物回到光轴上")
            ck(fr.inner_text("#ro-u").replace("\n", " ").find("42.0") >= 0,
               "物距读数仍为 42.0（老功能未受影响）",
               fr.inner_text("#ro-u").replace("\n", " "))
            ck(fr.evaluate("()=>document.getElementById('fv-u').textContent").startswith("42.0"),
               "底栏物距滑块数值显示正常")
            ft = fr.evaluate("()=>{const x=document.getElementById('fc-cone');"
                             "x.click();const a=x.getAttribute('aria-pressed');x.click();return a;}")
            ck(ft == "false", "立体光锥开关可切换（关→再开）", ft)

            ck(not pg.evaluate("(window.__rbErrors||[]).length"), "错误账本仍为空")
            # 退出 3D，避免影响后续视口复扫
            click(pg, '.s3d-bar[data-s3d="lens"] .s3d-b[data-m="2d"]')
            pg.wait_for_timeout(500)

        # ================================================== 8 控制台
        print("\n== 8 控制台 ==")
        real = [e for e in errs if not any(k in e for k in
                ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED"))]
        for e in real:
            print("     ", e[:200])
        ck(not real, "全程零真实控制台错误", len(real))
        ck(pg.evaluate("(window.__rbErrors||[]).length === 0"), "错误账本仍为空")

        b.close()

    print("\n" + "=" * 60)
    if FAILS:
        print("失败 %d 项：" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        raise SystemExit(1)
    print("V6.4.7 端到端全部通过")


if __name__ == "__main__":
    main()
