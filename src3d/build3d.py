# -*- coding: utf-8 -*-
"""
把「3D 场景外壳 + three.js + 场景脚本」组装成独立的单文件 3D 场景 HTML。

为什么要独立成文件再组装：
  1. 每个 3D 场景先当【独立作品】开发与验证（打开即用、可单独截图与迭代），
     再接进 4.8 MB 的大文件 —— 大文件里的调试成本高一个数量级；
  2. 组装时做「脚本收尾标签字面量」硬校验：V5.2.0 踩过该字面量出现在注释里
     导致整页脚本链断裂、而 node --check 全绿的坑（见 single-file-html-safe-patch 技能）。
"""
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#04060e">
<title>__TITLE__</title>
<style>
__CSS__
</style>
</head>
<body>
<canvas id="gl" role="img" aria-label="三维光路图"></canvas>
<div id="labels" aria-hidden="true"></div>
<header id="hud">
  <span class="chip"><i></i><span id="chip">光现象 · 3D 立体模型</span></span>
  <h1 id="ttl"></h1>
  <p class="sub" id="sub"></p>
</header>
<div id="ro" hidden>
  <h2 id="roTitle">实时读数</h2>
  <div id="roBody"></div>
</div>
<div id="tools" role="group" aria-label="视角控制"></div>
<footer id="ctl"><div id="ctlBody"></div></footer>
<div id="toast" role="status" aria-live="polite"></div>
<div id="boot"><div class="in"><div class="orb"></div><p id="bootTxt">正在构建三维光路</p></div></div>
<script>
__THREE__
</script>
<script>
__ORBIT__
</script>
<script>
__SHELL_JS__
</script>
<script>
__SCENE__
</script>
</body>
</html>
"""

SCENES = [
    ("refl", "光的反射 · 可折转纸板", "3D_光的反射_可折转纸板.html", "scene_refl.js"),
    ("lens", "凸透镜成像", "3D_凸透镜成像.html", "scene_lens.js"),
    ("mirror", "平面镜成像 · 棋子", "3D_平面镜成像_棋子.html", "scene_mirror.js"),
]


def read(p):
    return open(os.path.join(BASE, p), encoding="utf-8").read()


def node_check(name, code):
    p = os.path.join(BASE, "_chk_%s.js" % name)
    open(p, "w", encoding="utf-8", newline="\n").write(code)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        print("[JS FAIL] %s: %s" % (name, r.stderr[:500]))
        return False
    return True


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    css = read("shell.css")
    shelljs = read("shell.js")
    three = read("three.min.js")
    orbit = read("OrbitControls.js")
    ok = node_check("shell", shelljs)

    for key, title, outname, scenefile in SCENES:
        if only and only != key:
            continue
        scene = read(scenefile)
        ok = node_check("scene_" + key, scene) and ok
        html = (SHELL
                .replace("__TITLE__", title + " · 三维光路")
                .replace("__CSS__", css)
                .replace("__THREE__", three)
                .replace("__ORBIT__", orbit)
                .replace("__SHELL_JS__", shelljs)
                .replace("__SCENE__", scene))
        # 组装后的硬校验
        assert "<!--" not in html, "%s 含 <!--" % outname
        lit = len(re.findall(r"</script(?=[\s>/])", html))
        assert lit == 4, "%s 脚本收尾标签字面量 %d 个，应为 4" % (outname, lit)
        # 反向校验：把每段 script 内容抽出来，确认没有被提前闭合
        blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
        assert len(blocks) == 4, "%s 脚本块 %d 个，应为 4" % (outname, len(blocks))
        assert blocks[3] == "\n" + scene + "\n", "场景脚本被截断"
        assert blocks[0] == "\n" + three + "\n", "three.js 被截断"
        assert blocks[1] == "\n" + orbit + "\n", "OrbitControls 被截断"
        outp = os.path.join(BASE, outname)
        open(outp, "w", encoding="utf-8", newline="\n").write(html)
        print("OK  %-34s %8d B  (three %d + orbit %d + shell %d + scene %d)"
              % (outname, len(html.encode()), len(three), len(orbit), len(shelljs), len(scene)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
