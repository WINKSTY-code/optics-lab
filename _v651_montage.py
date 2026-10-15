# -*- coding: utf-8 -*-
"""把 3 张证据图拼成一张「自检_AI设置新增模型与更新日志_V651.png」
（顺带减少上传次数：同批次票据的 x-cos-security-token 在多数票据里逐字相同，合并后只需抄一次）"""
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/Administrator/Desktop/AI光学参赛/"
shots = [("_v651_证据_openai_gpt-6-luna.png", "OpenAI · 选中 gpt-6-luna"),
         ("_v651_证据_anthropic_opus-5.5.png", "Anthropic · 选中 claude-opus-5.5"),
         ("_v651_证据_更新日志.png", "更新日志：V6.5.1 / 2026-09-23 · 新增模型支持。")]

imgs = [(Image.open(BASE + f).convert("RGB"), cap) for f, cap in shots]

PAD, GAP, TITLE = 14, 12, 26
w = PAD * 2 + imgs[0][0].width + imgs[1][0].width + GAP
h = PAD * 2 + TITLE + max(imgs[0][0].height, imgs[1][0].height) + GAP + TITLE + imgs[2][0].height
canvas = Image.new("RGB", (w, h), (247, 246, 243))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 17)
except Exception:
    font = ImageFont.load_default()

y = PAD
for i, (im, cap) in enumerate(imgs):
    if i == 2:
        y += TITLE + GAP
    d.text((PAD, y), cap, fill=(30, 30, 30), font=font)
    x = PAD if i < 2 else PAD
    if i == 2:
        # 第三张（更新日志）宽度较小，居中放到画布中
        x = (w - im.width) // 2
    canvas.paste(im, (x, y + TITLE))
    if i < 2:
        y2 = y
    if i == 0:
        y = y2  # 第一行保持
# 上面循环对第一行处理不够直观，这里直接重排一次（更清晰）
canvas = Image.new("RGB", (w, h), (247, 246, 243))
d = ImageDraw.Draw(canvas)
y1 = PAD
d.text((PAD, y1), imgs[0][1], fill=(30, 30, 30), font=font)
canvas.paste(imgs[0][0], (PAD, y1 + TITLE))
x2 = PAD + imgs[0][0].width + GAP
d.text((x2, y1), imgs[1][1], fill=(30, 30, 30), font=font)
canvas.paste(imgs[1][0], (x2, y1 + TITLE))
y2 = y1 + TITLE + max(imgs[0][0].height, imgs[1][0].height) + GAP
d.text((PAD, y2), imgs[2][1], fill=(30, 30, 30), font=font)
canvas.paste(imgs[2][0], ((w - imgs[2][0].width) // 2, y2 + TITLE))

out = BASE + "自检_AI设置新增模型与更新日志_V651.png"
canvas.save(out, optimize=True)
import os
print("saved", out, os.path.getsize(out), "B", canvas.size)
