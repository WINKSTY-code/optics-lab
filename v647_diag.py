# -*- coding: utf-8 -*-
"""诊断：母文件里的旧字面量 vs 我的重编码，逐字符找差异。"""
import io
import json

BS = chr(92)
DIR = r'C:\Users\Administrator\Desktop\AI光学参赛'
s = io.open(DIR + BS + '光学交互实验室_AI_v6.4.6.html', encoding='utf-8').read()
KEY = 'window.__S3D_LENS__ = "'
lines = s.split('\n')
li = [i for i, l in enumerate(lines) if l.startswith(KEY)][0]
old_lit = lines[li][len('window.__S3D_LENS__ = '):-1]
val = json.loads(old_lit)


def enc(v):
    t = json.dumps(v, ensure_ascii=False)
    t = t.replace('</', '<' + BS + '/')
    t = t.replace('\u2028', BS + 'u2028').replace('\u2029', BS + 'u2029')
    return t


new = enc(val)
print('old %d  new %d  diff %d' % (len(old_lit), len(new), len(new) - len(old_lit)))
n = 0
i = j = 0
while i < len(old_lit) and j < len(new) and n < 12:
    if old_lit[i] == new[j]:
        i += 1
        j += 1
        continue
    print('--- diff #%d  old@%d=%r   new@%d=%r' % (n + 1, i, old_lit[i:i + 24], j, new[j:j + 24]))
    print('    ctx old: %r' % old_lit[max(0, i - 50):i + 10])
    n += 1
    # 尝试对齐：猜是 new 多了 1 个字符
    if new[j:j + 2] == BS + 'u' or new[j:j + 2] == BS + '/':
        j += 2
        # 找到 old 对应位置
        continue
    i += 1
print('总差异段数（前 12 段）')
# 统计各类转义条数
for pat, tag in [(BS + 'u2028', 'u2028'), (BS + '/', 'slash'), (BS + 'u003c', 'u003c'), (BS + 'n', 'n')]:
    print('  %-8s old=%d new=%d' % (tag, old_lit.count(pat), new.count(pat)))
print('原始 < 个数 old=%d new=%d' % (old_lit.count('<'), new.count('<')))
