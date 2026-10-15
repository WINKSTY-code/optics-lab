# -*- coding: utf-8 -*-
import os, functools, http.server, socketserver, threading, pathlib
from playwright.sync_api import sync_playwright
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME="光学交互实验室_AI_v6.1.0.html"; PORT=8796
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
httpd=socketserver.TCPServer(("127.0.0.1",PORT),functools.partial(H,directory=BASE))
httpd.allow_reuse_address=True
threading.Thread(target=httpd.serve_forever,daemon=True).start()
url="http://127.0.0.1:%d/%s"%(PORT,NAME)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    pg=b.new_page(viewport={"width":1440,"height":950},device_scale_factor=1)
    pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
    pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(1600)
    pg.evaluate("document.querySelectorAll('.modal-mask').forEach(m=>{m.classList.remove('show');m.style.display='';})")
    for key,tab in [("refl","reflect"),("lens","lens"),("mirror","mirror")]:
        pg.click('.tab-btn[data-tab="%s"]'%tab); pg.wait_for_timeout(400)
        pg.click('.s3d-bar[data-s3d="%s"] button[data-m="3d"]'%key); pg.wait_for_timeout(2600)
        pg.screenshot(path=os.path.join(BASE,"_v610_%s_3D.png"%key))
        pg.click('.s3d-bar[data-s3d="%s"] button[data-m="2d"]'%key); pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(BASE,"_v610_%s_2D.png"%key))
    b.close()
httpd.shutdown()
print("shots done")
