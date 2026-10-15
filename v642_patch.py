# -*- coding: utf-8 -*-
"""V6.4.2 补丁：光屏固定不再随像侧移 + 屏面加大，像在屏平面内反向移动。
先提取 __S3D_LENS__ 反解 → 在 inner 上改场景 → 转义注入 → 版本号/日志。"""
import re, json, os, subprocess, sys

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
SRC = BASE + r"\光学交互实验室_AI_v6.4.1.html"
DST = BASE + r"\光学交互实验室_AI_v6.4.2.html"
LOG = []

s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)

def rep(txt, old, new, n=1, label=""):
    c = txt.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %s  x%d" % (label, c))
    return txt.replace(old, new)

# ---------- 1) 提取内嵌 HTML 并反解 ----------
pat_str = re.compile(r'window\.__S3D_LENS__\s*=\s*("(?:[^"\\]|\\.)*")', re.S)
m = pat_str.search(s)
assert m, "未找到 __S3D_LENS__"
inner = json.loads(m.group(1))
pat_blk = re.compile(r"(<script[^>]*>)(.*?)(</script(?=[\s>/]))", re.S)
blocks = list(pat_blk.finditer(inner))
assert len(blocks) == 4, "内嵌块数 %d" % len(blocks)
scene0 = blocks[3].group(2)

# ---------- 2) 场景内替换 ----------
scene = scene0
scene = rep(scene,
"""    /* 光屏：物侧偏后像也侧偏（z 向 -m 倍），把光屏沿 z 平移到像所在的平面才能接到像
       —— 真实光具座上就是"把屏挪到像的位置"；上下方向像若超出屏面则提示屏太小。 */
    var xScr = real ? sxf(vShow) : RAIL_R;
    var zScr = real ? -m * zTip : 0;
    screenG.visible = real;
    screenG.position.set(xScr, AY, zScr);
    S.labelVis(lb.scr, real);
    S.labelAt(lb.scr, [xScr + 0.12, AY + 1.62, zScr]);""",
"""    /* 光屏固定在光具座上（V6.4.2：不再随像侧移）—— 物左右偏移后像在屏平面内反向
       移动，屏面已加大以容纳；像偏出屏面（上下或左右）则提示屏太小。 */
    var xScr = real ? sxf(vShow) : RAIL_R;
    screenG.visible = real;
    screenG.position.set(xScr, AY, 0);
    S.labelVis(lb.scr, real);
    S.labelAt(lb.scr, [xScr + 0.12, AY + 1.62, 0]);""",
    1, "S3 光屏固定")

scene = rep(scene,
"""    else {
      var topY = yImgBase - ih;                    // 实像的像顶（最低点）
      var tooTall = (yImgBase > 1.5 || topY < -1.5);
      scrTxt = tooTall ? '像超出光屏（屏太小）' : '屏上有清晰的像';
      scrCls = tooTall ? 'no' : 'ok';
    }""",
"""    else {
      var topY = yImgBase - ih;                    // 实像的像顶（最低点）
      var out = (yImgBase > 1.5 || topY < -1.5 || Math.abs(zImg) > 1.4);   // 上下或左右偏出屏面
      scrTxt = out ? '像超出光屏（屏太小）' : '屏上有清晰的像';
      scrCls = out ? 'no' : 'ok';
    }""",
    1, "S4 超屏判定加 z 向")

scene = rep(scene,
    "    var sc = new T.Mesh(new T.PlaneGeometry(1.7, 3.0), S.MAT.matte(0xc4ccdb));",
    "    var sc = new T.Mesh(new T.PlaneGeometry(2.8, 3.0), S.MAT.matte(0xc4ccdb));",
    1, "S1 屏面加大")
scene = rep(scene, "    [-0.88, 0.88].forEach(function (z) {",
                  "    [-1.4, 1.4].forEach(function (z) {",
    1, "S2 边框跟随")

# ---------- 3) 重组 + 转义注入（lambda！） ----------
new_inner = inner[:blocks[3].start(2)] + scene + inner[blocks[3].end(2):]
nb = list(pat_blk.finditer(new_inner))
assert len(nb) == 4 and nb[3].group(2).strip() == scene.strip(), "块[3]回读不一致"
esc = json.dumps(new_inner, ensure_ascii=False).replace("</script", "<\\/script")
assert json.loads(esc) == new_inner, "转义 round-trip 失败"
pat_assign = re.compile(r'window\.__S3D_LENS__\s*=\s*"(?:[^"\\]|\\.)*";')
assert len(pat_assign.findall(s)) == 1
s = pat_assign.sub(lambda m2: "window.__S3D_LENS__ = " + esc + ";", s, count=1)
LOG.append("OK  __S3D_LENS__ 重新注入（lambda）x1")

# ---------- 4) 大文件级：版本号三处 ----------
s = rep(s, "var BUILD = 'v6.4.1', MAX_SHOW = 3", "var BUILD = 'v6.4.2', MAX_SHOW = 3", 1, "BUILD 常量")
s = rep(s, "    return 'v6.4.1';", "    return 'v6.4.2';", 1, "RPT_BUILD 兜底")
s = rep(s,
    '<div class="ver-badge" title="光学交互实验室 V6.4.1 · 凸透镜3D实验实现物体三维全方向移动">v6.4.1</div>',
    '<div class="ver-badge" title="光学交互实验室 V6.4.2 · 光屏固定不再随像侧移，屏面加大，像在屏上反向移动">v6.4.2</div>',
    1, "版本角标")

# ---------- 5) 更新日志：V6.4.2 新条目 ----------
s = rep(s,
"""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.1</span><span class="log-date">2026-09-17</span></div>
        <p>凸透镜3D实验实现物体三维全方向移动</p>
      </div>""",
"""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.2</span><span class="log-date">2026-09-17</span></div>
        <p>光屏固定不再随像侧移，屏面加大，像在屏上反向移动。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.1</span><span class="log-date">2026-09-17</span></div>
        <p>凸透镜3D实验实现物体三维全方向移动</p>
      </div>""",
    1, "日志 V6.4.2 新增")

# ---------- 6) 硬校验 + 落盘 ----------
c0, o0 = len(re.findall(r"</script(?=[\s>/])", open(SRC, encoding="utf-8").read())), len(re.findall(r"<script[^>]*>", open(SRC, encoding="utf-8").read()))
c1_, o1_ = len(re.findall(r"</script(?=[\s>/])", s)), len(re.findall(r"<script[^>]*>", s))
assert c1_ == c0 and o1_ == o0, "[FAIL] script 标签计数漂移 (%d/%d -> %d/%d)" % (c0, o0, c1_, o1_)
LOG.append("OK  script 标签计数与源一致（closes %d / opens %d）" % (c1_, o1_))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))

# ---------- 7) 拆块 node --check ----------
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
html = open(DST, encoding="utf-8").read()
blocks2 = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
os.makedirs(BASE + r"\_chk642", exist_ok=True)
bad = 0
for i, b in enumerate(blocks2):
    if len(b.strip()) < 20:
        continue
    p = BASE + r"\_chk642\blk%d.js" % i
    open(p, "w", encoding="utf-8", newline="\n").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:400]))
print("拆块检查：%d 块，失败 %d" % (len(blocks2), bad))
sys.exit(1 if bad else 0)
