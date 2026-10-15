# -*- coding: utf-8 -*-
"""
把桌面的独立作品「路灯下的影子间距 3D演示.html」改造成【可被主作品内嵌】的版本。

为什么用「文本补丁」而不是重新组装：
  该演示自带一整套设计系统（:root 变量、html/body overflow、#gl 定位、四块面板、
  移动端断点），重新组装等于重写它；补丁式改造把改动压到最小、可审查、可复现。

改造清单（四类）：
  1. <body> 加 class="embed"  → 嵌入态样式与布局的钩子
  2. </style> 前插入「嵌入模式」样式：
     · 隐藏场景自带的全屏按钮（全屏交给父页，父页全屏的是整个 3D 框）
     · 底部控制条右侧让出 178px 给父页悬浮在右下角的「2D / 3D案例」切换条
     · 右侧读数卡可滚动（矮箱体里不被裁掉）
     · 窄箱体（手机 / 窄列）收起图表与参数，并整体抬高控制条
  3. 主循环与生命周期：加 RUN/setRunning，父页 s3d:active=false 时真正停掉 rAF
     （同源 srcdoc 的 iframe 不在浏览器「隐藏 iframe 节流」范围内，切走后仍满速渲染）
  4. 与父页的消息协议（与既有 refl/lens/mirror/pinhole 四个场景完全同口径）：
     父 → 子  {t:'s3d:init', params} / {t:'s3d:active', on}
     子 → 父  {t:'s3d:ready'|'s3d:lost'|'s3d:error'|'s3d:state', key}
  5. 取景避让：freeCenter() 额外把右下角（父页切换条位置）算作已占用

产出：shadow3d.html（独立可双击打开，也是内嵌用的那份源码）
"""
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\Administrator\Desktop\路灯下的影子间距 3D演示.html"
DST = os.path.join(BASE, "shadow3d.html")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


# ---------------------------------------------------------------- 嵌入模式样式
# 断点取 900px：桌面端主作品左列为 946px（宽箱体），手机端为 370px（窄箱体）。
# 所有规则一律带 body.embed 前缀 —— 其特指度高于场景自身的 #id 规则，
# 因此在同一断点内一定压得住原样式，布局不依赖两条媒体查询的先后。
EMBED_CSS = """
/* ==========================================================================
   嵌入模式（body.embed）—— 本场景被主作品以 iframe + srcdoc 承载时启用
   · 自带的全屏按钮交给父页（父页把整个 3D 框全屏），这里隐藏；
   · 父页的「2D / 3D案例」切换条悬浮在本场景右下角，底部控制条为此让出右侧；
   · 读数卡限高可滚动，矮箱体里也不会被裁掉关键读数。
   ========================================================================== */
body.embed #btnFull{display:none !important;}

/* ---- 宽箱体（>900px，桌面左列约 946px）---- */
body.embed #dock{left:10px;right:178px;transform:none;max-width:none;}
body.embed #dock #time{min-width:96px;}
body.embed #hud{max-height:calc(100% - 84px);overflow-y:auto;overscroll-behavior:contain;}

/* ---- 窄箱体（<=900px，手机 / 窄列）----
   收起图表与逐行读数，读数卡只保留 d / 趋势 / 参数调节；
   控制条改用两行网格并整体抬高 46px，把右下角完整让给父页切换条。 */
@media (max-width:900px){
  body.embed #topbar{padding:7px 9px;gap:6px;left:10px;top:10px;}
  body.embed #topbar h1{font-size:12px;}
  body.embed #topbar h1 span{display:none;}

  body.embed #hud{right:10px;top:54px;width:172px;padding:9px 10px;
                  max-height:calc(100% - 232px);overflow-y:auto;overscroll-behavior:contain;}
  body.embed #hud .rows{display:none;}
  body.embed #hud .opt-row{display:none;}
  body.embed #hud .sec{display:block;}
  body.embed #hud .fold{display:none;}
  body.embed #fold-params{display:block !important;}
  body.embed #dVal{font-size:26px;}
  body.embed #dUnit{font-size:10.5px;}

  body.embed #chartCard{display:none;}

  body.embed #dock{left:10px;right:10px;bottom:46px;transform:none;max-width:none;
    display:grid;grid-template-columns:auto 1fr auto;gap:6px 8px;align-items:center;
    padding:8px 10px;width:auto;}
  body.embed #dock .dock-sep{display:none;}
  body.embed #dock .chips{grid-column:1/-1;display:flex;justify-content:center;flex-wrap:wrap;gap:6px;}
  body.embed #dock #time{min-width:0;width:100%;}
  body.embed #dock .chip,body.embed #dock .btn{font-size:11px;padding:4px 9px;height:26px;}

  body.embed .lab{font-size:11.5px;}
  body.embed .lab.dval{font-size:13px;}
}
"""

# ------------------------------------------------------------ 协议与生命周期
PROTO_TOP = """
/* ---------------- 0.5 嵌入协议（与主作品 s3d:* 同口径） ----------------
   父 → 子  {t:'s3d:init', params}   进 3D 时同步一次（本场景参数独立，仅回执）
            {t:'s3d:active', on}     父页切走 / 切回 —— 真正停掉 rAF 省电
   子 → 父  {t:'s3d:ready', key}     场景就绪 / 上下文已恢复
            {t:'s3d:lost',  key}      渲染上下文丢失（父页会重置挂载）
            {t:'s3d:error', key, msg} 出错（父页会退回 2D）
            {t:'s3d:state', key, params}
   离线 file:// 下 origin 为 null，故不做 origin 校验，只严格校验消息形状。 */
var S3D_KEY = 'shadow';
function post(m){ try { (window.parent || window).postMessage(m, '*'); } catch(e){} }
"""

RUN_BLOCK = """var last = performance.now(), chartTick = 0, viewTick = 0, holdPend = false, holdUntil = 0;

/* ★ 嵌入协议：父页切走时真正停掉 rAF。
   同源 srcdoc 的 iframe 不在浏览器「隐藏 iframe 节流」范围内，
   只把容器藏起来的话，切走后仍在满速渲染。 */
var RUN = { on: true, raf: 0 };
function setRunning(on){
  on = !!on;
  if (on === RUN.on) return;
  RUN.on = on;
  if (on){ last = performance.now(); if (!RUN.raf) RUN.raf = requestAnimationFrame(loop); }
  else { if (RUN.raf) cancelAnimationFrame(RUN.raf); RUN.raf = 0; }
}

function loop(now){
  if (!RUN.on){ RUN.raf = 0; return; }
  RUN.raf = requestAnimationFrame(loop);
"""

PROTO_TAIL = """

/* ---------------- 15. 与父页的消息协议 ---------------- */
window.addEventListener('message', function(e){
  var m = e && e.data;
  if (!m || typeof m !== 'object' || typeof m.t !== 'string') return;
  if (m.t === 's3d:active'){ setRunning(m.on !== false); return; }
  if (m.t === 's3d:init'){
    /* 本场景的参数（灯高 / 两人身高 / 间距）与父页 2D「影子形成」的
       （物距 / 物体位置）不是同一套，故不做参数同步，只回执一次状态。 */
    post({ t:'s3d:state', key:S3D_KEY, params:{} });
  }
});
post({ t:'s3d:ready', key:S3D_KEY });
"""


def main():
    s = open(SRC, encoding="utf-8").read()
    n_open0 = len(re.findall(r"<script", s))
    n_close0 = len(re.findall(r"</script(?=[\s>/])", s))
    size0 = os.path.getsize(SRC)

    # 1. body 加 embed 类
    s = rep(s, "<body>\n", '<body class="embed">\n', 1, "body.embed")

    # 2. 嵌入模式样式
    s = rep(s, "</style>\n</head>", EMBED_CSS + "</style>\n</head>", 1, "嵌入模式样式")

    # 3. 协议常量（放在 'use strict'; 之后，post 为函数声明会提升）
    s = rep(s, "'use strict';\n", "'use strict';\n" + PROTO_TOP, 1, "协议常量 post()/S3D_KEY")

    # 4. 错误处理器同时通报父页
    s = rep(
        s,
        "  d.textContent = 'ERROR: ' + (e.message||'') + '\\n' + (e.filename||'') + ':' + (e.lineno||'');\n});",
        "  d.textContent = 'ERROR: ' + (e.message||'') + '\\n' + (e.filename||'') + ':' + (e.lineno||'');\n"
        "  post({ t:'s3d:error', key:S3D_KEY, msg:String(e.message||'') });\n});",
        1,
        "错误处理器通报父页",
    )

    # 5. 渲染上下文丢失 / 恢复
    s = rep(
        s,
        "if (THREE.sRGBEncoding !== undefined) renderer.outputEncoding = THREE.sRGBEncoding;",
        "if (THREE.sRGBEncoding !== undefined) renderer.outputEncoding = THREE.sRGBEncoding;\n\n"
        "/* 上下文丢失：先自愈，同时通报父页（父页会重置挂载，便于重新进入） */\n"
        "canvas.addEventListener('webglcontextlost', function(e){\n"
        "  e.preventDefault(); setRunning(false);\n"
        "  post({ t:'s3d:lost', key:S3D_KEY });\n"
        "});\n"
        "canvas.addEventListener('webglcontextrestored', function(){\n"
        "  setRunning(true); post({ t:'s3d:ready', key:S3D_KEY });\n"
        "});",
        1,
        "webgl 上下文丢失/恢复",
    )

    # 6. 主循环加 RUN 守卫
    s = rep(
        s,
        "var last = performance.now(), chartTick = 0, viewTick = 0, holdPend = false, holdUntil = 0;\n"
        "function loop(now){\n  requestAnimationFrame(loop);\n",
        RUN_BLOCK,
        1,
        "主循环 RUN 守卫 + setRunning",
    )

    # 6.5 测试钩子：把「当前是否在跑 rAF」暴露出去，供 e2e 硬断言
    s = rep(
        s,
        "  seek:function(p){ S.p = Math.max(0, Math.min(1, p)); S.playing = false; holdPend = false; elPlay.textContent='▶'; updateScene(performance.now()); drawChart(); },",
        "  seek:function(p){ S.p = Math.max(0, Math.min(1, p)); S.playing = false; holdPend = false; elPlay.textContent='▶'; updateScene(performance.now()); drawChart(); },\n"
        "  run:function(){ return RUN.on; },",
        1,
        "__demo.run 测试钩子",
    )

    # 7. 启动的首帧也登记 rafId
    s = rep(s, "resize();\nrequestAnimationFrame(loop);", "resize();\nRUN.raf = requestAnimationFrame(loop);", 1, "启动登记 rafId")

    # 8. 取景避让：右下角算作已占用
    s = rep(
        s,
        "  var ids = ['topbar','hud','chartCard','dock','drawer'];\n"
        "  for (i=0;i<ids.length;i++){\n"
        "    var el = document.getElementById(ids[i]); if (!el) continue;\n"
        "    var r = el.getBoundingClientRect();\n"
        "    if (r.width <= 0 || r.height <= 0) continue;\n"
        "    var x0 = Math.max(0, Math.floor(r.left/W*NX)), x1 = Math.min(NX, Math.ceil(r.right/W*NX));\n"
        "    var y0 = Math.max(0, Math.floor(r.top/H*NY)),  y1 = Math.min(NY, Math.ceil(r.bottom/H*NY));\n"
        "    for (var y=y0;y<y1;y++) for (var x=x0;x<x1;x++) occ[y*NX+x] = 1;\n"
        "  }",
        "  var ids = ['topbar','hud','chartCard','dock','drawer'];\n"
        "  var boxes = [];\n"
        "  for (i=0;i<ids.length;i++){\n"
        "    var el = document.getElementById(ids[i]); if (!el) continue;\n"
        "    var r = el.getBoundingClientRect();\n"
        "    if (r.width <= 0 || r.height <= 0) continue;\n"
        "    boxes.push(r);\n"
        "  }\n"
        "  /* 嵌入模式：父页的「2D / 3D案例」切换条悬浮在右下角，取景时一并避开 */\n"
        "  if (document.body.classList.contains('embed'))\n"
        "    boxes.push({left:W-196, top:H-62, right:W, bottom:H});\n"
        "  for (i=0;i<boxes.length;i++){\n"
        "    var r2 = boxes[i];\n"
        "    var x0 = Math.max(0, Math.floor(r2.left/W*NX)), x1 = Math.min(NX, Math.ceil(r2.right/W*NX));\n"
        "    var y0 = Math.max(0, Math.floor(r2.top/H*NY)),  y1 = Math.min(NY, Math.ceil(r2.bottom/H*NY));\n"
        "    for (var y=y0;y<y1;y++) for (var x=x0;x<x1;x++) occ[y*NX+x] = 1;\n"
        "  }",
        1,
        "取景避让右下角",
    )

    # 9. 尾部协议块
    s = rep(
        s,
        "                 freeCenter:freeCenter, actionBox:actionBox, viewOff:viewOff, cam:cam, follow:follow };\n})();",
        "                 freeCenter:freeCenter, actionBox:actionBox, viewOff:viewOff, cam:cam, follow:follow };"
        + PROTO_TAIL
        + "})();",
        1,
        "尾部消息协议块",
    )

    # ------------------------------------------------------------ 组装硬校验
    n_open1 = len(re.findall(r"<script", s))
    n_close1 = len(re.findall(r"</script(?=[\s>/])", s))
    assert n_open1 == n_open0, "脚本开标签数变了：%d -> %d" % (n_open0, n_open1)
    assert n_close1 == n_close0, "脚本收尾标签字面量数变了：%d -> %d" % (n_close0, n_close1)
    LOG.append("OK  %-46s %d/%d（前后不变）" % ("脚本标签计数", n_open1, n_close1))

    blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
    assert len(blocks) == 2, "脚本块 %d 个，应为 2" % len(blocks)
    assert 'post({ t:' in blocks[1] and 'setRunning' in blocks[1], "协议代码没进第 2 个脚本块"

    # 拆块语法自检
    for i, b in enumerate(blocks):
        p = os.path.join(BASE, "_chk_s3d_shadow_%d.js" % i)
        open(p, "w", encoding="utf-8", newline="\n").write(b)
        r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
        assert r.returncode == 0, "[JS FAIL] block %d: %s" % (i, r.stderr[:500])
        LOG.append("OK  %-46s block%d" % ("node --check", i))

    open(DST, "w", encoding="utf-8", newline="\n").write(s)
    n1 = os.path.getsize(DST)
    print("\n".join(LOG))
    print("\n源 %s (%d B)\n产物 %s (%d B, %+d B)"
          % (os.path.basename(SRC), size0, os.path.basename(DST), n1, n1 - size0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
