
(function(){
  if(window.__rbV491) return; window.__rbV491 = true;
  var BUILD = 'v6.1.0', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;

  var TXT = {
    zh:  {h:'初始化失败', p:'页面在启动过程中遇到错误，部分或全部功能可能无法使用。请把下面的错误信息复制给开发者，以便定位问题。',
          ht:'页面启动超时', hp:'超过 10 秒仍未完成初始化。可能是浏览器扩展、安全策略或脚本错误阻塞了启动。',
          copy:'📋 复制错误信息', copied:'✅ 已复制，请粘贴给开发者', fail:'复制失败，请手动选中下方文字',
          reload:'🔄 重新加载', close:'关闭'},
    zht: {h:'初始化失敗', p:'頁面在啟動過程中遇到錯誤，部分或全部功能可能無法使用。請把下面的錯誤資訊複製給開發者，以便定位問題。',
          ht:'頁面啟動逾時', hp:'超過 10 秒仍未完成初始化。可能是瀏覽器擴充功能、安全策略或指令碼錯誤阻塞了啟動。',
          copy:'📋 複製錯誤資訊', copied:'✅ 已複製，請貼給開發者', fail:'複製失敗，請手動選取下方文字',
          reload:'🔄 重新載入', close:'關閉'},
    en:  {h:'Initialization failed', p:'The page hit an error while starting up, so some or all features may be unavailable. Please copy the details below and send them to the developer.',
          ht:'Startup timed out', hp:'Initialization did not finish within 10 seconds. A browser extension, security policy or script error may be blocking startup.',
          copy:'📋 Copy error details', copied:'✅ Copied - please paste it to the developer', fail:'Copy failed - please select the text manually',
          reload:'🔄 Reload', close:'Close'}
  };
  function lang(){
    try{ var v = localStorage.getItem('ai_optics_v1_lang'); if(v==='zh'||v==='zht'||v==='en') return v; }catch(e){}
    var n = String(navigator.language||navigator.userLanguage||'').toLowerCase();
    if(n.indexOf('zh')===0) return /hant|tw|hk|mo/.test(n) ? 'zht' : 'zh';
    return 'en';
  }
  function env(){
    return ['构建版本 : '+BUILD,
            '发生时间 : '+new Date().toString(),
            '页面地址 : '+location.href,
            '浏览器   : '+(navigator.userAgent||''),
            '视口/DPR : '+window.innerWidth+'x'+window.innerHeight+' @'+(window.devicePixelRatio||1),
            '界面语言 : '+document.documentElement.lang+' / '+lang()
           ].join('\n');
  }
  function mkBtn(label, bg, ink){
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.style.cssText = 'flex:0 0 auto;cursor:pointer;font:inherit;font-size:13px;font-weight:700;padding:8px 14px;'+
      'border-radius:9px;border:1px solid rgba(255,255,255,.18);background:'+bg+';color:'+ink+';';
    return b;
  }
  function show(kind, detail){
    if(dismissed || shown >= MAX_SHOW) return;
    shown++;
    var t = TXT[lang()] || TXT.zh;
    var box = document.createElement('div');
    box.id = '__rbOverlay';
    box.setAttribute('role','alertdialog');
    box.setAttribute('aria-modal','true');
    box.setAttribute('aria-live','assertive');
    box.style.cssText = 'position:fixed;inset:0;z-index:2147483600;background:rgba(8,8,6,.94);display:flex;'+
      'align-items:center;justify-content:center;padding:20px;box-sizing:border-box;'+
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;';

    var card = document.createElement('div');
    card.style.cssText = 'max-width:600px;width:100%;max-height:calc(100vh - 40px);overflow:auto;background:#161613;'+
      'color:#eef4dd;border:2px solid #ff6b5a;border-radius:14px;padding:20px 22px;box-shadow:0 16px 48px rgba(0,0,0,.65);';

    var h = document.createElement('div');
    h.textContent = '⚠️ ' + (kind === 'timeout' ? t.ht : t.h);
    h.style.cssText = 'font-size:19px;font-weight:800;color:#ff8a70;margin:0 0 10px;line-height:1.35;';

    var p = document.createElement('div');
    p.textContent = (kind === 'timeout' ? t.hp : t.p);
    p.style.cssText = 'font-size:14px;line-height:1.7;color:#cdd5b4;margin:0 0 14px;';

    var pre = document.createElement('pre');
    pre.textContent = detail;   /* 关键：用 textContent 而非 innerHTML，错误信息里含标签也不会造成注入 */
    pre.style.cssText = 'margin:0 0 16px;padding:12px;background:#0d0d0b;border:1px solid #3a3a33;border-radius:10px;'+
      'color:#e8f2ff;font-family:ui-monospace,Consolas,Monaco,monospace;font-size:12px;line-height:1.6;'+
      'white-space:pre-wrap;word-break:break-all;max-height:38vh;overflow:auto;user-select:text;-webkit-user-select:text;';

    var bc = mkBtn(t.copy, '#c8f04f', '#17150e');
    var br = mkBtn(t.reload, '#2a2a24', '#eef4dd');
    var bx = mkBtn(t.close, '#2a2a24', '#eef4dd');

    bc.onclick = function(){
      var ok = function(){ bc.textContent = t.copied; setTimeout(function(){ bc.textContent = t.copy; }, 2200); };
      /* file:// 或非安全上下文下 navigator.clipboard 不可用 —— 退回 textarea + execCommand */
      var fallback = function(){
        try{
          var ta = document.createElement('textarea');
          ta.value = detail;
          ta.setAttribute('readonly','readonly');
          ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0;';
          (document.body || document.documentElement).appendChild(ta);
          ta.select(); ta.setSelectionRange(0, detail.length);
          var done = document.execCommand('copy');
          ta.remove();
          if(done) ok(); else bc.textContent = t.fail;
        }catch(e2){ bc.textContent = t.fail; }
      };
      try{
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(detail).then(ok, fallback);
        } else fallback();
      }catch(e){ fallback(); }
    };
    br.onclick = function(){ location.reload(); };
    bx.onclick = function(){ dismissed = true; box.remove(); };

    var bar = document.createElement('div');
    bar.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;';
    bar.appendChild(bc); bar.appendChild(br); bar.appendChild(bx);

    card.appendChild(h); card.appendChild(p); card.appendChild(pre); card.appendChild(bar);
    box.appendChild(card);
    (document.body || document.documentElement).appendChild(box);
    try{ bx.focus(); }catch(e){}
  }
  function payload(kind, ev){
    var d = '';
    if(kind === 'error'){
      d = '未捕获异常：' + ((ev && ev.message) || '未知错误');
      if(ev && ev.filename) d += '\n位置：' + ev.filename + ':' + (ev.lineno || 0) + ':' + (ev.colno || 0);
      var st = ev && ev.error && ev.error.stack;
      if(st) d += '\n\n调用栈：\n' + String(st).split('\n').slice(0, 8).join('\n');
    } else if(kind === 'reject'){
      var r = ev && ev.reason;
      d = '未被处理的 Promise 拒绝：' + ((r && (r.message || r)) || '未知原因');
      if(r && r.stack) d += '\n\n调用栈：\n' + String(r.stack).split('\n').slice(0, 8).join('\n');
    } else {
      d = '启动超时：10 秒内未收到就绪信号（window.__APP_READY）。\n建议：点「复制错误信息」反馈给开发者，或强制刷新（Ctrl+F5）。';
    }
    return '【初中光学 · 交互实验室 ' + BUILD + '】\n' + d + '\n\n──── 环境信息 ────\n' + env();
  }
  function report(kind, ev){
    reported++;
    var detail = payload(kind, ev);
    try{ (window.__rbErrors = window.__rbErrors || []).push({ time: new Date().toISOString(), kind: kind, detail: detail }); }catch(e){}
    try{ console.error('[' + BUILD + '] ' + kind, (ev && (ev.error || ev.reason)) || ev); }catch(e){}
    /* 已成功启动之后才出现的异常：页面并没有"白屏"，此时弹全屏浮层只会打断正在使用的人 */
    if(window.__APP_READY) return;
    show(kind, detail);
  }

  /* 1) 运行时异常。capture:true 才能同时收到资源加载失败事件 */
  window.addEventListener('error', function(ev){
    var t = ev && ev.target;
    if(t && t !== window && t.nodeName){
      /* 资源类失败：<link> 字体、<img> 图片等。本作品可完全离线降级，不弹层 */
      try{ console.warn('[' + BUILD + '] 资源加载失败（已降级，不影响功能）：' +
        String(t.nodeName).toLowerCase() + ' ' + (t.src || t.href || '')); }catch(e){}
      return;
    }
    report('error', ev);
  }, true);

  /* 2) 未处理的 Promise 拒绝（await 里的失败不会触发上面的 error） */
  window.addEventListener('unhandledrejection', function(ev){ report('reject', ev); });

  /* 3) 启动看门狗：既不抛错也不就绪 = 卡在加载态，用户同样需要看到提示 */
  window.__rbMarkReady = function(){ window.__APP_READY = true; };
  window.__rbShowLast = function(){
    if(window.__rbErrors && window.__rbErrors.length){
      dismissed = false; shown = 0;
      show('error', window.__rbErrors[window.__rbErrors.length - 1].detail);
    }
  };
  setTimeout(function(){
    if(window.__APP_READY || reported > 0) return;
    report('timeout', null);
  }, 10000);
})();
