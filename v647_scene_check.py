# -*- coding: utf-8 -*-
"""V6.4.7 3D 凸透镜场景（独立文件）静态检查：拆分 script 块 + node --check + 结构断言。"""
import io
import os
import re
import subprocess
import sys

SCENE = r'C:\Users\Administrator\Desktop\AI光学参赛\_extract_v646_lens.html'
NODE = r'C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe'
OUT = r'C:\Users\Administrator\Desktop\AI光学参赛\_v647_scene_chk'

src = io.open(SCENE, encoding='utf-8').read()
if not os.path.isdir(OUT):
    os.makedirs(OUT)

# 1) 拆分 script 块（浏览器语义：</script 后面跟空白/ > / 结尾 才算结束）
blocks = []
idx = 0
low = src.lower()
while True:
    a = low.find('<script', idx)
    if a < 0:
        break
    a2 = src.find('>', a)
    b = a2 + 1
    m = re.compile(r'</script(?=[\s>/])', re.I).search(src, b)
    if not m:
        break
    blocks.append(src[b:m.start()])
    idx = m.end()

print('script blocks: %d' % len(blocks))
fails = []
for i, code in enumerate(blocks):
    if not code.strip():
        print('  block %d: 空（跳过）' % i)
        continue
    p = os.path.join(OUT, 'b%02d.js' % i)
    io.open(p, 'w', encoding='utf-8').write(code)
    r = subprocess.run([NODE, '--check', p], capture_output=True, text=True)
    tag = 'OK  ' if r.returncode == 0 else 'FAIL'
    print('  block %-2d %s len=%d' % (i, tag, len(code)))
    if r.returncode != 0:
        fails.append((i, r.stderr[:400]))

# 2) 结构断言
checks = [
    ('透镜上下滑块', 'name: \'ly\', label: \'透镜上下\''),
    ('透镜左右滑块', 'name: \'lz\', label: \'透镜左右\''),
    ('ly 参数', "name === 'ly') ly = S.px(v, -4, 4)"),
    ('lz 参数', "name === 'lz') lz = S.px(v, -4, 4)"),
    ('状态变量', 'oy = 0, oz = 0, ly = 0, lz = 0'),
    ('axG 声明', 'objG, postG, axG;'),
    ('透镜定位', 'lens.position.set(0, AY + sLy, sLz);'),
    ('光轴随动', 'axG.position.set(0, AY + sLy, sLz);'),
    ('像坐标', 'sLy - m * (yBase - sLy)'),
    ('像点坐标', 'sLy - m * (yTip - sLy)'),
    ('口径判定', 'var dy = yy - sLy, dz = zz - sLz;'),
    ('光心光线', 'rayG.add(S.beam(new V(xObj, yTip, zTip), new V(0, sLy, sLz), 0x4fc3f7, 0.013));'),
    ('透镜光锥', 'yl = sLy + rt * Math.cos(ang)'),
    ('重置含 ly', "S.setParam('ly', 0); S.setParam('lz', 0);"),
    ('读数 loff', "S.setRO('loff',"),
    ('三列栅格', '#ctlBody{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))'),
    ('窄屏两列', '@media (max-width:900px)'),
    ('手机两行', '#ctl input[type=range]{order:3;flex:1 1 100%;width:100%}'),
    ('hidden 兜底', '#ctl[hidden]{display:none}'),
]
print('\n--- 结构断言 ---')
for label, needle in checks:
    n = src.count(needle)
    ok = n >= 1
    print('  %-12s %s  (%d)' % (label, 'OK  ' if ok else 'FAIL', n))
    if not ok:
        fails.append(('assert:' + label, needle))

# 3) 反例：旧写法必须已消失
must_gone = [
    'lens.position.set(0, AY, 0);\n    S.add(lens);\n    S.label(\'凸透镜\'',
    'var inLens = function (yy, zz) { return yy * yy + zz * zz',
    'coneG.add(S.beam(tip, new V(0, 0, 0), 0xff7043, 0.006));',
    'new V(0, 0, 0), new V(pImgX, pImgY, pImgZ), 0xffd54f, 0.006)',
]
print('\n--- 旧写法残留检查（应为 0） ---')
for s in must_gone:
    n = src.count(s)
    print('  %s  (%d)  %s' % (('OK  ' if n == 0 else 'FAIL'), n, s[:60].replace('\n', '\\n')))
    if n:
        fails.append(('gone:' + s[:40], s))

print('\n===== %s =====' % ('ALL PASS' if not fails else 'FAIL: %d' % len(fails)))
for f in fails:
    print(f)
sys.exit(1 if fails else 0)
