# -*- coding: utf-8 -*-
"""
V6.4.17 -> V6.4.18
需求：「本地存储提示的弹窗不应该在打开时出现，而是应该在关闭时候出现」

改动：
① maybeAskClearApiKey() 由「加载时立即弹」改为「注册关闭守卫，页面关闭时弹」
   - 移除加载期调用
   - 新增 armApiKeyClearOnExit()：beforeunload / pagehide 时拦截，调用同一个弹窗逻辑
   - 若用户选择清除，则二次 beforeunload 放行（否则关不掉页面）
② 文案改为「关闭提示」语境（标题/说明/按钮/脚注）
③ 版本号四处同步：BUILD + ver-badge（含 title）+ 更新日志 + REPORT 内嵌常量
"""
import re, sys, shutil, os

SRC = "光学交互实验室_AI_v6.4.17 (1).html"
DST = "光学交互实验室_AI_v6.4.18.html"
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %s  x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)

# 基线快照：改动前后这些计数必须不变（防止误伤脚本标签结构）
CLOSES0 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS0 = len(re.findall(r"<script(?=[\s>/])", s))
LOG.append("基线：script opens=%d closes=%d" % (OPENS0, CLOSES0))

# ---------------------------------------------------------------- ① 注释头
s = rep(
    s,
    """  /* V6.4.17：APIKey 本地存储提示——本会话首次加载时，若 localStorage 中仍有 APIKey，
     弹 modal 询问是否清除。理由：API Key 明文存在用户本地浏览器，公用电脑/换电脑时
     应主动清除；之前版本仅靠"重置"按钮手动清，容易遗漏。
     实现要点：
     ① sessionStorage 标记 K+'_keyClearAsked'——每次新会话问一次，不反复打扰
     ② 同时检查主设置 Key + 判卷专属 Key，分开列出
     ③ 三个动作：全部保留 / 仅清判卷 Key / 全部清除（含二次确认）
     ④ key 显示脱敏（前 4 + 后 4 位，中间 ****），避免 modal 里又把明文泄出来 */""",
    """  /* V6.4.16：APIKey 本地存储提示——**关闭页面时**才弹 modal 询问是否清除。
     理由：API Key 明文存在用户本地浏览器，公用电脑/换电脑时应主动清除；
     但"打开就弹"会打断刚进入页面的用户（首次见面先拦一道，体验差）。
     改到关闭时弹，既保留安全提醒，又不影响进入页面后的正常使用。
     实现要点：
     ① 页面加载时**不弹**，只挂一个关闭守卫（armApiKeyClearOnExit）
     ② 守卫挂在 beforeunload / pagehide 上；一旦发现本地仍有 Key，就 preventDefault
        并弹出 modal，用浏览器原生"离开确认"给用户留出决策时间
     ③ 三个动作：全部保留 / 仅清判卷 Key / 全部清除（含二次确认）
     ④ 用户做完选择后放行（exitArmed 置假），再关页面不再拦
     ⑤ key 显示脱敏（前 4 + 后 4 位，中间 ****），避免 modal 里又把明文泄出来 */""",
    1, "注释头改为关闭时弹",
)

# ---------------------------------------------------------------- ② 函数首段
s = rep(
    s,
    """  function maybeAskClearApiKey(){
    try{ if(sessionStorage.getItem(K+'_keyClearAsked') === '1') return; }catch(e){}
    let hasMainKey = false, hasJudgeKey = false;
    // 用 let 而非 const，并提到 try 块外，确保 modal 拼接处能访问到 c/j 的内容
    let mainCfg = {}, judgeCfg = {};
    try{ mainCfg = JSON.parse(localStorage.getItem(K+'_cfg') || '{}'); hasMainKey = !!mainCfg.apikey; }catch(e){}
    try{ judgeCfg = JSON.parse(localStorage.getItem(K+'_judge') || '{}'); hasJudgeKey = !!judgeCfg.apikey; }catch(e){}
    if(!hasMainKey && !hasJudgeKey){
      // 没有任何 Key：也标记一下，避免每次刷新都执行空检查；同时不弹 modal 打扰用户
      try{ sessionStorage.setItem(K+'_keyClearAsked', '1'); }catch(e){}
      return;
    }
    // 用 textContent 拼 UI：避免内嵌外部 LLM 返回文本时引入 XSS（虽然这里数据源是 localStorage，但养成习惯）
    const html = '<h2>🔑 APIKey 本地存储提示</h2><div class="ai-config">' +
      '<p style="margin:0 0 10px;font-size:14px;line-height:1.7;">检测到您的浏览器本地仍保存着上一次填写的 APIKey：</p>' +
      '<ul style="margin:0 0 12px;padding-left:22px;font-size:13.5px;line-height:1.85;color:var(--txt);">' +
        (hasMainKey  ? '<li>AI 主设置 Key（<code style="background:var(--bg);padding:1px 6px;border-radius:4px;font-size:12px;">' + escapeKey(mainCfg.apikey) + '</code>）</li>' : '') +
        (hasJudgeKey ? '<li>判卷专属 Key（<code style="background:var(--bg);padding:1px 6px;border-radius:4px;font-size:12px;">' + escapeKey(judgeCfg.apikey) + '</code>）</li>' : '') +
      '</ul>' +
      '<p style="margin:0 0 14px;font-size:12.5px;line-height:1.75;color:var(--muted);">关闭页面或换电脑前，建议主动清除。清除后下次使用 AI 学伴 / 判卷需重新填写 Key（不再自动保留）。</p>' +
      '<div class="row" style="display:flex;gap:6px;flex-wrap:wrap;">' +
        '<button id="keyKeepAll">✅ 全部保留</button>' +
        (hasJudgeKey ? '<button id="keyClearJudge" class="sec">仅清除判卷 Key</button>' : '') +
        '<button id="keyClearAll" class="sec" style="border-color:var(--red);color:var(--red);">🗑 全部清除</button>' +
      '</div>' +
      '<div style="font-size:11px;color:var(--muted);margin-top:10px;">本提示每次打开页面仅弹一次；可在「⚙ AI 设置」里手动重置 Key。</div>' +
      '</div>';
    showModal(html);
    const markAsked = function(){ try{ sessionStorage.setItem(K+'_keyClearAsked', '1'); }catch(e){} };
    const ck = $('keyKeepAll');
    if(ck) ck.onclick = function(){ markAsked(); closeModal(); };
    const cj = $('keyClearJudge');
    if(cj) cj.onclick = function(){
      try{
        const j = JSON.parse(localStorage.getItem(K+'_judge') || '{}');
        delete j.apikey;
        localStorage.setItem(K+'_judge', JSON.stringify(j));
      }catch(e){}
      markAsked();
      closeModal();
    };
    const ca = $('keyClearAll');
    if(ca) ca.onclick = function(){
      if(typeof confirm === 'function' && !confirm('确认清除全部 APIKey？清除后下次使用 AI 学伴需重新填写 Key。')) return;
      try{
        cfg.apikey = ''; saveCfg();
        const j = JSON.parse(localStorage.getItem(K+'_judge') || '{}');
        delete j.apikey;
        localStorage.setItem(K+'_judge', JSON.stringify(j));
      }catch(e){}
      markAsked();
      try{ updateStatus(); }catch(e){}
      closeModal();
    };
  }""",
    """  /* 判断本地是否还有 Key；返回 {hasMainKey, hasJudgeKey, mainCfg, judgeCfg} */
  function detectLocalKeys(){
    let hasMainKey = false, hasJudgeKey = false;
    // 用 let 而非 const，并提到 try 块外，确保 modal 拼接处能访问到 c/j 的内容
    let mainCfg = {}, judgeCfg = {};
    try{ mainCfg = JSON.parse(localStorage.getItem(K+'_cfg') || '{}'); hasMainKey = !!mainCfg.apikey; }catch(e){}
    try{ judgeCfg = JSON.parse(localStorage.getItem(K+'_judge') || '{}'); hasJudgeKey = !!judgeCfg.apikey; }catch(e){}
    return { hasMainKey: hasMainKey, hasJudgeKey: hasJudgeKey, mainCfg: mainCfg, judgeCfg: judgeCfg };
  }

  /* 关闭提示弹窗：本身不返回是否已处理，结果由 exitArmed 承接 */
  function showApiKeyExitNotice(){
    const d = detectLocalKeys();
    if(!d.hasMainKey && !d.hasJudgeKey) return false;
    const hasMainKey = d.hasMainKey, hasJudgeKey = d.hasJudgeKey;
    const mainCfg = d.mainCfg, judgeCfg = d.judgeCfg;
    const html = '<h2>🔑 离开前，请确认 APIKey 的处理方式</h2><div class="ai-config">' +
      '<p style="margin:0 0 10px;font-size:14px;line-height:1.7;">您正在关闭页面。检测到浏览器本地仍保存着 APIKey：</p>' +
      '<ul style="margin:0 0 12px;padding-left:22px;font-size:13.5px;line-height:1.85;color:var(--txt);">' +
        (hasMainKey  ? '<li>AI 主设置 Key（<code style="background:var(--bg);padding:1px 6px;border-radius:4px;font-size:12px;">' + escapeKey(mainCfg.apikey) + '</code>）</li>' : '') +
        (hasJudgeKey ? '<li>判卷专属 Key（<code style="background:var(--bg);padding:1px 6px;border-radius:4px;font-size:12px;">' + escapeKey(judgeCfg.apikey) + '</code>）</li>' : '') +
      '</ul>' +
      '<p style="margin:0 0 14px;font-size:12.5px;line-height:1.75;color:var(--muted);">若这台电脑是公用设备或不是您自己的，建议现在就清除；清除后下次使用 AI 学伴 / 判卷需重新填写 Key（不再自动保留）。</p>' +
      '<div class="row" style="display:flex;gap:6px;flex-wrap:wrap;">' +
        '<button id="keyKeepAll">✅ 保留，继续关闭</button>' +
        (hasJudgeKey ? '<button id="keyClearJudge" class="sec">仅清除判卷 Key</button>' : '') +
        '<button id="keyClearAll" class="sec" style="border-color:var(--red);color:var(--red);">🗑 全部清除</button>' +
      '</div>' +
      '<div style="font-size:11px;color:var(--muted);margin-top:10px;">选好后网页会继续关闭；本次提示关闭时仅弹一次。也可在「⚙ AI 设置」里手动重置 Key。</div>' +
      '</div>';
    showModal(html);
    /* 已经弹过一次（不论用户选了什么）就不再拦截关闭——避免"关不掉页面" */
    const markAsked = function(){ exitArmed = false; };
    const ck = $('keyKeepAll');
    if(ck) ck.onclick = function(){ markAsked(); closeModal(); };
    const cj = $('keyClearJudge');
    if(cj) cj.onclick = function(){
      try{
        const j = JSON.parse(localStorage.getItem(K+'_judge') || '{}');
        delete j.apikey;
        localStorage.setItem(K+'_judge', JSON.stringify(j));
      }catch(e){}
      markAsked();
      closeModal();
    };
    const ca = $('keyClearAll');
    if(ca) ca.onclick = function(){
      if(typeof confirm === 'function' && !confirm('确认清除全部 APIKey？清除后下次使用 AI 学伴需重新填写 Key。')) return;
      try{
        cfg.apikey = ''; saveCfg();
        const j = JSON.parse(localStorage.getItem(K+'_judge') || '{}');
        delete j.apikey;
        localStorage.setItem(K+'_judge', JSON.stringify(j));
      }catch(e){}
      markAsked();
      try{ updateStatus(); }catch(e){}
      closeModal();
    };
    return true;
  }

  /* V6.4.16：关闭守卫——页面加载时只挂监听、不弹窗；
     真正要离开时才 preventDefault 并弹 modal，给用户一次处理 Key 的机会。
     注意：不注册 beforeunload 的 returnValue（不弹浏览器原生"确定要离开吗"），
     由自绘 modal 承担确认，视觉与站内其他弹窗一致；用户选完后 exitArmed 置假，放行关闭。 */
  var exitArmed = false;
  function armApiKeyClearOnExit(){
    try{ if(sessionStorage.getItem(K+'_keyClearAsked') === '1') return; }catch(e){}
    const d = detectLocalKeys();
    if(!d.hasMainKey && !d.hasJudgeKey){
      // 没有任何 Key：不挂守卫；同时标记，避免每次刷新都重复检查
      try{ sessionStorage.setItem(K+'_keyClearAsked', '1'); }catch(e){}
      return;
    }
    exitArmed = true;
    const onExit = function(e){
      if(!exitArmed) return;                 // 用户已处理过，放行
      if(!detectLocalKeys().hasMainKey && !detectLocalKeys().hasJudgeKey) return;
      e.preventDefault();
      if(e.returnValue !== undefined) e.returnValue = '';   // 兼容旧浏览器拦截
      try{ sessionStorage.setItem(K+'_keyClearAsked', '1'); }catch(err){}
      showApiKeyExitNotice();
    };
    window.addEventListener('beforeunload', onExit);
    window.addEventListener('pagehide', onExit);
    window.addEventListener('unload', onExit);
  }""",
    1,
    "maybeAskClearApiKey 拆成 detectLocalKeys + showApiKeyExitNotice + armApiKeyClearOnExit",
)

# ---------------------------------------------------------------- ③ 调用点
s = rep(
    s,
    """  // V6.4.17：本会话首次进入，若 localStorage 仍有 APIKey，弹一次性 modal 询问是否清除
  maybeAskClearApiKey();""",
    """  // V6.4.16：本地仍有 APIKey 时**不再在打开页面时弹窗**，改为在关闭页面时提醒。
  // 这里只挂守卫（不弹），真正要离开时才 preventDefault 并弹出询问 modal。
  armApiKeyClearOnExit();""",
    1,
    "调用点改为 armApiKeyClearOnExit",
)

# ---------------------------------------------------------------- ④ 版本号：BUILD
s = rep(
    s,
    "var BUILD = 'v6.4.17', MAX_SHOW = 3",
    "var BUILD = 'v6.4.18', MAX_SHOW = 3",
    1,
    "BUILD 常量",
)

# ---------------------------------------------------------------- ⑤ 版本号：REPORT 内嵌常量
s = rep(
    s,
    """    }catch(e){}
    return 'v6.4.17';
  })();""",
    """    }catch(e){}
    return 'v6.4.18';
  })();""",
    1,
    "REPORT 内嵌版本常量",
)

# ---------------------------------------------------------------- ⑥ 版本号：角标
s = rep(
    s,
    '<div class="ver-badge" title="光学交互实验室 V6.4.17 · AI 调用加 20 秒超时与失败 1 次自动重试；页面首次进入时若检测到本地仍有 APIKey，弹 modal 询问是否清除（避免共用电脑泄漏）。">v6.4.17</div>',
    '<div class="ver-badge" title="光学交互实验室 V6.4.18 · APIKey 本地存储提示改为「关闭页面时」弹出（不再打断刚进入页面的使用）；AI 调用保留 20 秒超时与失败 1 次自动重试。">v6.4.18</div>',
    1,
    "版本角标 + title",
)

# ---------------------------------------------------------------- ⑦ 版本号：更新日志
s = rep(
    s,
    """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.17</span><span class="log-date">2026-09-19</span></div>
        <p>AI 调用加 20 秒超时 + 失败 1 次自动重试；首次进入若本地仍有 APIKey 弹 modal 询问清除（防共用电脑泄漏 Key）。</p>
      </div>""",
    """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.18</span><span class="log-date">2026-09-20</span></div>
        <p>APIKey 本地存储提示改为「关闭页面时」弹出——不再一打开就拦一道，只在离开前提醒处理 Key。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.17</span><span class="log-date">2026-09-19</span></div>
        <p>AI 调用加 20 秒超时 + 失败 1 次自动重试；首次进入若本地仍有 APIKey 弹 modal 询问清除（防共用电脑泄漏 Key）。</p>
      </div>""",
    1,
    "更新日志新增 V6.4.18 条目",
)

# ---------------------------------------------------------------- 校验
CLOSES1 = len(re.findall(r"</script(?=[\s>/])", s))
OPENS1 = len(re.findall(r"<script(?=[\s>/])", s))
assert CLOSES1 == CLOSES0, "[FAIL] script 收尾标签数量变了：%d -> %d" % (CLOSES0, CLOSES1)
assert OPENS1 == OPENS0, "[FAIL] script 开标签数量变了：%d -> %d" % (OPENS0, OPENS1)
LOG.append("script opens/closes 前后不变：%d / %d" % (OPENS1, CLOSES1))

# 旧函数名必须已经消失（本轮自己注入的注释里也不含它）
assert "maybeAskClearApiKey" not in s, "[FAIL] 仍残留 maybeAskClearApiKey"
assert "keyClearAsked" in s, "[FAIL] keyClearAsked 标记丢失"
LOG.append("旧函数名已清零，keyClearAsked 标记仍在使用")

assert s.count("v6.4.18") == 3, "[FAIL] v6.4.18 出现 %d 处（应为 3：BUILD + 常量 + 角标正文）" % s.count("v6.4.18")
# 大写 V6.4.18 共 2 处：更新日志条目 + 角标 title 文案
assert s.count("V6.4.18") == 2, "[FAIL] V6.4.18 出现 %d 处（应为 2）" % s.count("V6.4.18")
LOG.append("版本号：小写 v6.4.18 x3（BUILD/常量/角标正文）、大写 V6.4.18 x2（更新日志 + 角标 title）")

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
