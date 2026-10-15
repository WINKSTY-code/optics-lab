# -*- coding: utf-8 -*-
"""V6.4.12 启动看门狗专项（真机计时）：
把 window.__APP_READY 钉死为 false，模拟「页面一直没初始化完」，然后真等：
  · 第 12 秒（旧上限 10s 已过）→ 不得弹「页面启动超时」
  · 第 16 秒（新上限 15s 已过）→ 必须弹，且文案是「15 秒」
这是对用户那句「网速慢 10 秒没加载出来就会被它截断，改成 15 秒」的最直接验证。
"""
import pathlib, sys, time
from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.4.12.html").resolve().as_uri()
PASS, FAIL = [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)


def overlay_state(pg):
    return pg.evaluate("""() => {
      const o = document.getElementById('__rbOverlay');
      return { exists: !!o, visible: !!(o && o.getBoundingClientRect().height > 0),
               txt: o ? (o.textContent || '') : '' };
    }""")


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        # 钉死 __APP_READY：看门狗永远认为「还没就绪」
        pg.add_init_script("""
          Object.defineProperty(window, '__APP_READY', {
            configurable: true,
            get: function(){ return false; },
            set: function(){}
          });
        """)
        pg.goto(URL, wait_until="domcontentloaded")
        t0 = time.time()

        pg.wait_for_timeout(12000)
        st = overlay_state(pg)
        ck(not st["exists"], "第 %.0f 秒：未弹报错浮层（旧上限 10s 已过）" % (time.time() - t0))

        pg.wait_for_timeout(4500)
        st = overlay_state(pg)
        ck(st["exists"] and st["visible"], "第 %.0f 秒：报错浮层已弹出（新上限 15s 已过）" % (time.time() - t0))
        ck("页面启动超时" in st["txt"], "浮层标题是「页面启动超时」")
        ck("15 秒" in st["txt"] and "10 秒" not in st["txt"],
           "浮层文案写的是「超过 15 秒」，且没有「10 秒」残留")
        try:
            pg.screenshot(path=str(BASE / "_v6412_启动超时15秒.png"))
            print("  (截图 _v6412_启动超时15秒.png)")
        except Exception:
            pass
        b.close()

    print("-" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("  - " + f)
        sys.exit(1)


if __name__ == "__main__":
    main()
