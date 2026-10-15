# -*- coding: utf-8 -*-
"""从最终产物反解 __S3D_LENS__，与 _lens_scene_new.js 逐字比对"""
import re, json

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
DST = BASE + r"\光学交互实验室_AI_v6.4.1.html"
NEW_SCENE = BASE + r"\_lens_scene_new.js"

s = open(DST, encoding="utf-8").read()
pat = re.compile(r'window\.__S3D_LENS__\s*=\s*("(?:[^"\\]|\\.)*")', re.S)
m = pat.search(s)
assert m, "产物中未找到 __S3D_LENS__"
inner = json.loads(m.group(1))
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", inner, re.S)
assert len(blocks) == 4, "内嵌块数 %d" % len(blocks)
new_scene = open(NEW_SCENE, encoding="utf-8").read().replace("\r\n", "\n").strip()
assert blocks[3].strip() == new_scene, "产物块[3]与新场景脚本不一致"
assert 'oy = S.px(v, -4, 4)' in blocks[3] and "label: '物体左右'" in blocks[3], "关键改动缺失"
print("产物反解验证通过：块[3] 与新场景逐字一致（%d chars）" % len(blocks[3]))

# 版本号与日志抽查
assert s.count("v6.4.1") >= 3, "版本号出现次数不足"
assert "凸透镜3D实验实现物体三维全方向移动" in s, "V6.4.1 日志缺失"
for t in ["顶栏窄屏不折行", "修3D切页冻结", "反射3D新增光路可逆开关", "新增通用数据记录器自动落表"]:
    assert t in s, "精简日志缺失: " + t
print("版本号/日志抽查通过")
