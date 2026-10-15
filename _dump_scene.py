# -*- coding: utf-8 -*-
"""导出块[3]（凸透镜场景脚本）供阅读与修改"""
import re

P = r"C:\Users\Administrator\Desktop\AI光学参赛\_lens_current.js"
OUT = r"C:\Users\Administrator\Desktop\AI光学参赛\_lens_scene.js"
s = open(P, encoding="utf-8").read()
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
open(OUT, "w", encoding="utf-8").write(blocks[3])
print("导出块[3]:", len(blocks[3]), "chars")
