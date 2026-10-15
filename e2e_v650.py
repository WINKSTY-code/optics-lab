# -*- coding: utf-8 -*-
"""V6.5.0 端到端回归（审计 P1-4 的「自检迁到独立侧」落地 + 方案 C 的核心验证）

覆盖：
 A. 方案 C 核心 —— 6 个内嵌 3D 子页经「占位标记 + 常量回填」后，three.js 真的在
    iframe 内执行起来：document.scripts 里能找到 ~600KB 的库、window.THREE.REVISION
    可读，且 5 个 r147 页同版本、影子页是另一个构建（两构建的现状被原样保留）。
 B. 从生产文件移除 runE2E 后，原先那批自检项改由本脚本从外部覆盖（可覆盖的部分）。
 C. 全程无 pageerror / 无 console error。
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.5.0.html").resolve().as_uri()

PASS, FAIL, NOTE = [], [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)
    return bool(cond)


def note(msg):
    NOTE.append(msg)
    print("  --   " + msg)


def clear_masks(pg):
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")


def dismiss_first_run(pg):
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.fill("#stuName", "E2E")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(600)
    except Exception:
        pass
    clear_masks(pg)


def click_tab(pg, t):
    pg.evaluate("""t => { const b = document.querySelector('.tab-btn[data-tab="' + t + '"]'); if (b) b.click(); }""", t)
    pg.wait_for_timeout(200)


def click_line_mode(pg, m):
    pg.evaluate("""m => { const b = document.querySelector('#line-mode button[data-m="' + m + '"]'); if (b) b.click(); }""", m)
    pg.wait_for_timeout(350)


def click_3d(pg, k):
    pg.evaluate("""k => { const b = document.querySelector('.s3d-bar[data-s3d="' + k + '"] .s3d-b[data-m="3d"]'); if (b) b.click(); }""", k)
    pg.wait_for_timeout(900)


PROBE = """() => {
  let libLen = null, libHead = null;
  for (let i = 0; i < document.scripts.length; i++) {
    const t = document.scripts[i].textContent || '';
    if (t.indexOf('!function(t,e){"object"==typeof exports') >= 0) { libLen = t.length; libHead = t.slice(0, 40); break; }
  }
  return {
    scripts: document.scripts.length,
    libLen: libLen,
    libHead: libHead,
    rev: (typeof THREE !== 'undefined' && THREE && THREE.REVISION) ? String(THREE.REVISION) : null,
    hasRenderer: (typeof THREE !== 'undefined' && THREE && typeof THREE.WebGLRenderer === 'function'),
    canvases: document.querySelectorAll('canvas').length,
    markerLeft: document.documentElement.outerHTML.indexOf('__S3D_THREE_LIB__')
  };
}"""


def probe_frame(pg, want_lib=True, timeout=9000):
    """轮询各子框架，找到已经跑起 three.js 的那个"""
    step = 250
    for _ in range(max(1, timeout // step)):
        for fr in pg.frames:
            if fr == pg.main_frame:
                continue
            try:
                r = fr.evaluate(PROBE)
            except Exception:
                continue
            if r and r.get("rev"):
                return fr, r
        pg.wait_for_timeout(step)
    return None, None


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = br.new_page(viewport={"width": 1440, "height": 900})
        errors, consoles = [], []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: (consoles.append(m.text) if m.type == "error" else None))
        pg.goto(URL)
        pg.wait_for_timeout(1800)

        print("== A. 方案 C 核心：three.js 经常量回填后在 iframe 内真正生效 ==")
        dismiss_first_run(pg)

        # A1 三个常驻 3D 场景（各自的标签页 / 按钮：见 mount 层 CFG）
        scenes = [("reflect", "refl"), ("lens", "lens"), ("mirror", "mirror")]
        revs = {}
        for tab, key in scenes:
            click_tab(pg, tab)
            click_3d(pg, key)
            fr, r = probe_frame(pg)
            ok = bool(r)
            ck(ok, "3D 场景 %-8s 挂载成功（iframe 内 THREE.REVISION=%s）" % (key, (r or {}).get("rev")))
            if ok:
                revs[key] = r["rev"]
                ck(r["libLen"] and r["libLen"] > 500000,
                   "  %-8s 子页内联脚本里找到完整 three.js（%s 字符）" % (key, r["libLen"]))
                ck(r["hasRenderer"], "  %-8s THREE.WebGLRenderer 可用" % key)
                ck(r["canvases"] >= 1, "  %-8s 场景 canvas 数量 %d" % (key, r["canvases"]))
                ck(r["markerLeft"] == -1, "  %-8s 占位标记已全部回填（无残留）" % key)
                pg.screenshot(path=str(BASE / ("_v650_3D_%s.png" % key)))

        # A2 直线传播页的两个按模式显示的 3D 案例
        click_tab(pg, "line")
        click_line_mode(pg, "pinhole")
        click_3d(pg, "pinhole")
        fr, r = probe_frame(pg)
        ck(bool(r), "3D 场景 pinhole  挂载成功（REVISION=%s）" % (r or {}).get("rev"))
        if r:
            revs["pinhole"] = r["rev"]
            ck(r["libLen"] and r["libLen"] > 500000, "  pinhole  库体 %s 字符" % r["libLen"])
            ck(r["markerLeft"] == -1, "  pinhole  占位标记无残留")
            pg.screenshot(path=str(BASE / "_v650_3D_pinhole.png"))

        click_line_mode(pg, "shadow")
        click_3d(pg, "shadow")
        fr, r = probe_frame(pg)
        ck(bool(r), "3D 场景 shadow   挂载成功（REVISION=%s，应为另一构建）" % (r or {}).get("rev"))
        if r:
            revs["shadow"] = r["rev"]
            ck(r["libLen"] and r["libLen"] > 500000, "  shadow   库体 %s 字符" % r["libLen"])
            ck(r["hasRenderer"], "  shadow   THREE.WebGLRenderer 可用")
            ck(r["markerLeft"] == -1, "  shadow   占位标记无残留")
            pg.screenshot(path=str(BASE / "_v650_3D_shadow.png"))

        # A3 日食与月食（ECL，另一套挂载层，同样接了回填）
        click_line_mode(pg, "eclipse")
        fr, r = probe_frame(pg)
        ck(bool(r), "3D 场景 ecl      挂载成功（REVISION=%s）" % (r or {}).get("rev"))
        if r:
            revs["ecl"] = r["rev"]
            ck(r["libLen"] and r["libLen"] > 500000, "  ecl      库体 %s 字符" % r["libLen"])
            ck(r["markerLeft"] == -1, "  ecl      占位标记无残留")
            pg.screenshot(path=str(BASE / "_v650_3D_ecl.png"))

        # A4 两构建的现状被原样保留（方案 C 的既定前提：不合并两构建，只集中存放）
        r147 = {k: v for k, v in revs.items() if k != "shadow"}
        ck(len(set(r147.values())) == 1 and len(r147) >= 4,
           "5 个 r147 场景的 REVISION 一致 == %s（%d 个页面）" % (set(r147.values()), len(r147)))
        ck(revs.get("shadow") and revs.get("shadow") not in r147.values(),
           "影子页仍是另一个构建：REVISION=%s（与 r147 不同，与改前一致）" % revs.get("shadow"))

        print("\n== B. 原 runE2E 自检项改由本侧覆盖（从生产文件移除后） ==")
        click_tab(pg, "reflect")
        n_canvas = pg.evaluate("() => document.querySelectorAll('canvas').length")
        # 注：被删掉的 runE2E 断言写的是 === 10，但 v6.4.26 实测就是 11（多出挑战模式的
        #     cv-judge）—— 那是自检项自身年久失修，与本次改动无关。这里按基线口径断言。
        ck(n_canvas == 11, "canvas_11：画布 %d 个（v6.4.26 基线同为 11；旧 runE2E 写 10 属过期）" % n_canvas)

        tab_ok, tab_err = True, ""
        for t in ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo"]:
            try:
                click_tab(pg, t)
            except Exception as e:
                tab_ok, tab_err = False, str(e)
        ck(tab_ok, "tabs_10：10 个标签页全部可切换 %s" % tab_err)

        ck(pg.evaluate("() => !!window.AI"), "ai_module：window.AI 存在")
        ck(pg.evaluate("() => typeof window.AI.runE2E === 'undefined'"),
           "ai_module：window.AI 上已无 runE2E 导出（P1-4 修复确认）")
        ck(pg.evaluate("() => { try { return window.AI.kbAll().length >= 15; } catch(e){ return false; } }"),
           "knowledge_base：知识库条目 >= 15")
        ck(pg.evaluate("""() => { try {
              const c = window.AI.getSimContextFromDOM('lens'); return typeof c === 'string' && c.length > 0;
            } catch(e){ return false; } }"""), "sim_context：凸透镜情境串可生成")
        modal_ok = pg.evaluate("""() => { try {
              document.getElementById('topChat').click();
              const on = !!document.querySelector('.modal-mask.show');
              document.getElementById('aiAskClose').click();
              return on;
            } catch(e){ return false; } }""")
        ck(modal_ok, "ask_modal：AI 提问弹窗可开可关")
        ck(pg.evaluate("""() => { try {
              window.AI.switchStudent({id:'E2E_T', name:'E2E测试', no:'E2E'}); return typeof window.AI.switchStudent === 'function';
            } catch(e){ return false; } }"""), "student_identity：身份切换接口可用")
        ck(pg.evaluate("() => { try { return !!window.AI.profSummary(); } catch(e){ return false; } }"),
           "profile：学情汇总可生成")
        note("原 runE2E 里的 kb_search / kb_answer_socratic / voice_gate / xss_tools 依赖 IIFE 内部"
             "私有函数（未挂 window），从外部不可达 —— 未纳入本侧覆盖，属已知缺口。")

        print("\n== C. 全程无脚本错误 ==")
        ck(len(errors) == 0, "pageerror 0 条（实际 %d）%s" % (len(errors), errors[:3]))
        # 外链字体（jsdelivr）在本机不可达，浏览器记 2 条 net::ERR_CONNECTION_RESET；
        # v6.4.26 逐字相同 → 非本次引入，且字体有系统回退，不影响功能。
        baseline = [c for c in consoles if "ERR_CONNECTION_RESET" in c]
        real_err = [c for c in consoles if "ERR_CONNECTION_RESET" not in c and "favicon" not in c.lower()]
        ck(len(real_err) == 0, "除已知外链字体失败外，console.error 0 条（实际 %d）%s" % (len(real_err), real_err[:3]))
        ck(len(baseline) == 2,
           "外链字体失败 %d 条，与 v6.4.26 基线一致（jsdelivr 在本机不可达，字体走系统回退）" % len(baseline))

        clear_masks(pg)
        click_tab(pg, "reflect")
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(BASE / "_v650_整页.png"), full_page=False)
        br.close()

    print("-" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if NOTE:
        print("已知缺口 %d 条" % len(NOTE))
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  - " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
