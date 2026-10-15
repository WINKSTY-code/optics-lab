# -*- coding: utf-8 -*-
"""V6.4.7 打补丁：把改好的 3D 凸透镜场景重新编码嵌入母文件，并同步版本号 / 更新日志。

要点：
  · 场景以 window.__S3D_LENS__ = "<html...>" 的 JS 字符串字面量内联，整条语句占一行；
    重新编码用 json.dumps（ensure_ascii=False）+ 把 </ 转义成 <\\/ + 转义 U+2028/9。
  · 先用母文件里的旧字面量做「解码→重编码」往返校验，字节一致才允许往下走
    （证明本次编码器与上一版产物同源，不会引入转义差异）。
"""
import io
import json
import os
import sys

BS = chr(92)
DIR = r'C:\Users\Administrator\Desktop\AI光学参赛'
SRC = os.path.join(DIR, '光学交互实验室_AI_v6.4.6.html')
NEW_SCENE = os.path.join(DIR, '_extract_v646_lens.html')
DST = os.path.join(DIR, '光学交互实验室_AI_v6.4.7.html')

KEY = 'window.__S3D_LENS__ = "'
fails = []


def rep(s, old, new, n=1, tag=''):
    c = s.count(old)
    if c != n:
        fails.append('%s 期望 %d 处，实际 %d 处：%s' % (tag, n, c, old[:70].replace('\n', '|')))
        return s
    print('  [ok] %-22s x%d' % (tag, c))
    return s.replace(old, new)


def enc(v):
    t = json.dumps(v, ensure_ascii=False)
    # 只需转义 </script —— 这正是 HTML 解析器在 script 数据里唯一会提前收尾的序列。
    # （实测旧产物也是只转义这一处：其它 </div>、</style> 都原样保留，
    #   全量转义 </ 会让字面量长度差 50 字符，破坏字节级往返校验。）
    t = t.replace('</script', '<' + BS + '/script')
    t = t.replace('\u2028', BS + 'u2028').replace('\u2029', BS + 'u2029')
    return t


s = io.open(SRC, encoding='utf-8').read()
scene = io.open(NEW_SCENE, encoding='utf-8').read()
print('源文件 %d 字节；新场景 %d 字节' % (len(s), len(scene)))

# ---------- 1. 往返校验 ----------
lines = s.split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, '找不到唯一的 __S3D_LENS__ 行：%s' % hit
li = hit[0]
raw = lines[li][len('window.__S3D_LENS__ = '):]
assert raw.endswith('";'), '字面量未以 "; 结尾：%r' % raw[-12:]
old_lit = raw[:-1]
old_html = json.loads(old_lit)
rt = enc(old_html)
if rt != old_lit:
    print('!! 往返不一致，长度 %d vs %d' % (len(rt), len(old_lit)))
    fails.append('encode round-trip')
else:
    print('  [ok] 旧字面量 解码→重编码 字节一致（%d 字符）' % len(old_lit))

# ---------- 2. 替换场景 ----------
new_lit = enc(scene)
assert len(new_lit) > 100000
assert json.loads(new_lit) == scene, '新字面量解码后与场景文件不一致'
print('  [ok] 场景字面量替换完成（%d → %d 字符）' % (len(old_lit), len(new_lit)))

# ---------- 2.5 危险序列体检 ----------
for tok in ('<!--', '<script'):
    print('     %-8s 旧场景 %d 处 / 新场景 %d 处' % (tok, old_html.count(tok), scene.count(tok)))
assert scene.count('<script') == old_html.count('<script'), 'script 标签数变化'

lines[li] = 'window.__S3D_LENS__ = ' + new_lit + ';'
s2 = '\n'.join(lines)

# ---------- 3. 版本号同步 ----------
s2 = rep(s2, "var BUILD = 'v6.4.6', MAX_SHOW = 3", "var BUILD = 'v6.4.7', MAX_SHOW = 3", tag='BUILD')
s2 = rep(s2, "return 'v6.4.6';", "return 'v6.4.7';", tag='RPT_BUILD')
s2 = rep(
    s2,
    '<div class="ver-badge" title="光学交互实验室 V6.4.6 · 小孔成像加物距调节，顶栏按钮并入设置。">v6.4.6</div>',
    '<div class="ver-badge" title="光学交互实验室 V6.4.7 · 凸透镜3D可移透镜，底栏一行三个。">v6.4.7</div>',
    tag='ver-badge')

OLD_LOG = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.6</span>'
           '<span class="log-date">2026-09-18</span></div>\n'
           '        <p>小孔成像加物距调节，顶栏按钮并入设置。</p>\n'
           '      </div>')
NEW_LOG = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.7</span>'
           '<span class="log-date">2026-09-18</span></div>\n'
           '        <p>凸透镜3D可移动透镜，底栏一行三个。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.6</span>'
           '<span class="log-date">2026-09-18</span></div>\n'
           '        <p>小孔成像加物距调节，顶栏按钮并入设置。</p>\n'
           '      </div>')
s2 = rep(s2, OLD_LOG, NEW_LOG, tag='changelog')

if fails:
    print('\n!! 中止：%s' % fails)
    sys.exit(1)

io.open(DST, 'w', encoding='utf-8', newline='').write(s2)
print('\n已写出 %s  (%d 字节, 原 %d 字节)' % (os.path.basename(DST), len(s2), len(s)))
print('  行数 %d，log-item %d 条' % (s2.count('\n') + 1, s2.count('class="log-item')))
