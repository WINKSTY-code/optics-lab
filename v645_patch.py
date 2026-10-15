# -*- coding: utf-8 -*-
"""
V6.4.3 -> V6.4.5
把独立作品「路灯下的影子间距 3D演示」作为「3D案例」集成进 5·直线传播 的【影子形成】模式，
并在实验区右下角提供 2D / 3D案例 切换（复用既有 s3d 挂载层，与另四个 3D 场景完全同口径）。

改动清单
  A. 影子形成的「3D案例」切换条 + 3D 框（懒挂载 iframe），与小孔成像的那一套并列
  B. 内嵌场景源码 window.__S3D_SHADOW__（新开一个 script 块，不动既有大块）
  C. 挂载层：SRC/CFG 增 shadow；setMode 恢复原 inline display（同舞台两条切换条互不点亮）
  D. 直线传播模块：切模式时收回 3D 并切换两条切换条的显隐；影子 3D 态不落数据表 + 角标提示
  E. 版本号四处同步（BUILD / 报告兜底常量 / 版本角标 / 更新日志）

每处替换都断言命中次数，任一处不符立即中止。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.3.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.5.html")
SCENE = os.path.join(BASE, "src3d", "shadow", "shadow3d.html")

LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


# ------------------------------------------------------------------ A. 切换条与 3D 框
BAR_AND_FRAME = """
    <!-- V6.4.5：影子形成「3D案例」——路灯下的影子间距（独立 3D 场景，懒挂载，仅影子模式显示） -->
    <div class="s3d-bar" data-s3d="shadow" role="group" aria-label="3D案例切换">
          <button type="button" class="s3d-b is-on" data-m="2d" aria-pressed="true" data-i18n="s3d.2d">2D</button>
          <button type="button" class="s3d-b" data-m="3d" aria-pressed="false" data-i18n="s3d.case3d">3D案例</button>
          <button type="button" class="s3d-b s3d-only3 s3d-fsb" data-i18n-title="s3d.fs" title="全屏演示" aria-label="全屏演示"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M4 9V4h5M20 15v5h-5M15 4h5v5M9 20H4v-5"/></svg></button>
    </div>
    <div class="s3d-frame" data-s3d="shadow" hidden>
          <div class="s3d-fsbar">
            <button type="button" class="sec s3d-exit" data-i18n="s3d.exit">← 退出全屏</button>
            <span class="s3d-fstip" data-i18n="s3d.fstip">按 Esc 或点左侧按钮退出全屏</span>
          </div>
          <iframe class="s3d-ifr" title="路灯下的影子间距 · 3D 案例" aria-label="路灯下的影子间距 · 3D 案例"></iframe>
    </div>
"""

# ------------------------------------------------------------------ C. 挂载层
SRC_OLD = ("  var SRC = { refl: window.__S3D_REFL__, lens: window.__S3D_LENS__, "
           "mirror: window.__S3D_MIRROR__, pinhole: window.__S3D_PINHOLE__ };")
SRC_NEW = ("  var SRC = { refl: window.__S3D_REFL__, lens: window.__S3D_LENS__, "
           "mirror: window.__S3D_MIRROR__, pinhole: window.__S3D_PINHOLE__,\n"
           "              shadow: window.__S3D_SHADOW__ };")

CFG_OLD = "    pinhole:{ panel:'tab-line',    src:{} }\n  };"
CFG_NEW = ("    pinhole:{ panel:'tab-line',    src:{} },\n"
           "    /* V6.4.5：路灯下的影子间距。参数是「灯高 / 两人身高 / 间距」，与 2D\n"
           "       「影子形成」的（物距 / 物体位置）不是一套，故不同步、也不落数据表。 */\n"
           "    shadow: { panel:'tab-line',    src:{} }\n  };")

HELPER_OLD = ("  function barOf(k){ return document.querySelector('.s3d-bar[data-s3d=\"' + k + '\"]'); }")
HELPER_NEW = HELPER_OLD + """
  /* ★ V6.4.5：隐藏前先记下元素【原本的】inline display，恢复时还原原值。
     旧实现一律置回空串，而直线传播页的同一个 .s3d-stage 里有两条「3D案例」切换条
     （影子形成 / 小孔成像），各自由直线传播模块按当前模式控制显隐；
     置回空串会把本该 display:none 的那条点亮 —— 两条切换条同时可见。 */
  function setDisp1(node, hide){
    if (hide){
      if (node.__s3dDisp === undefined) node.__s3dDisp = node.style.display;
      node.style.display = 'none';
    } else if (node.__s3dDisp !== undefined){
      node.style.display = node.__s3dDisp;
      delete node.__s3dDisp;
    }
  }
  /* 视图变化广播：各实验据此调整「本模式是否参与数据记录」一类的联动 */
  function announce(k, on){
    try { document.dispatchEvent(new CustomEvent('s3d:view', { detail:{ key:k, on:on } })); } catch(e){}
  }"""

SETMODE_OLD = """    var stage = frame.parentNode, col = stage.parentNode, i, el;
    /* 舞台内：只有画布要让位（切换条与 3D 框各自按需显示） */
    for (i = 0; i < stage.children.length; i++){
      el = stage.children[i];
      if (el === frame || el === bar) continue;
      el.style.display = on ? 'none' : '';
    }
    /* 舞台外（画布下方的图例等）：3D 态一并收起，免得 2D 的说明留在 3D 界面里 */
    for (i = 0; i < col.children.length; i++){
      el = col.children[i];
      if (el === stage) continue;
      el.style.display = on ? 'none' : '';
    }"""
SETMODE_NEW = """    var stage = frame.parentNode, col = stage.parentNode, i, el;
    /* 舞台内：只有画布要让位（切换条与 3D 框各自按需显示） */
    for (i = 0; i < stage.children.length; i++){
      el = stage.children[i];
      if (el === frame || el === bar) continue;
      setDisp1(el, on);
    }
    /* 舞台外（画布下方的图例等）：3D 态一并收起，免得 2D 的说明留在 3D 界面里 */
    for (i = 0; i < col.children.length; i++){
      el = col.children[i];
      if (el === stage) continue;
      setDisp1(el, on);
    }"""

VIEW_OLD = """    it.view = on ? '3d' : '2d';
    if (on){"""
VIEW_NEW = """    it.view = on ? '3d' : '2d';
    announce(k, on);
    if (on){"""

RESUME_OLD = """      sync(k);                                  /* 把父页当前参数推回场景 */
      post(k, { t:'s3d:active', on:true });"""
RESUME_NEW = """      sync(k);                                  /* 把父页当前参数推回场景 */
      post(k, { t:'s3d:active', on:true });
      announce(k, true);"""

MODULE_DOC_OLD = "   · 三个 3D 场景各自是【自包含单文件】"
MODULE_DOC_NEW = "   · 五个 3D 场景各自是【自包含单文件】"

# ------------------------------------------------------------------ D. 直线传播模块
NOTE_OLD = ('<span class="ecl-note" id="line-eclNote" hidden data-i18n="ecl.note">'
            '3D 演示不参与数据记录</span>')
NOTE_NEW = NOTE_OLD + ('<span class="ecl-note" id="line-s3dNote" hidden data-i18n="ecl.note">'
                       '3D 演示不参与数据记录</span>')

MODE_OLD = """    mode = b.dataset.m;
    // V6.4.3：离开小孔成像时收回 3D 案例；「3D案例」切换条仅在小孔成像模式显示
    if (window.S3D && S3D.isOn && S3D.isOn('pinhole') && mode !== 'pinhole') S3D.setMode('pinhole', '2d');
    var _pb3d = document.querySelector('.s3d-bar[data-s3d="pinhole"]');
    if (_pb3d) _pb3d.style.display = (mode === 'pinhole') ? '' : 'none';"""
MODE_NEW = """    mode = b.dataset.m;
    // V6.4.5：离开某模式时收回它的 3D 案例，并把 view 复位成 2d（幂等调用）
    if (window.S3D && S3D.setMode){
      if (mode !== 'shadow')  S3D.setMode('shadow',  '2d');
      if (mode !== 'pinhole') S3D.setMode('pinhole', '2d');
    }
    // 「3D案例」切换条只在对应模式显示（影子形成 / 小孔成像各一条）
    var _sb3d = document.querySelector('.s3d-bar[data-s3d="shadow"]');
    if (_sb3d) _sb3d.style.display = (mode === 'shadow') ? '' : 'none';
    var _pb3d = document.querySelector('.s3d-bar[data-s3d="pinhole"]');
    if (_pb3d) _pb3d.style.display = (mode === 'pinhole') ? '' : 'none';"""

GETTER_OLD = """      // V5.2.0：3D 演示为独立场景，不参与数据记录（返回 null → REC.commit 直接跳过）
      if (mode === 'eclipse') return null;"""
GETTER_NEW = """      // V5.2.0：3D 演示为独立场景，不参与数据记录（返回 null → REC.commit 直接跳过）
      if (mode === 'eclipse') return null;
      // V6.4.5：影子 3D 案例的参数（灯高 / 身高 / 间距）与 2D 的（物距 / 物体位置）
      // 不是同一套，照记会写进与画面不符的脏数据，故同样返回 null
      if (mode === 'shadow' && window.S3D && S3D.isOn && S3D.isOn('shadow')) return null;"""

LISTEN_OLD = """    'rectilinear_data.csv');

  return { setTheme(t){ P = PAL[t]; render(); }, render };"""
LISTEN_NEW = """    'rectilinear_data.csv');

  /* V6.4.5：影子形成切到 3D 案例时，数据面板上标注「本次不参与记录」 */
  document.addEventListener('s3d:view', function(e){
    var d = e && e.detail;
    if (!d || d.key !== 'shadow') return;
    var n = document.getElementById('line-s3dNote');
    if (n) n.hidden = !d.on;
  });

  return { setTheme(t){ P = PAL[t]; render(); }, render };"""

# ------------------------------------------------------------------ E. 版本号
VER_BADGE_OLD = ('<div class="ver-badge" title="光学交互实验室 V6.4.3 · 小孔成像新增心形小孔阵3D案例">'
                 'v6.4.3</div>')
VER_BADGE_NEW = ('<div class="ver-badge" title="光学交互实验室 V6.4.5 · 影子形成新增路灯影子间距3D案例">'
                 'v6.4.5</div>')

LOG_OLD = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.3</span><span class="log-date">2026-09-17</span></div>
        <p>小孔成像新增心形小孔阵3D案例。</p>
      </div>"""
LOG_NEW = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.5</span><span class="log-date">2026-09-18</span></div>
        <p>影子形成新增路灯影子间距3D案例。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.3</span><span class="log-date">2026-09-17</span></div>
        <p>小孔成像新增心形小孔阵3D案例。</p>
      </div>"""


def main():
    s = open(SRC, encoding="utf-8").read()
    size0 = os.path.getsize(SRC)
    n_open0 = len(re.findall(r"<script", s))
    n_close0 = len(re.findall(r"</script(?=[\s>/])", s))

    scene = open(SCENE, encoding="utf-8").read()
    esc = json.dumps(scene, ensure_ascii=False)
    assert json.loads(esc) == scene, "JSON 往返不等价"
    esc = re.sub(r"</script", lambda m: "<\\/script", esc, flags=re.I)   # 必须用 lambda，字符串 repl 会二次解释转义
    assert "</script" not in esc.replace("<\\/script", ""), "仍残留脚本收尾标签字面量"
    LOG.append("OK  %-52s %.2f%%" % ("场景源码 json 转义", (len(esc) - len(scene)) * 100.0 / len(scene)))

    # A. 切换条 + 3D 框（插在小孔成像那套之前，DOM 顺序与模式顺序一致）
    canvas_tag = ('<canvas id="cv-line" width="920" height="420" role="img" '
                  'aria-label="光的直线传播实验示意图：影子形成与小孔成像两种模式，结论见右侧判定卡片"></canvas>')
    s = rep(s, canvas_tag + "\n", canvas_tag + "\n" + BAR_AND_FRAME, 1, "A 切换条 + 3D 框")

    # B. 内嵌场景源码（新开 script 块，放在 MIRROR 块之后、s3d 样式之前）
    anchor_b = "\\n</html>\\n\";\n</script>\n\n<style>\n/* ==========================================================================\n   V6.0.0 · 2D / 3D 视图切换"
    assert s.count(anchor_b) == 1, "[FAIL] B 源码插入锚点不唯一：%d" % s.count(anchor_b)
    # ⚠️ json.dumps 的返回值【自带外层引号】，这里不能再补引号，否则 JS 变成
    #     `= ""<!DOCTYPE …`（多一对引号，且 json.loads 反解会报 Extra data）。
    new_block = ('\\n</html>\\n";\n</script>\n\n<script>\n'
                 'window.__S3D_SHADOW__ = ' + esc + ';\n</script>\n\n'
                 '<style>\n/* ==========================================================================\n'
                 '   V6.0.0 · 2D / 3D 视图切换')
    s = s.replace(anchor_b, new_block)
    LOG.append("OK  %-52s x1" % "B __S3D_SHADOW__ 源码块")

    # C. 挂载层
    s = rep(s, SRC_OLD, SRC_NEW, 1, "C1 SRC 增 shadow")
    s = rep(s, CFG_OLD, CFG_NEW, 1, "C2 CFG 增 shadow")
    s = rep(s, MODULE_DOC_OLD, MODULE_DOC_NEW, 1, "C3 模块头注释")
    s = rep(s, HELPER_OLD, HELPER_NEW, 1, "C4 setDisp1 / announce")
    s = rep(s, SETMODE_OLD, SETMODE_NEW, 1, "C5 setMode 还原原 inline display")
    s = rep(s, VIEW_OLD, VIEW_NEW, 1, "C6 setMode 广播视图变化")
    s = rep(s, RESUME_OLD, RESUME_NEW, 1, "C7 resumeFor 广播视图变化")

    # D. 直线传播模块
    s = rep(s, NOTE_OLD, NOTE_NEW, 1, "D1 数据面板提示元素")
    s = rep(s, MODE_OLD, MODE_NEW, 1, "D2 模式切换：收回 3D + 两条例显隐")
    s = rep(s, GETTER_OLD, GETTER_NEW, 1, "D3 影子 3D 态不落数据表")
    s = rep(s, LISTEN_OLD, LISTEN_NEW, 1, "D4 监听 s3d:view 显示提示")

    # E. 版本号四处
    s = rep(s, "var BUILD = 'v6.4.3'", "var BUILD = 'v6.4.5'", 1, "E1 BUILD")
    s = rep(s, "    return 'v6.4.3';\n  })();", "    return 'v6.4.5';\n  })();", 1, "E2 报告兜底常量")
    s = rep(s, VER_BADGE_OLD, VER_BADGE_NEW, 1, "E3 版本角标")
    s = rep(s, LOG_OLD, LOG_NEW, 1, "E4 更新日志")

    # ------------------------------------------------------------ 硬校验
    n_open1 = len(re.findall(r"<script", s))
    n_close1 = len(re.findall(r"</script(?=[\s>/])", s))
    # 新增块自带一开一收；多出来的收标签就意味着转义没做干净（整页脚本链会断）。
    assert n_close1 == n_close0 + 1, "脚本收尾标签字面量应为 %d，实际 %d" % (n_close0 + 1, n_close1)
    # 开标签会多出「新块自己 1 个 + 场景源码字符串里未转义的 N 个」——
    # 脚本数据状态下裸 <script 无害，但一旦前面出现 <!-- 就会进入双重转义态，
    # 那时收标签失效 → 整页脚本链断裂。故场景源码里必须没有 HTML 注释。
    assert "<!--" not in scene, "场景源码含 HTML 注释，内嵌后会破坏脚本链"
    n_open_expect = n_open0 + 1 + scene.count("<script")
    assert n_open1 == n_open_expect, "脚本开标签数应为 %d，实际 %d" % (n_open_expect, n_open1)
    LOG.append("OK  %-52s opens %d->%d  closes %d->%d" % ("脚本标签计数", n_open0, n_open1, n_close0, n_close1))

    # 产物里反解场景源码，与磁盘原子文件逐字符比对（JSON 的 \/ 就是 /，无需额外替换）
    m = re.search(r'window\.__S3D_SHADOW__ = (".*?");\n</script>', s, re.S)
    assert m, "产物里找不到 __S3D_SHADOW__"
    back = json.loads(m.group(1))
    assert back == scene, "产物里的场景源码与 src3d/shadow/shadow3d.html 不一致"
    LOG.append("OK  %-52s %d B" % ("场景源码反解逐字符比对", len(back)))

    open(DST, "w", encoding="utf-8", newline="\n").write(s)
    n1 = os.path.getsize(DST)
    print("\n".join(LOG))
    print("\n源 %s (%d B)\n产物 %s (%d B, %+d B)"
          % (os.path.basename(SRC), size0, os.path.basename(DST), n1, n1 - size0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
