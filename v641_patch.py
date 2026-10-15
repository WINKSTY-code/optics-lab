# -*- coding: utf-8 -*-
"""V6.4.1 大文件补丁：
1) 凸透镜 3D 场景（__S3D_LENS__）替换为支持物体三维全方向移动的新版
2) 版本号三处（BUILD / RPT_BUILD 兜底 / 角标）
3) 更新日志：新增 V6.4.1 条目；V5.1.0 ~ V6.4.0 共 12 条精简至 ≤30 字
所有替换断言命中数；产物做脚本收尾标签字面量硬校验 + 拆块 node --check。"""
import re, json, os, subprocess, sys

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
SRC = BASE + r"\光学交互实验室_AI_v6.4.0.html"
DST = BASE + r"\光学交互实验室_AI_v6.4.1.html"
CUR_INNER = BASE + r"\_lens_current.js"          # 旧内嵌 HTML（从 v6.4.0 提取）
NEW_SCENE = BASE + r"\_lens_scene_new.js"
LOG = []

s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)

def rep(old, new, n=1, label=""):
    global s
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    s = s.replace(old, new)
    LOG.append("OK  %s  x%d" % (label, c))

# ================= 1) 场景注入 =================
old_inner = open(CUR_INNER, encoding="utf-8").read()
new_scene = open(NEW_SCENE, encoding="utf-8").read().replace("\r\n", "\n")

# 旧内嵌 HTML 中定位块[3]（凸透镜场景脚本），整块替换
pat_blk = re.compile(r"(<script[^>]*>)(.*?)(</script(?=[\s>/]))", re.S)
blocks = list(pat_blk.finditer(old_inner))
assert len(blocks) == 4, "旧内嵌 HTML 脚本块数 %d != 4" % len(blocks)
b3 = blocks[3]
old_scene = b3.group(2)
assert old_scene.count("凸透镜成像") >= 1 and "立体光锥" in old_scene, "块[3]不是凸透镜场景"
new_inner = old_inner[:b3.start(2)] + "\n" + new_scene + "\n" + old_inner[b3.end(2):]
# 反解自证：新内嵌 HTML 的块[3]必须逐字等于新场景脚本
nb = list(pat_blk.finditer(new_inner))
assert len(nb) == 4, "新内嵌 HTML 脚本块数不是 4"
assert nb[3].group(2).strip() == new_scene.strip(), "块[3]替换后回读不一致"
LOG.append("OK  场景块替换 round-trip 自证  x1")

# JSON 转义 + </script → <\/script（JS 字符串里 \/ 即 /）
esc = json.dumps(new_inner, ensure_ascii=False)
esc = esc.replace("</script", "<\\/script")
assert json.loads(esc) == new_inner, "转义 round-trip 失败"
LOG.append("OK  __S3D_LENS__ 转义 round-trip  x1")

pat_assign = re.compile(r'window\.__S3D_LENS__\s*=\s*"(?:[^"\\]|\\.)*";')
ms = pat_assign.findall(s)
assert len(ms) == 1, "__S3D_LENS__ 赋值出现 %d 处" % len(ms)
# ⚠️ 必须用 lambda：re.sub 的字符串 repl 会把 esc 里的 \\n、\\" 等序列二次解释
s = pat_assign.sub(lambda m: "window.__S3D_LENS__ = " + esc + ";", s, count=1)
LOG.append("OK  __S3D_LENS__ 注入  x1")

# ================= 2) 版本号三处 =================
rep("var BUILD = 'v6.4.0', MAX_SHOW = 3",
    "var BUILD = 'v6.4.1', MAX_SHOW = 3", 1, "BUILD 常量")
rep("    return 'v6.4.0';", "    return 'v6.4.1';", 1, "RPT_BUILD 兜底")
rep('<div class="ver-badge" title="光学交互实验室 V6.4.0 · UI设计优化：顶栏窄屏不再折行挤压、AI 提示移至右下角、画布底色统一纸面主题、色散标注避让光路">v6.4.0</div>',
    '<div class="ver-badge" title="光学交互实验室 V6.4.1 · 凸透镜3D实验实现物体三维全方向移动">v6.4.1</div>',
    1, "版本角标")

# ================= 3) 更新日志 =================
# 3a) 新增 V6.4.1 当前条目 + 精简 V6.4.0
rep("""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.0</span><span class="log-date">2026-09-16</span></div>
        <p><strong>UI 设计优化</strong>：顶栏按钮在手机端与窄窗口下不再被挤压成竖排文字（整行自动换行，不丢任何功能）；「AI 学伴已就绪」提示条移至右下角，不再遮挡实验页签；各 2D 实验画布底色统一收敛为纸面主题色（与页面底色保留细微层次，色散实验保留暗场观察）；三棱镜色散图的「法线」标注移至虚线外端、说明文字移至左下空白区，不再与彩色光路重叠。</p>
      </div>""",
"""      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.1</span><span class="log-date">2026-09-17</span></div>
        <p>凸透镜3D实验实现物体三维全方向移动</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.0</span><span class="log-date">2026-09-16</span></div>
        <p>顶栏窄屏不折行，AI 提示移右下角，画布底色统一纸面主题。</p>
      </div>""",
    1, "日志 V6.4.1 新增 + V6.4.0 精简")

# 3b) 其余 11 条精简（V5.1.0 ~ V6.3.0）
rep("<p>修掉<strong>「在 3D 模式下标一下实验名，3D 画面就冻住」</strong>（切走时被暂停，却没有任何代码唤回）；<strong>凸透镜 3D</strong> 补上物距与焦距滑块、<strong>平面镜 3D</strong> 补上物距滑块并在控制条显示物距 / 像距；<strong>日食 3D</strong> 补上上下文丢失恢复与暂停开关；四个 3D 场景改为<strong>同一时刻只保留一份挂载</strong>（原来最多四份 WebGL 上下文同时活着）。</p>",
    "<p>修3D切页冻结，透镜平面镜补滑块，同屏只留一份3D。</p>",
    1, "日志 V6.3.0 精简")
rep("<p>「光的反射」3D 场景新增<strong>光路可逆</strong>开关：打开后在反射光射出的方向上放上一支<strong>另一种颜色</strong>的激光笔反向射入，反射光会沿<strong>原来的入射光路</strong>射回去、与原入射光线完全重合；把纸板 F 折转时反向光路同样随之消失（可见口径与原场景一致）。同步精简 V6.0.0 及以后各版本的更新日志篇幅。</p>",
    "<p>反射3D新增光路可逆开关：反向入射沿原路返回。</p>",
    1, "日志 V6.2.2 精简")
rep("<p>修掉三个 3D 场景<strong>「用一段时间就卡死」</strong>：光路改为<strong>共享资源池</strong>（自动扫描时每帧新建对象由 24 个降到 2 个、几何体与材质分配归零，不再持续冲击显存）；补上 <strong>WebGL 上下文丢失后的恢复路径</strong>（能自动恢复就接着渲染，恢复不了则下次进 3D 重新初始化）；修掉 8 秒超时兜底把用户误踢回 2D 的问题。</p>",
    "<p>修3D久用卡死：光路共享资源池，补上下文丢失恢复。</p>",
    1, "日志 V6.2.1 精简")
rep("<p>三个 3D 场景按「实物上到底看得见什么」重修：<strong>光的反射</strong>纸板折转后反射光线<strong>真的消失</strong>（另增入射角自动扫描）；<strong>平面镜成像</strong>棋子 A、B 各自独立可拖动，判定重合要求前后与左右都对上；<strong>凸透镜成像</strong>重建为中间厚、边缘薄、带金属镜箍的<strong>立体双凸透镜</strong>。</p>",
    "<p>三3D按实物重修：折板光真消失，棋子可拖，立体双凸透镜。</p>",
    1, "日志 V6.2.0 精简")
rep("<p>三个 3D 场景集中修订：<strong>2D ｜ 3D 切换条移到实验区右下角</strong>；修掉「点实验名会退掉网页全屏」；平面镜棋子<strong>可直接在 3D 里拖动</strong>；光的反射把<strong>入射角也放进 3D 控制条</strong>；凸透镜的<strong>光锥改成真正的立体光锥</strong>。</p>",
    "<p>3D集中修订：切换条移右下角，修全屏误退，光锥立体化。</p>",
    1, "日志 V6.1.0 精简")
rep("<p><strong>光的反射 / 凸透镜成像 / 平面镜成像</strong>三个实验各新增一个独立的 <strong>3D 立体场景</strong>，画布角落 <strong>2D ｜ 3D</strong> 一键切换（2D 视图与原有全部功能不变）。三个场景都按苏科版教材装置建模，自动继承当前 2D 参数并双向同步，支持全屏，各自内嵌 three.js、离线可用。</p>",
    "<p>反射/透镜/平面镜三实验新增3D立体场景，一键切换。</p>",
    1, "日志 V6.0.0 精简")
rep("<p>「直线传播」实验新增第三个模式<strong>「日食与月食」</strong>：把一份独立的<strong>3D 立体演示</strong>（日地月系统 · 本影 / 半影光锥 · 食相时间轴 · 观测窗遮挡比例，内联 three.js、离线可用）以独立文档边界内嵌进本页，与「影子形成」「小孔成像」并列切换，支持<strong>全屏放大</strong>观察；3D 演示为自带场景，不参与数据记录。</p>",
    "<p>直线传播新增日食月食3D演示，支持全屏观察。</p>",
    1, "日志 V5.2.0 精简")
rep("<p>每个实验的数据记录行末新增<strong>「实验报告」按钮</strong>（浅蓝底色），点一下直接跳到该实验的实验报告；报告页的「← 返回实验」按钮同步改为浅蓝底色；数据记录行的「导出CSV」精简为「导出」。</p>",
    "<p>数据行末新增实验报告按钮，导出CSV精简为导出。</p>",
    1, "日志 V5.1.3 精简")
rep("<p>「实验报告」不再与 10 个实验并列成第 12 个标签页，改为从「AI 诊断」弹窗进入，报告页内新增「← 返回实验」快捷出口；同步精简 V5.0 及之后的更新日志篇幅。</p>",
    "<p>实验报告移入AI诊断弹窗，报告页加返回实验出口。</p>",
    1, "日志 V5.1.2 精简")
rep("<p>新增「实验报告」：按<strong>问题 → 猜想 → 方案（含变量控制）→ 数据表 → 结论 → 反思</strong>六要素组织，其中问题、方案、数据与结论均由各实验<strong>画布的真实参数</strong>自动取值；另含自评 / 互评与完成度进度条。支持一键导出自包含 HTML、纯文本、数据 CSV 与打印 / 存 PDF，全部离线可用。</p>",
    "<p>新增实验报告：六要素自动取数，支持导出与打印。</p>",
    1, "日志 V5.1.1 精简")
rep("<p>新增通用数据记录器：有数据可记的实验在用户<strong>停止操作 1 秒后自动落表</strong>（拖动滑块、切换模式、画布拖拽均可触发），数据自动去重并可导出 CSV；为原先缺表的 6 个实验补齐表格。AI 判卷升级为<strong>错因归因</strong>，并自动生成同知识点的变式题。</p>",
    "<p>新增通用数据记录器自动落表，AI判卷升级错因归因。</p>",
    1, "日志 V5.1.0 精简")

# ================= 4) 硬校验 + 落盘 =================
# 基线口径：源文件字符串内含未转义的 <script 开标签（内嵌 HTML 源码），故 opens>closes 属正常。
# 校验目的（§12）是「正文不得新增脚本收尾标签字面量」→ 要求前后计数都不变。
src_s = open(SRC, encoding="utf-8").read()
c0, o0 = len(re.findall(r"</script(?=[\s>/])", src_s)), len(re.findall(r"<script[^>]*>", src_s))
closes = re.findall(r"</script(?=[\s>/])", s)
n_open = len(re.findall(r"<script[^>]*>", s))
assert len(closes) == c0, "[FAIL] 收尾标签字面量 %d != 源 %d（正文混入了提前闭合）" % (len(closes), c0)
assert n_open == o0, "[FAIL] 开标签 %d != 源 %d（意外增删了 script 元素）" % (n_open, o0)
LOG.append("OK  script 标签计数与源一致（closes %d / opens %d）" % (len(closes), n_open))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))

# ================= 5) 拆 JS 块 node --check =================
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"
html = open(DST, encoding="utf-8").read()
blocks2 = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", html, re.S)
os.makedirs(BASE + r"\_chk641", exist_ok=True)
bad = 0
for i, b in enumerate(blocks2):
    if len(b.strip()) < 20:
        continue
    p = BASE + r"\_chk641\blk%d.js" % i
    open(p, "w", encoding="utf-8", newline="\n").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:400]))
print("拆块检查：%d 块，失败 %d" % (len(blocks2), bad))
sys.exit(1 if bad else 0)
