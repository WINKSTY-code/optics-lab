# -*- coding: utf-8 -*-
"""V6.4.7 · 3D 凸透镜场景（独立文件）浏览器端到端验证。

覆盖：
  A 启动与零报错
  B 底栏「一行三个」栅格（9 个控件 → 3×3）
  C 新增「透镜上下 / 左右」两个滑杆可用、读数联动
  D 透镜平移的物理正确性（像同向偏移，且位移量 > 透镜自身位移，即 (1+m) 因子）
  E 多视口布局不溢出
  F 截图存档
"""
import io
import os
import sys

from playwright.sync_api import sync_playwright

SCENE = 'file:///C:/Users/Administrator/Desktop/AI光学参赛/_extract_v646_lens.html'
OUT = r'C:\Users\Administrator\Desktop\AI光学参赛'

R = []


def chk(ok, name, detail=''):
    R.append((bool(ok), name, str(detail)))
    print(('  [PASS] ' if ok else '  [FAIL] ') + name + (('  | ' + str(detail)) if detail else ''))


def shot(page, name):
    p = os.path.join(OUT, name)
    page.screenshot(path=p)
    print('  shot -> %s' % name)
    return p


JS_LB = """(t)=>{
  const els=[...document.querySelectorAll('#labels .lb')];
  const el=els.find(e=>e.textContent.trim()===t);
  if(!el) return null;
  if(getComputedStyle(el).display==='none') return null;
  const r=el.getBoundingClientRect();
  return {x:+(r.x+r.width/2).toFixed(2), y:+(r.y+r.height/2).toFixed(2)};
}"""

JS_SET = """(a)=>{
  const el=document.getElementById('fc-'+a[0]);
  if(!el) return 'no-el';
  el.value=String(a[1]);
  el.dispatchEvent(new Event('input',{bubbles:true}));
  return el.value;
}"""

JS_GRID = """()=>{
  const bad=[];
  const c=document.getElementById('ctl'), b=document.getElementById('ctlBody');
  if(!c||!b) return {bad:['no #ctl'], n:0, rows:0, cols:''};
  const r=c.getBoundingClientRect();
  if(r.left<-1||r.right>window.innerWidth+1) bad.push('ctl 越界 '+r.left.toFixed(0)+'..'+r.right.toFixed(0)+' vw='+window.innerWidth);
  if(r.bottom>window.innerHeight+1) bad.push('ctl 底越界 '+r.bottom.toFixed(0));
  if(r.height>window.innerHeight*0.48) bad.push('ctl 过高 '+r.height.toFixed(0)+' / vh='+window.innerHeight);
  if(b.scrollWidth>b.clientWidth+2) bad.push('ctlBody 横向溢出 '+b.scrollWidth+'>'+b.clientWidth);
  [...b.children].forEach((el,i)=>{
    const q=el.getBoundingClientRect();
    if(!q.width) return;
    if(q.right>window.innerWidth+1||q.left<-1) bad.push('控件'+i+' 越界 '+q.left.toFixed(0)+'..'+q.right.toFixed(0));
    if(q.width<38) bad.push('控件'+i+' 过窄 '+q.width.toFixed(0));
    const inp=el.querySelector('input[type=range]');
    if(inp&&inp.getBoundingClientRect().width<26) bad.push('控件'+i+' 滑杆过窄 '+inp.getBoundingClientRect().width.toFixed(0));
  });
  const tops=[...b.children].map(e=>e.getBoundingClientRect().top).sort((x,y)=>x-y);
  let rows=0, cur=-1e9;                       /* 按 12px 容差聚类，容忍按钮与滑杆高度的差异 */
  tops.forEach(t=>{ if(t-cur>12){ rows++; cur=t; } });
  return {bad:bad, n:b.children.length, rows:rows,
          cols:getComputedStyle(b).gridTemplateColumns,
          disp:getComputedStyle(b).display};
}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader',
                                      '--disable-gpu-sandbox'])
        pg = br.new_page(viewport={'width': 1280, 'height': 800}, device_scale_factor=1)
        errs, warns = [], []
        pg.on('pageerror', lambda e: errs.append('pageerror: %s' % e))
        pg.on('console', lambda m: (errs if m.type == 'error' else warns).append(
            ('console.%s: %s' % (m.type, m.text))[:300]))

        pg.goto(SCENE)
        pg.wait_for_function(
            "()=>{var b=document.getElementById('boot');"
            "return !!b && (b.style.display==='none'||b.classList.contains('done'));}", timeout=45000)
        pg.wait_for_timeout(1200)

        print('\n=== A 启动 ===')
        chk(pg.evaluate("()=>document.querySelectorAll('#labels .lb').length") >= 5,
            'A1 3D 标签已投影', pg.evaluate("()=>document.querySelectorAll('#labels .lb').length"))
        chk(pg.evaluate("()=>{var c=document.querySelector('canvas');return !!c && c.width>100;}"),
            'A2 canvas 已渲染')
        chk(pg.evaluate("()=>getComputedStyle(document.getElementById('ctl')).display!=='none'"),
            'A3 底部控制条可见')

        print('\n=== B 底栏 3 个/行 ===')
        g = pg.evaluate(JS_GRID)
        chk(g['disp'] == 'grid', 'B1 #ctlBody 为 grid', g['disp'])
        chk(len(str(g['cols']).split(' ')) == 3, 'B2 三列栅格', g['cols'])
        chk(g['n'] == 9, 'B3 控件共 9 个（3×3）', g['n'])
        chk(g['rows'] == 3, 'B4 实际排成 3 行', g['rows'])
        chk(not g['bad'], 'B5 控件无越界/无横向溢出', g['bad'])
        shot(pg, '_v647_桌面_三列底栏.png')

        print('\n=== C 新滑杆可用 ===')
        for nm in ('ly', 'lz'):
            chk(pg.evaluate("(n)=>!!document.getElementById('fc-'+n)", nm), 'C-%s 控件存在' % nm)
        pg.evaluate(JS_SET, ['ly', 3])
        pg.wait_for_timeout(260)
        chk(pg.evaluate("()=>document.getElementById('fv-ly').textContent").startswith('3.0'),
            'C1 透镜上下 = 3.0 cm', pg.evaluate("()=>document.getElementById('fv-ly').textContent"))
        chk('上+3.0' in pg.evaluate("()=>document.getElementById('ro-loff').querySelector('b').textContent"),
            'C2 读数「透镜偏移」联动',
            pg.evaluate("()=>document.getElementById('ro-loff').querySelector('b').textContent"))
        pg.evaluate(JS_SET, ['lz', 2])
        pg.wait_for_timeout(260)
        chk('侧+2.0' in pg.evaluate("()=>document.getElementById('ro-loff').querySelector('b').textContent"),
            'C3 透镜左右 = 2.0 cm 联动',
            pg.evaluate("()=>document.getElementById('ro-loff').querySelector('b').textContent"))
        shot(pg, '_v647_默认视角_透镜上移.png')

        print('\n=== D 物理正确性（正侧视，u=42 f=11 → m≈0.355，像应同向且更大位移）===')
        pg.evaluate(JS_SET, ['lz', 0])
        pg.evaluate(JS_SET, ['ly', 0])
        pg.click('#tl-side')
        pg.wait_for_timeout(1600)
        L0 = pg.evaluate(JS_LB, '凸透镜')
        I0 = pg.evaluate(JS_LB, '实像')
        A0 = pg.evaluate(JS_LB, '主光轴')
        chk(L0 and I0 and A0, 'D1 基准标签可取到', (L0, I0, A0))
        pg.evaluate(JS_SET, ['ly', 3])
        pg.wait_for_timeout(300)
        L1 = pg.evaluate(JS_LB, '凸透镜')
        I1 = pg.evaluate(JS_LB, '实像')
        A1 = pg.evaluate(JS_LB, '主光轴')
        dL = L0['y'] - L1['y']          # 屏幕 y 向下为正 → 上移为正值
        dI = I0['y'] - I1['y']
        dA = A0['y'] - A1['y']
        print('     透镜位移 %.1fpx | 像位移 %.1fpx | 主光轴位移 %.1fpx（m≈%.3f）'
              % (dL, dI, dA, (42 * 11 / 31) / 42))
        chk(dL > 8, 'D2 透镜确实上移', 'dy=%.1f' % dL)
        chk(dI > 8, 'D3 像同向上移（不是相反）', 'dy=%.1f' % dI)
        chk(dI > dL * 1.12, 'D4 像位移 > 透镜位移（(1+m) 因子）', '%.1f vs %.1f' % (dI, dL))
        chk(abs(dA) > 2, 'D5 主光轴随透镜走', 'dy=%.1f' % dA)
        shot(pg, '_v647_侧视_透镜上移.png')

        print('\n=== D2 回零后应恢复 ===')
        pg.evaluate(JS_SET, ['ly', 0])
        pg.wait_for_timeout(300)
        L2 = pg.evaluate(JS_LB, '凸透镜')
        chk(abs(L2['y'] - L0['y']) < 0.8, 'D6 ly 归零后透镜回原位', '%.1f vs %.1f' % (L2['y'], L0['y']))

        print('\n=== D3 原有功能未受影响 ===')
        pg.evaluate(JS_SET, ['u', 22])
        pg.wait_for_timeout(260)
        vTxt = pg.evaluate("()=>document.getElementById('ro-v').querySelector('b').textContent")
        chk(vTxt.startswith('22.0'), 'D7 u=2f → v=22.0 cm', vTxt)
        chk('等大' in pg.evaluate("()=>document.getElementById('ro-nat').querySelector('b').textContent"),
            'D8 像的性质=等大',
            pg.evaluate("()=>document.getElementById('ro-nat').querySelector('b').textContent"))
        pg.evaluate(JS_SET, ['oy', 2])
        pg.wait_for_timeout(260)
        chk('上+2.0' in pg.evaluate("()=>document.getElementById('ro-off').querySelector('b').textContent"),
            'D9 物体上下仍可用', pg.evaluate("()=>document.getElementById('ro-off').querySelector('b').textContent"))
        pg.evaluate(JS_SET, ['oy', 0])
        pg.evaluate(JS_SET, ['u', 42])
        pg.evaluate(JS_SET, ['f', 11])
        pg.wait_for_timeout(200)

        print('\n=== E 多视口布局 ===')
        pg.click('#tl-reset')
        pg.wait_for_timeout(900)
        sweep = [(1440, 900, 3), (1280, 800, 3), (1100, 800, 3), (1024, 768, 3),
                 (900, 700, 5), (760, 720, 5), (560, 800, 5), (430, 820, 5),
                 (390, 780, 5), (360, 700, 5)]
        for w, h, rows in sweep:
            pg.set_viewport_size({'width': w, 'height': h})
            pg.wait_for_timeout(380)
            g = pg.evaluate(JS_GRID)
            chk(g['rows'] == rows and not g['bad'],
                'E %dx%d → %d 行' % (w, h, rows),
                'rows=%s cols=%s bad=%s' % (g['rows'], g['cols'], g['bad']))
            if w in (390,):
                shot(pg, '_v647_手机_底栏.png')
            if w == 900:
                shot(pg, '_v647_窄屏_两列.png')
        pg.set_viewport_size({'width': 1280, 'height': 800})
        pg.wait_for_timeout(300)

        print('\n=== F 报错统计 ===')
        chk(not errs, 'F1 无 console.error / pageerror', errs[:4])
        if warns:
            print('     warn(%d): %s' % (len(warns), warns[:3]))

        br.close()

    npass = sum(1 for r in R if r[0])
    print('\n================ %d/%d PASS ================' % (npass, len(R)))
    for ok, name, d in R:
        if not ok:
            print('  FAIL %s | %s' % (name, d))
    sys.exit(0 if npass == len(R) else 1)


if __name__ == '__main__':
    main()
