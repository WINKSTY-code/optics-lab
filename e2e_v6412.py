# -*- coding: utf-8 -*-
"""V6.4.12 端到端（真实 Chromium / file://）
① 打开挑战模式自动随机一道选择题；切走再回来仍出选择题；
② 用户亲手选一道作图题后，切走再回来【不被接管】；
③ 「🎲 随机一题」与「点选即判」机制未破坏；
④ 启动看门狗 15s：页面正常就绪、无误报浮层（15s 数值由静态自检覆盖）；
⑤ 全量回归。
★ 挑战模式整体包在 IIFE 里（PROBLEMS/STATE/judgeUserPicked 都不可从外部求值），
  一律改用 DOM 事实断言：.jp-item.active 的 data-pid / .jp-type、.qcard 可见性、
  .qcard-opts.locked 与 chosen-right/chosen-wrong 标记。
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.12.html").resolve().as_uri()

PASS, FAIL = [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)


def clear_masks(pg):
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")


def dismiss_first_run(pg):
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.fill("#stuName", "E2E测试")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(700)
    except Exception:
        pass
    clear_masks(pg)


def open_tab(pg, key):
    """真实点击导航按钮（挑战模式自动出题挂在捕获阶段 click 委托上，必须真实点击）"""
    pg.click('.tab-btn[data-tab="%s"]' % key)
    pg.wait_for_timeout(500)


JSTATE = r"""() => {
  const tab = document.getElementById('tab-judge');
  const wrap = document.querySelector('#tab-judge .canvas-wrap');
  const qcard = wrap ? wrap.querySelector('.qcard') : null;
  const cv = document.getElementById('cv-judge');
  const act = document.querySelector('#judgeProblemList .jp-item.active');
  const tag = act && act.querySelector('.jp-type') ? act.querySelector('.jp-type').textContent.trim() : null;
  const q = qcard ? qcard.children[1] : null;
  return {
    active: tab.classList.contains('active'),
    pid: act ? act.dataset.pid : null,
    typeTag: tag,
    isPick: !!(qcard && qcard.getBoundingClientRect().height > 0),
    qcardTag: qcard ? (qcard.textContent.indexOf('单选题') >= 0) : false,
    qcardQuestion: q ? (q.textContent || '').trim() : '',
    optCount: qcard ? qcard.querySelectorAll('.qcard-opt').length : 0,
    canvasHidden: cv ? cv.style.display === 'none' : null,
    listPick: [...document.querySelectorAll('#judgeProblemList .jp-type')]
                .filter(e => e.textContent.trim() === '单选').length,
    listTrace: [...document.querySelectorAll('#judgeProblemList .jp-type')]
                .filter(e => e.textContent.trim() === '手绘').length
  };
}"""

REG = r"""() => ({
  tabs: document.querySelectorAll('.tab-btn').length,
  panels: document.querySelectorAll('.panel').length,
  canvases: document.querySelectorAll('canvas').length,
  badge: (document.querySelector('.ver-badge') || {}).textContent,
  rbErrors: (window.__rbErrors || []).length,
  overlay: !!document.getElementById('__rbOverlay'),
  ready: !!window.__APP_READY,
  modules: typeof MODULES === 'object' && typeof REPORT === 'object' && typeof S3D === 'object',
  logFirst: (() => { const it = document.querySelector('.log-list .log-item .log-ver');
                     return it ? it.textContent.trim() : null; })(),
  logFirstTxt: (() => { const it = document.querySelector('.log-list .log-item p');
                        return it ? it.textContent.trim() : null; })(),
  randBtn: !!document.getElementById('judgeRandom')
})"""

NOISE = ("favicon", "Failed to load resource", "net::ERR_FAILED", "ERR_BLOCKED",
         "ERR_ABORTED", "cdn.jsdelivr.net", "fonts.googleapis.com")


def main():
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        dismiss_first_run(pg)

        print("\n== 0. 页面健康 ==")
        reg = pg.evaluate(REG)
        noisy = [e for e in errs if not any(n in e for n in NOISE)]
        ck(reg["rbErrors"] == 0, "自带错误账本 __rbErrors == 0")
        ck(not reg["overlay"], "启动失败浮层 #__rbOverlay 不存在")
        ck(reg["ready"] is True, "__APP_READY 已置真（看门狗不会误报）")
        ck(not noisy, "控制台无非预期错误：%s" % noisy[:3])
        ck(reg["badge"] == "v6.4.12", "右下角角标 == v6.4.12（实际 %s）" % reg["badge"])
        ck(reg["randBtn"] is True, "「🎲 随机一题」按钮仍在")

        print("\n== 1. 打开挑战模式 → 自动随机一道选择题 ==")
        open_tab(pg, "judge")
        j = pg.evaluate(JSTATE)
        ck(j["active"], "挑战模式面板已激活")
        ck(j["typeTag"] == "单选", "当前题是选择题（题库高亮项标签=%s）" % j["typeTag"])
        ck(j["isPick"], "选择题卡片可见（不再是空白画布）")
        ck(j["qcardTag"], "卡片标注「单选题」")
        ck(j["optCount"] == 4, "选项 4 个（实际 %d）" % j["optCount"])
        ck(j["canvasHidden"] is True, "作图画布已隐藏（被题卡覆盖）")
        ck((j["qcardQuestion"] or "").strip() != "", "题干非空：%s" % (j["qcardQuestion"] or "")[:30])
        ck(j["listPick"] >= 30, "选择题池充足（列表可见 %d 道单选）" % j["listPick"])

        print("\n== 2. 切走再回来 → 仍自动出选择题 ==")
        pid1 = j["pid"]
        open_tab(pg, "reflect")
        open_tab(pg, "judge")
        j2 = pg.evaluate(JSTATE)
        ck(j2["typeTag"] == "单选" and j2["isPick"], "回来后仍是选择题（高亮项=%s）" % j2["pid"])
        ck(j2["qcardVisible"] if False else j2["isPick"], "回来后选择题卡片仍可见")

        print("\n== 3. 用户亲手选一道作图题 → 切走再回来【不被接管】 ==")
        trace_id = pg.evaluate("""() => {
          const it = [...document.querySelectorAll('#judgeProblemList .jp-type')]
                      .find(e => e.textContent.trim() === '手绘');
          return it ? it.closest('.jp-item').dataset.pid : null;
        }""")
        ck(bool(trace_id), "找到一个作图题（%s）" % trace_id)
        pg.evaluate("""(tid) => {
          const el = document.querySelector('#judgeProblemList .jp-item[data-pid="' + tid + '"]');
          el.scrollIntoView({block:'center'});
          el.click();
        }""", trace_id)
        pg.wait_for_timeout(400)
        j3 = pg.evaluate(JSTATE)
        ck(j3["pid"] == trace_id and j3["typeTag"] == "手绘", "已切到指定作图题（%s）" % trace_id)
        ck(j3["canvasHidden"] is False, "作图画布恢复显示")
        open_tab(pg, "lens")
        open_tab(pg, "judge")
        j4 = pg.evaluate(JSTATE)
        ck(j4["pid"] == trace_id, "切走再回来仍是同一道作图题（不被换掉，pid=%s）" % j4["pid"])
        ck(j4["typeTag"] == "手绘", "类型未变（手绘）")

        print("\n== 4. 「🎲 随机一题」按钮 ==")
        pg.click("#judgeRandom")
        pg.wait_for_timeout(400)
        j5 = pg.evaluate(JSTATE)
        ck(j5["typeTag"] == "单选" and j5["isPick"], "点随机按钮 → 出选择题（%s）" % j5["pid"])

        print("\n== 5. 全量回归 ==")
        reg2 = pg.evaluate(REG)
        ck(reg2["tabs"] == 11, "导航按钮 == 11（实际 %s）" % reg2["tabs"])
        ck(reg2["panels"] == 12, "面板 == 12（实际 %s）" % reg2["panels"])
        ck(reg2["canvases"] == 11, "canvas == 11（实际 %s）" % reg2["canvases"])
        ck(reg2["modules"], "MODULES / REPORT / S3D 均在")
        ck(reg2["logFirst"] == "V6.4.12", "更新日志首条 == V6.4.12")
        ck(reg2["logFirstTxt"] == "挑战模式自动出题，启动超时15秒。", "首条正文 == %s" % reg2["logFirstTxt"])
        ck(len(reg2["logFirstTxt"]) <= 20, "首条正文 %d 字 ≤ 20" % len(reg2["logFirstTxt"]))
        open_tab(pg, "lens")
        ck(pg.evaluate("document.getElementById('tab-lens').classList.contains('active')"), "切换实验面板正常")

        print("\n== 6. 点选即判 + 锁定（放最后：答完约 3 秒会自动切下一题） ==")
        open_tab(pg, "judge")
        pg.wait_for_timeout(300)
        r = pg.evaluate("""() => {
          const qcard = document.querySelector('#tab-judge .qcard');
          if (!qcard || qcard.getBoundingClientRect().height <= 0) return {ok:false};
          const inp = qcard.querySelector('.qcard-opt input');
          if (!inp) return {ok:false};
          const before = qcard.querySelector('.qcard-opts').className;
          inp.checked = true;
          inp.dispatchEvent(new Event('change', {bubbles:true}));
          const opts = qcard.querySelector('.qcard-opts');
          return { ok: true, before: before,
                   locked: opts.classList.contains('locked'),
                   marks: qcard.querySelectorAll('.chosen-right,.chosen-wrong').length,
                   badge: !!qcard.querySelector('.qcard-opt span') };
        }""")
        ck(r.get("ok"), "选择题可作答")
        ck(r.get("locked") is True, "答完即锁定（.qcard-opts.locked）")
        ck(r.get("marks", 0) >= 1, "对错标记已挂上（chosen-right/chosen-wrong ×%d）" % r.get("marks", 0))

        errs2 = [e for e in errs if not any(n in e for n in NOISE)]
        ck(not errs2, "全程无非预期控制台错误：%s" % errs2[:3])
        ck(pg.evaluate("(window.__rbErrors||[]).length") == 0, "全程 __rbErrors 保持 0")

        b.close()

    print("\n" + "=" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  - " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
