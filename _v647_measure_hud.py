# -*- coding: utf-8 -*-
"""量一量 3D 场景的 HUD 说明文字与浮动标签有没有真的重叠。"""
import pathlib
from playwright.sync_api import sync_playwright

SCENE = (pathlib.Path(r'C:\Users\Administrator\Desktop\AI光学参赛') / '_extract_v646_lens.html').as_uri()
JS = """() => {
  const sub = document.querySelector('#hud .sub');
  const sr = sub.getBoundingClientRect();
  const cs = getComputedStyle(sub);
  const out = [];
  document.querySelectorAll('#labels .lb').forEach(el => {
    if (getComputedStyle(el).display === 'none') return;
    const r = el.getBoundingClientRect();
    const ov = !(r.right < sr.left || r.left > sr.right || r.bottom < sr.top || r.top > sr.bottom);
    out.push({t: el.textContent.trim(), x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height), ov: ov});
  });
  return {sub: {x: Math.round(sr.x), y: Math.round(sr.y), w: Math.round(sr.width),
                h: Math.round(sr.height), mw: cs.maxWidth, fs: cs.fontSize}, labels: out};
}"""

with sync_playwright() as pw:
    br = pw.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    for w, h in ((1440, 900), (1280, 800), (1024, 768)):
        pg = br.new_page(viewport={'width': w, 'height': h})
        pg.goto(SCENE)
        pg.wait_for_function("()=>{var b=document.getElementById('boot');"
                             "return !!b && (b.style.display==='none'||b.classList.contains('done'));}",
                             timeout=45000)
        pg.wait_for_timeout(1200)
        d = pg.evaluate(JS)
        print('== %dx%d ==' % (w, h))
        print('  sub  x=%d y=%d w=%d h=%d  max-width=%s font=%s'
              % (d['sub']['x'], d['sub']['y'], d['sub']['w'], d['sub']['h'], d['sub']['mw'], d['sub']['fs']))
        bad = [l for l in d['labels'] if l['ov']]
        print('  标签 %d 个，与 sub 重叠：%s' % (len(d['labels']), [(l['t'], l['x'], l['y']) for l in bad] or '无'))
        pg.close()
    br.close()
