# -*- coding: utf-8 -*-
"""对照实验：既有 pinhole 3D 与新增 shadow 3D 在「切走实验页」后的 rAF 行为是否一致。
判定用 renderer.info.render.frame 实际增长，不看内部标志位。"""
import pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
URL = (BASE / "光学交互实验室_AI_v6.4.5.html").as_uri()


def clear(pg):
    pg.evaluate("""() => document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); });""")


def fr_of(pg, key):
    el = pg.query_selector('.s3d-frame[data-s3d="%s"] .s3d-ifr' % key)
    return el.content_frame() if el else None


def frames(fr):
    try:
        return fr.evaluate("((window.__dbg||window.S3D||{}).renderer||{}).info"
                           "? (window.__dbg||window.S3D).renderer.info.render.frame : -1")
    except Exception as e:
        return "ERR:" + str(e)[:60]


def probe(pg, key):
    print("\n===== %s =====" % key)
    pg.evaluate("switchTab('line')"); pg.wait_for_timeout(400); clear(pg)
    if key == "pinhole":
        pg.click('#line-mode .sec[data-m="pinhole"]'); pg.wait_for_timeout(500); clear(pg)
    pg.click('.s3d-bar[data-s3d="%s"] .s3d-b[data-m="3d"]' % key)
    pg.wait_for_timeout(2300)
    fr = fr_of(pg, key)
    print("  子文档 globals: __dbg=%s  S3D=%s  __demo=%s" % (
        fr.evaluate("typeof window.__dbg"), fr.evaluate("typeof window.S3D"),
        fr.evaluate("typeof window.__demo")))
    a = frames(fr); pg.wait_for_timeout(700); b = frames(fr)
    print("  3D 态（本页）: 帧 %s -> %s  (在渲染=%s)" % (a, b, isinstance(b, int) and isinstance(a, int) and b > a))
    pg.evaluate("switchTab('lens')")
    pg.wait_for_timeout(800)
    c = frames(fr); pg.wait_for_timeout(900); d = frames(fr)
    print("  切走后       : 帧 %s -> %s  (仍在渲染=%s)" % (c, d, isinstance(d, int) and isinstance(c, int) and d > c))
    print("  切走后 S3D.isOn('%s') = %s" % (key, pg.evaluate("S3D.isOn('%s')" % key)))
    pg.evaluate("switchTab('line')"); pg.wait_for_timeout(400)
    if key == "pinhole":
        pg.click('#line-mode .sec[data-m="pinhole"]'); pg.wait_for_timeout(400)
    clear(pg)


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(URL, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    if pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试"); pg.fill("#stuNo", "E2E"); pg.click("#stuAdd")
        pg.wait_for_timeout(700)
    clear(pg)
    probe(pg, "shadow")
    b.close()
