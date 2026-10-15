# -*- coding: utf-8 -*-
"""探针：量 v6.4.7 顶栏各元素几何，定位「右上角空了一块」。
只读，不改任何文件。"""
import pathlib, json
from playwright.sync_api import sync_playwright

TARGET = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛/光学交互实验室_AI_v6.4.7.html")
URL = TARGET.resolve().as_uri()

JS = r"""() => {
  const q = s => document.querySelector(s);
  const R = e => { if(!e) return null; const r = e.getBoundingClientRect();
    return {l:+r.left.toFixed(1), r:+r.right.toFixed(1), w:+r.width.toFixed(1), t:+r.top.toFixed(1), b:+r.bottom.toFixed(1)}; };
  const bar = q('.topbar');
  const cs = getComputedStyle(bar);
  const tr = R(bar), ti = R(q('.title')), tp = R(q('.topbar-right')), sw = R(q('.set-wrap'));
  const kids = [...bar.children].map(e => ({
    cls: e.className || e.tagName, x: +e.getBoundingClientRect().left.toFixed(1),
    w: +e.getBoundingClientRect().width.toFixed(1)
  }));
  return {
    vw: window.innerWidth,
    mode: document.documentElement.getAttribute('data-mode'),
    justify: cs.justifyContent, wrap: cs.flexWrap, gap: cs.gap,
    bar: tr, title: ti, right: tp, setwrap: sw, kids,
    gapTitle2Right: (ti && tp) ? +(tp.l - ti.r).toFixed(1) : null,
    gapRight2Set: (tp && sw) ? +(sw.l - tp.r).toFixed(1) : null,
    gapSet2End: (sw && tr) ? +(tr.r - sw.r).toFixed(1) : null
  };
}"""

VIEWPORTS = [(1920, 900), (1600, 900), (1440, 900), (1366, 800), (1280, 800),
             (1100, 800), (1000, 800), (900, 800), (880, 800), (700, 800),
             (560, 800), (480, 800), (390, 780), (360, 780)]

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        print("%-11s %-8s %-16s %-6s %-9s %-9s %-9s" %
              ("视口", "mode", "justify", "wrap", "标题→按钮组", "按钮组→设置", "设置→右端"))
        print("-" * 78)
        for w, h in VIEWPORTS:
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
            pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
            pg.goto(URL, wait_until="domcontentloaded")
            pg.wait_for_timeout(900)
            try:
                pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m=>{
                    m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")
            except Exception:
                pass
            d = pg.evaluate(JS)
            print("%-11s %-8s %-16s %-6s %-9s %-9s %-9s" % (
                "%dx%d" % (w, h), d["mode"] or "-", d["justify"], d["wrap"],
                d["gapTitle2Right"], d["gapRight2Set"], d["gapSet2End"]))
            print("            kids: " + json.dumps(d["kids"], ensure_ascii=False))
            pg.close()
        b.close()

if __name__ == "__main__":
    main()
