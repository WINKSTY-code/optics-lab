# -*- coding: utf-8 -*-
"""探针：step7 三类计数失败的真实值 + rAF 停机链路。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()


def clear_masks(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); });""")


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    # 首启弹窗
    if pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd")
        pg.wait_for_timeout(700)
    clear_masks(pg)

    print("tab-btn    =", pg.evaluate("document.querySelectorAll('.tab-btn').length"))
    print("canvas     =", pg.evaluate("document.querySelectorAll('canvas').length"))
    print("panel      =", pg.evaluate("document.querySelectorAll('.panel').length"))
    print("typeof MODULES/REPORT/S3D =", pg.evaluate(
        "[typeof window.MODULES, typeof window.REPORT, typeof window.S3D].join(' / ')"))
    print("S3D keys   =", pg.evaluate("Object.keys(window.S3D || {}).join(',')"))
    print("S3D.reclaimAll? =", pg.evaluate("typeof (window.S3D||{}).reclaimAll"))
    print("S3D.resumeFor?  =", pg.evaluate("typeof (window.S3D||{}).resumeFor"))

    # rAF 链路
    pg.evaluate("switchTab('line')"); pg.wait_for_timeout(500)
    clear_masks(pg)
    pg.click('.s3d-bar[data-s3d="shadow"] .s3d-b[data-m="3d"]')
    pg.wait_for_timeout(2200)
    el = pg.query_selector('.s3d-frame[data-s3d="shadow"] .s3d-ifr')
    fr = el.content_frame()
    print("\n[3D 开启后] run =", fr.evaluate("window.__demo.run()"))
    pg.evaluate("switchTab('lens')")
    pg.wait_for_timeout(800)
    print("[切到 lens 后] run =", fr.evaluate("window.__demo.run()"))
    print("[切到 lens 后] 父页 tab-line active =",
          pg.evaluate("document.getElementById('tab-line').classList.contains('active')"))
    print("[切到 lens 后] S3D.isOn('shadow') =", pg.evaluate("S3D.isOn('shadow')"))
    # 谁负责通知 active？
    print("[S3D 源码里 announce/resumeFor 相关]")
    src = pg.evaluate("""() => {
      const s = [...document.querySelectorAll('script')].map(x=>x.textContent)
        .filter(t=>t.indexOf("s3d:active")>=0);
      return s.length ? s[0].length : -1;
    }""")
    print("   含 s3d:active 的脚本长度 =", src)
    b.close()
