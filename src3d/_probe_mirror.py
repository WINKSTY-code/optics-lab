# -*- coding: utf-8 -*-
import os, pathlib
from playwright.sync_api import sync_playwright
BASE=os.path.dirname(os.path.abspath(__file__))
url=(pathlib.Path(BASE)/"3D_平面镜成像_棋子.html").resolve().as_uri()
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    pg=b.new_page(viewport={"width":1440,"height":900})
    pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(BASE,"_m0_默认.png"))
    pg.click("#tl-side"); pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(BASE,"_m1_透过玻璃看虚像.png"))
    print("front ghost visible:", pg.evaluate("""() => { let v=null;
      S3D.scene.traverse(o=>{ if(o.isMesh&&o.geometry&&o.geometry.type==='LatheGeometry'&&o.material.transparent) v=o.visible; });
      return v; }"""))
    # 把镜头绕到板后
    pg.evaluate("S3D.camera.position.set(3.2, 0.9, 0.02); S3D.controls.target.set(0,0.26,0); S3D.controls.update();")
    pg.wait_for_timeout(900)
    print("behind ghost visible:", pg.evaluate("""() => { let v=null;
      S3D.scene.traverse(o=>{ if(o.isMesh&&o.geometry&&o.geometry.type==='LatheGeometry'&&o.material.transparent) v=o.visible; });
      return v; }"""))
    pg.screenshot(path=os.path.join(BASE,"_m2_绕到板后.png"))
    b.close()
