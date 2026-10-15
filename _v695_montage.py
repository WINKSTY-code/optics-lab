# -*- coding: utf-8 -*-
"""把 3 张证据图拼成 1 张（§59⑤：上传次数与 token 手抄次数都 3→1）。"""
from PIL import Image, ImageDraw, ImageFont

FILES = [("_v695_证据_anthropic_haiku55.png", "AI 设置 · Provider=Anthropic · 模型=claude-haiku-5.5（中文）"),
         ("_v695_证据_anthropic_zht.png",     "繁體：claude-haiku-5.5"),
         ("_v695_证据_anthropic_en.png",     "English: claude-haiku-5.5"),
         ("_v695_证据_更新日志.png",          "更新日志首条 V6.9.5（关于 → 更新日志）")]

imgs = [(f, t, Image.open(f).convert("RGB")) for f, t in FILES]
H = sum(im.height for _, _, im in imgs) + 34 * len(imgs) + 16
W = max(im.width for _, _, im in imgs) + 16
canvas = Image.new("RGB", (W, H), (247, 245, 240))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
except Exception:
    font = ImageFont.load_default()

y = 8
for f, t, im in imgs:
    d.rectangle([6, y, W - 6, y + 26], fill=(228, 234, 244))
    d.text((12, y + 4), t, fill=(30, 41, 59), font=font)
    y += 34
    canvas.paste(im, (8, y))
    y += im.height + 8

OUT = "自检_V695_新增claude-haiku-5.5.png"
canvas.save(OUT)
print(OUT, canvas.size)
