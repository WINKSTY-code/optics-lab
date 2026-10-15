# -*- coding: utf-8 -*-
"""V6.4.9 前置探针：① 各面板 .ctrl 放在 .left 还是 .right；② 物体颜色模式当前是否真的什么都没有。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.8.html").resolve().as_uri()

PROBE = r"""() => {
  const out = { panels: [], disp: null };
  document.querySelectorAll('.panel').forEach(p => {
    const l = p.querySelector('.stage > .left'), r = p.querySelector('.stage > .right');
    if (!l && !r) return;
    const cl = l ? l.querySelectorAll(':scope > .ctrl').length : -1;
    const cr = r ? r.querySelectorAll(':scope > .ctrl').length : -1;
    out.panels.push({ id: p.id, left: cl, right: cr,
                      hasStage: !!(p.querySelector('.s3d-stage')) });
  });
  // 物体颜色模式实测
  const q = s => document.querySelector(s);
  out.disp = {
    modeBtns: [...document.querySelectorAll('#disp-mode .sec')].map(b => b.dataset.m),
    rgbCtrlDisplay: q('#disp-rgb-ctrl') ? getComputedStyle(q('#disp-rgb-ctrl')).display : 'MISSING',
    objCtrlDisplay: q('#disp-obj-ctrl') ? getComputedStyle(q('#disp-obj-ctrl')).display : 'MISSING',
    objCtrlParent: q('#disp-obj-ctrl') ? (q('#disp-obj-ctrl').parentNode.id || q('#disp-obj-ctrl').parentNode.className) : 'MISSING',
    rgbCtrlParent: q('#disp-rgb-ctrl') ? (q('#disp-rgb-ctrl').parentNode.id || q('#disp-rgb-ctrl').parentNode.className) : 'MISSING',
    visBtnsInObjCtrl: q('#disp-obj-ctrl') ? [...q('#disp-obj-ctrl').querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0).length : -1,
    objCtrlHeight: q('#disp-obj-ctrl') ? Math.round(q('#disp-obj-ctrl').getBoundingClientRect().height) : -1
  };
  return out;
}"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(1600)
        pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
            m.classList.remove('show'); m.classList.remove('is-closing'); })""")
        try:
            if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
                pg.fill("#stuName", "E2E"); pg.fill("#stuNo", "E2E")
                pg.click("#stuAdd"); pg.wait_for_timeout(700)
        except Exception:
            pass
        pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
            m.classList.remove('show'); m.classList.remove('is-closing'); })""")

        d = pg.evaluate(PROBE)
        print("%-14s %-7s %-7s %s" % ("panel", ".left", ".right", "3D?"))
        print("-" * 42)
        for x in d["panels"]:
            print("%-14s %-7s %-7s %s" % (x["id"], x["left"], x["right"], x["hasStage"]))
        print("\n=== 切到「物体颜色」模式 ===")
        pg.click('.tab-btn[data-tab="disperse"]')
        pg.wait_for_timeout(300)
        pg.click('#disp-mode .sec[data-m="obj"]')
        pg.wait_for_timeout(300)
        for k, v in pg.evaluate(PROBE)["disp"].items():
            print("  %-18s %s" % (k, v))
        pg.screenshot(path=str(BASE / "_v649_修前_物体颜色模式.png"),
                      clip={"x": 0, "y": 0, "width": 1440, "height": 620})
        b.close()
    print("\n截图：_v649_修前_物体颜色模式.png")


if __name__ == "__main__":
    main()
