# -*- coding: utf-8 -*-
"""从 v6.4.0 大文件提取 __S3D_LENS__ 当前源码"""
import re, json

SRC = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.0.html"
OUT = r"C:\Users\Administrator\Desktop\AI光学参赛\_lens_current.js"

s = open(SRC, encoding="utf-8").read()

pat = re.compile(r'window\.__S3D_LENS__\s*=\s*("(?:[^"\\]|\\.)*")', re.S)
m = pat.search(s)
assert m, "未找到 __S3D_LENS__"
esc = m.group(1)
raw = json.loads(esc)
bs_tag = "<" + chr(92) + "/script"   # <\/script
assert esc.count(bs_tag) == raw.count("</script"), "转义口径不一致"
# round-trip 自证
re_esc = json.dumps(raw, ensure_ascii=False)
assert json.loads(re_esc) == raw, "round-trip 失败"
open(OUT, "w", encoding="utf-8").write(raw)
print("提取成功:", len(raw), "chars /", len(esc.encode("utf-8")), "B escaped")
