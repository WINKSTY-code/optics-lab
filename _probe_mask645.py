# -*- coding: utf-8 -*-
"""探针：启动后 #aiCfgMask 的真实状态与出现时机，以及所有 .modal-mask 的 display。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()


def snap(pg, tag):
    data = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.modal-mask').forEach(m => {
        const cs = getComputedStyle(m);
        out.push({id: m.id, cls: m.className, disp: cs.display, z: cs.zIndex,
                  vis: cs.visibility, pe: cs.pointerEvents});
      });
      const t = document.elementFromPoint(700, 450);
      return {masks: out, top: t ? (t.tagName + '#' + t.id + '.' + t.className) : null};
    }""")
    print("--- %s ---" % tag)
    for m in data["masks"]:
        print("   %-14s cls=%-24s disp=%-8s z=%-6s pe=%s" %
              (m["id"] or "(noid)", m["cls"], m["disp"], m["z"], m["pe"]))
    print("   中心点命中元素: %s" % data["top"])


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    snap(pg, "启动后（未做任何清理）")
    pg.evaluate("switchTab('line')")
    pg.wait_for_timeout(500)
    snap(pg, "切到 line 页后")
    b.close()
