# -*- coding: utf-8 -*-
"""候选说明文案的实测行高（要在 1024 宽下仍≤2 行，避免压到浮动标签）。"""
import pathlib
from playwright.sync_api import sync_playwright

SCENE = (pathlib.Path(r'C:\Users\Administrator\Desktop\AI光学参赛') / '_extract_v646_lens.html').as_uri()

CANDS = [
    ('现行 3 句',
     '从烛焰顶端发出的光经凸透镜后会聚到一点，光屏放到那个位置就出现<b>倒立的实像</b>。'
     '拖动「物体上下 / 左右」把蜡烛移离主光轴 —— 像会向<b>相反方向</b>移动，像距不变；'
     '拖动「透镜上下 / 左右」让透镜偏离光具座中轴（<b>共轴调节</b>）—— 像会跟着<b>同向</b>偏移。'
     '转动视角看整束光锥怎样穿过这枚<b>立体的双凸透镜</b>。'),
    ('A 两行紧凑',
     '烛焰发出的光经凸透镜会聚到一点，光屏放那儿就出现<b>倒立的实像</b>。'
     '「物体」与「透镜」都能上下左右移动：物移则像<b>反向</b>偏移，'
     '透镜移则像<b>同向</b>偏移（共轴调节），像距不变。'),
    ('B 两行更短',
     '烛焰发出的光经凸透镜会聚到一点，光屏放那儿就出现<b>倒立的实像</b>。'
     '物体与透镜都能上下左右移动：物移则像<b>反向</b>偏，透镜移则像<b>同向</b>偏，像距不变。'),
    ('C 一句半',
     '烛焰发出的光经凸透镜会聚到一点，光屏放那儿就出现<b>倒立的实像</b>。'
     '拖动「物体 / 透镜」上下左右移动，可看像怎样随之偏移（<b>共轴调节</b>）。'),
]

JS = """(html) => {
  const sub = document.querySelector('#hud .sub');
  sub.innerHTML = html;
  const r = sub.getBoundingClientRect();
  const lh = parseFloat(getComputedStyle(sub).lineHeight) || 0;
  return {h: Math.round(r.height), bottom: Math.round(r.bottom), lh: lh,
          lines: lh ? Math.round(r.height / lh) : -1};
}"""

with sync_playwright() as pw:
    br = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    pg = br.new_page(viewport={'width': 1024, 'height': 768})
    pg.goto(SCENE)
    pg.wait_for_function("()=>{var b=document.getElementById('boot');"
                         "return !!b && (b.style.display==='none'||b.classList.contains('done'));}",
                         timeout=45000)
    pg.wait_for_timeout(1000)
    print('1024x768 下（浮标签最低 top≈144）：')
    for name, html in CANDS:
        d = pg.evaluate(JS, html)
        print('  %-10s 高=%-4d 底=%-4d 行数=%d  %s'
              % (name, d['h'], d['bottom'], d['lines'], 'OK' if d['bottom'] < 144 else '会压到标签'))
    br.close()
