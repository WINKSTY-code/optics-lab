# -*- coding: utf-8 -*-
"""V6.5.2 取证截图：AI 设置里 minimax 的模型下拉（含新增条目）"""
import os, pathlib
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.5.2.html")
OUT = os.path.join(BASE, "_chk652")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={"width": 1440, "height": 1000}).new_page()
    for pat in ("**/cdn.jsdelivr.net/**", "**/fonts.googleapis.com/**",
                "**/fonts.gstatic.com/**", "**/unpkg.com/**"):
        pg.route(pat, lambda r: r.abort())
    pg.goto(pathlib.Path(DST).resolve().as_uri(), wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd"); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.classList.remove('is-closing');});")
    pg.click("#setBtn"); pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(600)
    pg.select_option("#aiProvider", "minimax"); pg.wait_for_timeout(250)
    pg.select_option("#aiModel", "MiniMax-M3.1-Flash-Preview"); pg.wait_for_timeout(250)

    info = pg.evaluate("""() => {
      const m = document.querySelector('#aiCfgMask .modal');
      const r = m.getBoundingClientRect();
      const ml = document.getElementById('aiModel');
      const box = document.createRange();
      box.selectNodeContents(ml);
      const mr = ml.getBoundingClientRect();
      return { modal: {x:r.x, y:r.y, w:r.width, h:r.height},
               sel: ml.value, label: ml.options[ml.selectedIndex].textContent,
               options: [...ml.options].map(o => o.textContent),
               modelRect: {x:mr.x, y:mr.y, w:mr.width, h:mr.height} };
    }""")
    print("选中:", info["sel"], "|", info["label"])
    print("下拉全部选项文本:")
    for t in info["options"]:
        print("   -", t)

    m = info["modal"]
    pg.screenshot(path=os.path.join(OUT, "cfg_minimax.png"),
                  clip={"x": max(0, m["x"] - 10), "y": max(0, m["y"] - 10),
                        "width": m["w"] + 20, "height": m["h"] + 20})
    # 控件区域特写（原生 select 无头下打不开，只能让选中值出现在控件里 —— §59④）
    r = info["modelRect"]
    pg.screenshot(path=os.path.join(OUT, "model_select.png"),
                  clip={"x": max(0, r["x"] - 14), "y": max(0, r["y"] - 30),
                        "width": r["w"] + 28, "height": r["h"] + 40})
    b.close()
print("OK 截图已保存")
