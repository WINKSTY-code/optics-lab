# -*- coding: utf-8 -*-
"""由 e2e_v600.py 生成 e2e_v610.py（版本号、切换条位置改右下角、新增跨端同步与全屏归属回归）"""
src = open('e2e_v600.py', encoding='utf-8').read()
D = []


def rep(old, new, tag, cnt=1):
    global src
    assert src.count(old) == cnt, ('MISS ' + tag, src.count(old))
    src = src.replace(old, new)
    D.append(tag)


rep('NAME = "光学交互实验室_AI_v6.0.0.html"', 'NAME = "光学交互实验室_AI_v6.1.0.html"', 'name')
rep('a(pg.locator(".ver-badge").inner_text().strip() == "v6.0.0", "版本角标 = v6.0.0")',
    'a(pg.locator(".ver-badge").inner_text().strip() == "v6.1.0", "版本角标 = v6.1.0")', 'ver')

# 切换条位置：改为断言"悬浮在画布右下角"
rep("""        geo = pg.evaluate(\"\"\"(k) => {
          const bar=document.querySelector('.s3d-bar[data-s3d="'+k+'"]');
          const cv=document.querySelector('.s3d-frame[data-s3d="'+k+'"]').parentNode.querySelector('canvas');
          const rb=bar.getBoundingClientRect(), rc=cv.getBoundingClientRect();
          return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                  right: Math.round(rc.right-rb.right), top: Math.round(rb.top-rc.top),
                  btns:[...bar.querySelectorAll('button[data-m]')].map(b=>b.textContent.trim()),
                  fs: !!bar.querySelector('.s3d-fsb')};
        }\"\"\", key)
        a(geo["inside"], "切换条悬浮在 2D 画布内（右上角）", "距右 %dpx 距上 %dpx" % (geo["right"], geo["top"]))""",
    """        geo = pg.evaluate(\"\"\"(k) => {
          const bar=document.querySelector('.s3d-bar[data-s3d="'+k+'"]');
          const cv=document.querySelector('.s3d-frame[data-s3d="'+k+'"]').parentNode.querySelector('canvas');
          const rb=bar.getBoundingClientRect(), rc=cv.getBoundingClientRect();
          return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                  right: Math.round(rc.right-rb.right), botGap: Math.round(rc.bottom-rb.bottom),
                  inLowerHalf: (rb.top + rb.bottom)/2 > (rc.top + rc.bottom)/2,
                  btns:[...bar.querySelectorAll('button[data-m]')].map(b=>b.textContent.trim()),
                  fs: !!bar.querySelector('.s3d-fsb')};
        }\"\"\", key)
        a(geo["inside"], "切换条悬浮在 2D 画布内（右下角）",
          "距右 %dpx 距下 %dpx" % (geo["right"], geo["botGap"]))
        a(geo["inLowerHalf"], "切换条位于画布下半部（右下角，不是右上角）", str(geo))""", 'geo')

# 每个场景的跨端同步补充断言
rep("""        # 3D 模式下数据记录仍照常（参数就是同一套）""",
    """        # 场景内控件 → 父页滑块回写（V6.1.0 新增）
        if key == "refl":
            fr.evaluate(\"\"\"() => { const s=document.getElementById('fc-i'); s.value=28;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }\"\"\")
            pg.wait_for_timeout(600)
            a(float(pg.evaluate("document.getElementById('refl-iSlider').value")) == 28,
              "3D 内改入射角 → 回写父页滑块 = 28", pg.evaluate("document.getElementById('refl-iSlider').value"))
            a(ro(fr, "i") == "28°", "3D 读数同步 28°", aro(fr, "i"))
        if key == "mirror":
            fr.evaluate(\"\"\"() => { const s=document.getElementById('fc-z'); s.value=5;
                                   s.dispatchEvent(new Event('input',{bubbles:true})); }\"\"\")
            pg.wait_for_timeout(500)
            zz = pg.evaluate(\"\"\"() => { const o=[];
                S3D.scene.traverse(x=>{ if(x.isMesh&&x.geometry&&x.geometry.type==='LatheGeometry')
                  o.push(+x.position.z.toFixed(3)); }); return o; }\"\"\")
            a(zz and abs(zz[0] - 0.3) < 0.02 and len(set(zz)) == 1,
              "3D 内左右移动棋子 → 物/像/B 同步（像跟着动）", str(zz))
            a(aro(fr, "z") == "5.0 cm", "读数卡显示左右位置", aro(fr, "z"))
        if key == "lens":
            nz = fr.evaluate(\"\"\"() => { let n=0;
                S3D.scene.traverse(o=>{ if(o.isMesh&&o.geometry&&o.geometry.type==='CylinderGeometry'
                  && Math.abs(o.position.z) > 0.05) n++; }); return n; }\"\"\")
            a(nz >= 10, "光锥是立体锥（有 z≠0 的光线），不是同一平面里的扇面", "z≠0 光束段 %d" % nz)

        # 3D 模式下数据记录仍照常（参数就是同一套）""", 'sync back')

# 追加：全屏归属回归（网页全屏不该被点实验名退掉）
rep("""    ok_tabs = []
    for t in ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"]:""",
    """    # 🔥 全屏归属回归：实验室顶部自带的「全屏」是全屏 documentElement 的；
    #    点实验名【绝不能】把它退掉（V6.0.0 的 bug）
    pg.evaluate(\"\"\"() => { document.querySelectorAll('.modal-mask').forEach(m=>m.classList.remove('show')); }\"\"\")
    pg.click("#fsBtn")
    pg.wait_for_timeout(700)
    st1 = pg.evaluate("({fe: !!document.fullscreenElement, isHtml: document.fullscreenElement === document.documentElement})")
    a(st1["fe"] and st1["isHtml"], "点实验室自带的「全屏」→ 整个页面进入全屏", str(st1))
    pg.click('.tab-btn[data-tab="lens"]')
    pg.wait_for_timeout(700)
    st2 = pg.evaluate("({fe: !!document.fullscreenElement, isHtml: document.fullscreenElement === document.documentElement})")
    a(st2["fe"] and st2["isHtml"], "★ 点实验名后网页全屏仍在（修复：不再误退 documentElement 全屏）", str(st2))
    pg.click("#fsBtn")
    pg.wait_for_timeout(600)
    a(not pg.evaluate("!!document.fullscreenElement"), "再点一次「全屏」可正常退出")

    ok_tabs = []
    for t in ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"]:""", 'fs owner')

# 视口复扫：跟随右下角
rep("""              return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                      rows:new Set([...bar.querySelectorAll('button')]
                             .filter(b=>b.getBoundingClientRect().width>0)   /* 隐藏键 rect 全 0，不能计入 */
                             .map(b=>Math.round(b.getBoundingClientRect().top))).size};
            }\"\"\")""",
    """              return {inside: rb.left>rc.left-2 && rb.right<rc.right+2 && rb.top>rc.top-2 && rb.bottom<rc.bottom+2,
                      inLowerHalf: (rb.top + rb.bottom)/2 > (rc.top + rc.bottom)/2,
                      rows:new Set([...bar.querySelectorAll('button')]
                             .filter(b=>b.getBoundingClientRect().width>0)   /* 隐藏键 rect 全 0，不能计入 */
                             .map(b=>Math.round(b.getBoundingClientRect().top))).size};
            }\"\"\")
            if not g["inLowerHalf"]: bad.append((vw, vh, z, "不在右下角"))""", 'vp')

open('e2e_v610.py', 'w', encoding='utf-8', newline='\n').write(src)
print('e2e_v610.py generated:', len(D), D)
