# -*- coding: utf-8 -*-
"""把 V6.5.2 的三张证据图拼成一张（减少票据手抄次数，也便于阅读）"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, "_chk652")
OUT = os.path.join(D, "自检_V652_模型与更新日志.png")

font_t = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 26)
font_s = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
font_c = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 17)

cfg = Image.open(os.path.join(D, "cfg_minimax.png"))
sel = Image.open(os.path.join(D, "model_select.png"))
log = Image.open(os.path.join(D, "changelog.png"))
print("尺寸 cfg", cfg.size, "sel", sel.size, "log", log.size)

PAD, GAP = 26, 20
head_h = 74
lab_h = 30

# 缩放：日志图很高，按 0.62 缩
lw = int(log.width * 0.62); lh = int(log.height * 0.62)
log2 = log.resize((lw, lh), Image.LANCZOS)
cw, ch = cfg.width, cfg.height
left_w = max(cw, sel.width + 30)

body_w = max(left_w, lw)
left_h = ch + 14 + sel.height
body_h = max(left_h, lh)

W = PAD * 2 + body_w + GAP + lw
H = head_h + lab_h + body_h + 34 + PAD

canvas = Image.new("RGB", (W, H), (245, 246, 248))
d = ImageDraw.Draw(canvas)
d.rectangle([0, 0, W, head_h - 8], fill=(31, 41, 55))
d.text((PAD, 14), "V6.5.2 自检证据 · AI 设置新增模型支持 MiniMax-M3.1-Flash-Preview", font=font_t, fill=(255, 255, 255))
d.text((PAD, 46), "2026-09-29 · 光学交互实验室 v6.5.1 → v6.5.2 · 真实 Chromium（file:// 离线通道）", font=font_s, fill=(186, 199, 214))

y = head_h
x1 = PAD
d.text((x1, y), "① AI 设置 · MiniMax 模型下拉（新增条目已可选）", font=font_s, fill=(30, 41, 59))
y2 = y + lab_h
canvas.paste(cfg, (x1, y2))
canvas.paste(sel, (x1, y2 + ch + 14))

x2 = x1 + left_w + GAP
d.text((x2, y), "② 更新日志（首条 V6.5.2 · cur）", font=font_s, fill=(30, 41, 59))
canvas.paste(log2, (x2, y2))

# 底部说明
d.rectangle([0, H - 34, W, H], fill=(230, 233, 238))
d.text((PAD, H - 29), "下拉完整选项：MiniMax-M3（旗舰） → MiniMax-M3.1-Flash-Preview → MiniMax-M2.7 → — 自定义 —", font=font_c, fill=(55, 65, 81))

canvas.save(OUT)
print("已保存:", OUT, canvas.size, os.path.getsize(OUT), "B")
