# -*- coding: utf-8 -*-
import pathlib
from playwright.sync_api import sync_playwright
URL = pathlib.Path(r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.3.html").resolve().as_uri()
with sync_playwright() as p:
    b = p.chromium.launch()
    for w,h in [(1280,800),(1366,768),(1440,900),(1600,900),(1920,1080),(390,844)]:
        pg = b.new_page(viewport={"width":w,"height":h})
        errs=[]
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(900)
        r = pg.evaluate("""() => {
          const el = (s)=>document.querySelector(s);
          document.querySelectorAll('.mask,.modal,.aiCfgMask').forEach(e=>e.classList.remove('show'));
          if (window.switchTab) switchTab('line');
          const sec = el('#tab-line'); const left = sec.querySelector('.left');
          const stage = sec.querySelector('.s3d-stage');
          const fr = sec.querySelector('.s3d-frame[data-s3d="pinhole"]');
          const bar = sec.querySelector('.s3d-bar[data-s3d="pinhole"]');
          const rl = left.getBoundingClientRect();
          const rf = fr.getBoundingClientRect();
          const rb = bar.getBoundingClientRect();
          return {left:[Math.round(rl.width),Math.round(rl.height)],
                  frame:[Math.round(rf.width),Math.round(rf.height)],
                  bar:[Math.round(rb.width),Math.round(rb.height)],
                  barRight: Math.round(rb.right), barBottomFromBottom: Math.round(innerHeight-rb.bottom),
                  mode: document.documentElement.getAttribute('data-mode')||'desktop'};
        }""")
        print(w,h,"=> left",r['left']," frame",r['frame']," bar",r['bar'],"barRight",r['barRight'],"barBottomInset",r['barBottomFromBottom'],"mode",r['mode'])
        pg.close()
    b.close()
