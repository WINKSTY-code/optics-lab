# -*- coding: utf-8 -*-
"""对比 v6.4.26 与 v6.5.0：加载后立即统计 canvas 数 + 列出失败的网络请求，
判定 E2E 里那 2 条「失败」是改动引入的，还是改动前就存在的。"""
import pathlib, json
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
FILES = ["光学交互实验室_AI_v6.4.26.html", "光学交互实验室_AI_v6.5.0.html"]

with sync_playwright() as pw:
    br = pw.chromium.launch()
    for f in FILES:
        pg = br.new_page(viewport={"width": 1440, "height": 900})
        failed, cerr = [], []
        pg.on("requestfailed", lambda r: failed.append((r.url[:110], (r.failure or ""))))
        pg.on("console", lambda m: (cerr.append(m.text[:140]) if m.type == "error" else None))
        pg.goto((BASE / f).resolve().as_uri())
        pg.wait_for_timeout(2500)
        # 不做任何操作，直接数（避免挂 3D 场景额外引入 canvas）
        n_canvas = pg.evaluate("() => document.querySelectorAll('canvas').length")
        ids = pg.evaluate("""() => Array.from(document.querySelectorAll('canvas')).map(c => c.id || c.className || '(no-id)')""")
        ext = pg.evaluate("""() => Array.from(document.querySelectorAll('link[href],script[src],img[src]'))
              .map(e => e.getAttribute('href') || e.getAttribute('src'))
              .filter(u => u && /^https?:/i.test(u))""")
        print("=" * 70)
        print(f)
        print("  canvas 数（静态，未挂 3D）:", n_canvas)
        print("  canvas 清单:", ids)
        print("  外链资源:", ext if ext else "（无）")
        print("  请求失败:", failed if failed else "（无）")
        print("  console.error:", cerr if cerr else "（无）")
        pg.close()
    br.close()
