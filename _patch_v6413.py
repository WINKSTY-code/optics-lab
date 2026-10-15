# -*- coding: utf-8 -*-
"""
v6.4.12 -> v6.4.13 补丁脚本
修复：3D实验右下角全屏按钮，切到其他实验再切回后临时失效。

根因：
  S3D 挂载层里 it.on（此刻是否在渲染）与 it.view（用户选的 2D/3D）是分开的。
  互斥回收 reclaimOthers / 静置回收 scheduleIdle(30s) 触发的 unmount() 会把
  it.on 置回 false，但 view 仍是 '3d'（设计如此，便于切回时恢复 3D）。
  而 resumeFor() 唤醒画面时从不恢复 it.on —— 右下角全屏按钮的点击守卫正是
  st[k].on，于是"切走(>=30s 或去别的实验开了3D)再回来"按钮就静默失效，
  直到用户把 2D/3D 再切一轮才活。滑杆同步(onAnyEvent)、切页暂停也用同一守卫。

补丁点：
  P1 BUILD 版本号
  P2 RPT_BUILD 兜底版本号
  P3 右下角版本角标
  P4 更新日志新增 V6.4.13 条目
  P5 st 声明加 _seq（激活次序计数器）
  P6 setMode 进 3D 时记录 it.seq
  P7 resumeFor 重写：恢复 it.on、mount 成功才置位、同页互斥只唤醒最后激活的
  P8 message handler 新增 s3d:ready 分支：remount 后补发参数与运行态
"""
import io, os, re, sys

SRC = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.12.html"
DST = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.13.html"

with io.open(SRC, "r", encoding="utf-8") as f:
    s = f.read()

def patch(name, old, new, s):
    n = s.count(old)
    assert n == 1, "[%s] 匹配 %d 处（应为 1）" % (name, n)
    print("[OK] %s" % name)
    return s.replace(old, new, 1)

# ---------- P1 BUILD ----------
s = patch("P1 BUILD",
      "var BUILD = 'v6.4.12', MAX_SHOW = 3",
      "var BUILD = 'v6.4.13', MAX_SHOW = 3", s)

# ---------- P2 RPT_BUILD ----------
s = patch("P2 RPT_BUILD",
      "    return 'v6.4.12';",
      "    return 'v6.4.13';", s)

# ---------- P3 ver-badge ----------
m = re.search(r'<div class="ver-badge" title="[^"]*">v6\.4\.12</div>', s)
assert m and s.count(m.group(0)) == 1, "P3 ver-badge 定位失败"
s = s.replace(m.group(0),
      '<div class="ver-badge" title="光学交互实验室 V6.4.13 · 修复切到其他实验再回来后，3D 右下角全屏按钮临时失效的问题（唤醒时恢复渲染标记，回收重挂后自动补发参数）。">v6.4.13</div>')
print("[OK] P3 ver-badge")

# ---------- P4 更新日志 ----------
old_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.12</span><span class="log-date">2026-09-18</span></div>\n'
           '        <p>挑战模式自动出题，启动超时15秒。</p>\n'
           '      </div>')
new_log = ('      <div class="log-item cur">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.13</span><span class="log-date">2026-09-18</span></div>\n'
           '        <p>修复切页回来后3D全屏按钮失效，唤醒即恢复渲染状态。</p>\n'
           '      </div>\n'
           '      <div class="log-item">\n'
           '        <div class="log-head"><span class="log-ver">V6.4.12</span><span class="log-date">2026-09-18</span></div>\n'
           '        <p>挑战模式自动出题，启动超时15秒。</p>\n'
           '      </div>')
s = patch("P4 更新日志", old_log, new_log, s)

# ---------- P5 st 声明 ----------
m = re.search(r'  var st = \{\};[^\n]*\n', s)
assert m and s.count(m.group(0)) == 1, "P5 st 声明定位失败"
s = s.replace(m.group(0),
      "  var st = {}, _seq = 0;             // key -> { on:bool, mounted:bool, view, seq }；seq=进入3D的次序，resumeFor 据此只唤醒最后激活的\n")
print("[OK] P5 st 声明")

# ---------- P6 setMode 记录 seq ----------
old = ("    it.on = on;\n"
       "    /* view 记住用户选的 2D/3D")
new = ("    it.on = on;\n"
       "    if (on) it.seq = ++_seq;                /* ★ V6.4.13：记录激活次序，同页多个 3D 案例唤醒时只认最后一个 */\n"
       "    /* view 记住用户选的 2D/3D")
s = patch("P6 setMode seq", old, new, s)

# ---------- P7 resumeFor 重写 ----------
m = re.search(r'  function resumeFor\(panelId\)\{.*?\n  \}\n', s, re.S)
assert m and s.count(m.group(0)) == 1, "P7 resumeFor 定位失败"
new_resume = (
"  /* ★ V6.3.0：切回某个实验页时，把该页处于 3D 态的场景重新唤醒。\n"
"     旧实现 on:true 只在点 3D 按钮那一处发过，而切页会无条件暂停，\n"
"     于是「切到别的实验再切回来」必然看到一帧死图（拖不动、缩放无反应）。\n"
"   ★ V6.4.13：唤醒时同步恢复 it.on —— 互斥回收 / 静置回收都会把 on 置回 false\n"
"     （view 仍保留 '3d'），旧版只顾唤醒画面不恢复 on，而右下角全屏按钮、\n"
"     滑杆同步、切页暂停都以 st[k].on 为守卫，于是切页回来按钮就临时失效。\n"
"     另外 mount 可能失败（源码缺失），置位放在 mount 成功之后。\n"
"     同页若有多个 3D 案例（直线传播的影子 / 小孔），只唤醒最后激活的那个。 */\n"
"  function resumeFor(panelId){\n"
"    var cands = [], k, i;\n"
"    for (k in CFG){\n"
"      if (CFG[k].panel === panelId && st[k] && st[k].view === '3d') cands.push(k);\n"
"    }\n"
"    cands.sort(function(a, b){ return (st[b].seq || 0) - (st[a].seq || 0); });\n"
"    for (i = 1; i < cands.length; i++) setMode(cands[i], '2d');   /* 其余复位成 2D（幂等） */\n"
"    if (cands.length){\n"
"      k = cands[0];\n"
"      var it = st[k];\n"
"      cancelIdle(k);\n"
"      reclaimOthers(k);\n"
"      if (mount(k)){                            /* 静置期间被回收过就重新初始化 */\n"
"        it.on = true;                           /* ★ V6.4.13：渲染标记随画面一起恢复 */\n"
"        sync(k);                                /* 把父页当前参数推回场景 */\n"
"        post(k, { t:'s3d:active', on:true });\n"
"        announce(k, true);\n"
"      }\n"
"    }\n"
"    if (window.ECL && window.ECL.onTab){ try { window.ECL.onTab(panelId === 'tab-line'); } catch(e){} }\n"
"  }\n")
s = s.replace(m.group(0), new_resume, 1)
print("[OK] P7 resumeFor 重写")

# ---------- P8 s3d:ready 分支 ----------
old = "    if (m.t === 's3d:state'){ if (!echoing && CFG[m.key]) applyBack(m.key, m.params); return; }"
new = ("    if (m.t === 's3d:ready'){\n"
       "      /* ★ V6.4.13：remount 后最初发出的 init / active 会发进重载中的 iframe 而丢失。\n"
       "         子场景加载完成（或渲染上下文自愈）时会报 ready —— 在这里补发参数与运行态，\n"
       "         恢复才真正闭环；仅当该场景确实处于渲染态且所在页正被查看时才补。 */\n"
       "      if (m.key && CFG[m.key] && isOn(m.key) && onTabOf(m.key)){\n"
       "        sync(m.key); post(m.key, { t:'s3d:active', on:true });\n"
       "      }\n"
       "      return;\n"
       "    }\n"
       "    if (m.t === 's3d:state'){ if (!echoing && CFG[m.key]) applyBack(m.key, m.params); return; }")
s = patch("P8 s3d:ready 分支", old, new, s)

# ---------- 收尾：残留版本串检查 ----------
left = [i + 1 for i, ln in enumerate(s.split("\n")) if "v6.4.12" in ln and "log-ver" not in ln]
print("残留 v6.4.12（更新日志历史条目除外）:", left)
assert not left, "仍有未升级的版本号"

with io.open(DST, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("已写出:", DST, os.path.getsize(DST), "bytes")
