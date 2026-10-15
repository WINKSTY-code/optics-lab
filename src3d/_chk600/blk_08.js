
(function(){
  if(window.__a11yV49) return; window.__a11yV49 = true;

  var uid = 0, curMask = null, lastFocus = null;

  /* --- .modal 补 dialog 语义（内容被 showModal() 整体替换后会重新计算） --- */
  function decorate(mask){
    var m = mask.querySelector('.modal'); if(!m) return;
    var h = m.querySelector('h2,h3,.modal-title');
    if(h){
      if(!h.id) h.id = 'a11y-ttl-' + (++uid);
      if(m.getAttribute('aria-labelledby') !== h.id) m.setAttribute('aria-labelledby', h.id);
      if(m.hasAttribute('aria-label')) m.removeAttribute('aria-label');
    }else{
      if(m.hasAttribute('aria-labelledby')) m.removeAttribute('aria-labelledby');
      var t = (m.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 50);
      m.setAttribute('aria-label', t || '对话框');
    }
    if(m.getAttribute('role') !== 'dialog') m.setAttribute('role', 'dialog');
    if(m.getAttribute('aria-modal') !== 'true') m.setAttribute('aria-modal', 'true');
  }

  /* --- 可见的可聚焦元素 --- */
  function focusables(root){
    var sel = 'button:not([disabled]),[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
    return Array.prototype.filter.call(root.querySelectorAll(sel), function(el){
      return el.getClientRects().length > 0;
    });
  }
  function focusFirst(mask){
    var m = mask.querySelector('.modal'); if(!m) return;
    if(!m.hasAttribute('tabindex')) m.setAttribute('tabindex', '-1');
    var f = focusables(m);
    var target = f[0] || m;
    try{ target.focus({ preventScroll: true }); }catch(e){ try{ target.focus(); }catch(e2){} }
  }

  /* --- 显示 / 隐藏：切换语义与焦点 --- */
  function sync(mask){
    var shown = mask.classList.contains('show');
    var prev  = mask.__a11yShown === true;
    if(shown === prev) return;
    mask.__a11yShown = shown;
    if(shown){
      mask.removeAttribute('aria-hidden');
      decorate(mask);
      lastFocus = document.activeElement;
      curMask = mask;
      setTimeout(function(){ if(curMask === mask) focusFirst(mask); }, 30);
    }else{
      if(curMask === mask) curMask = null;
      if(lastFocus && document.contains(lastFocus)){
        try{ lastFocus.focus({ preventScroll: true }); }catch(e){}
      }
      lastFocus = null;
      mask.setAttribute('aria-hidden', 'true');
    }
  }

  /* --- 挂钩（静态 + 动态插入的弹窗） --- */
  function reDecorate(mask){
    decorate(mask);
    if(!mask.classList.contains('show')) return;
    var m = mask.querySelector('.modal'); if(!m) return;
    // showModal() 用 innerHTML 整体替换内容 → 旧焦点节点已消失，收回弹窗内第一个可交互元素
    if(!m.contains(document.activeElement)) focusFirst(mask);
  }
  var pending = null;

  /* ============================================================
     V4.9.13 · 弹窗退场拦截器（全站唯一收口）
     问题：站内关闭弹窗有 5 类写法，逐处改动画既易漏又易回归：
       ① closeModal()
       ② 各关闭/取消按钮：mask.classList.remove('show')
       ③ Esc 键
       ④ 点遮罩空白处
       ⑤ 「跳转实验 / 跳转挑战」时先隐弹窗再切 tab
     做法：**不看谁在关，只看 .show 被移除这件事**。
     用 MutationObserver 观察 class：一旦发现「原本显示 → show 消失 且 尚未在退场中」，
     立刻把 show 补回去、改为加 .is-closing 走退场动画，动画结束再真正移除 show。
     这样任何路径（含以后新写的）都自动获得退场动画，不存在遗漏。
     ============================================================ */
  var CLOSE_MS = 260;   // 与 CSS maskOut/modalOut 时长一致

  function playExit(mask){
    if(mask.__closing) return;
    mask.__closing = true;
    mask.classList.add('is-closing');

    var done = false;
    var finish = function(){
      if(done) return; done = true;
      mask.removeEventListener('animationend', onEnd);
      // 关键顺序：先摘 show，再摘 is-closing。
      // 且先落 __exitDone 标记 —— 否则下面的 class 变更会再触发拦截器，
      // 判定"想关却没关成"，于是重新 add('show')+is-closing，形成死循环
      // （首版实测：class 每帧被改 3 次、动画永远播不完）。
      mask.__exitDone = true;
      mask.classList.remove('show');
      mask.classList.remove('is-closing');
      mask.__closing = false;
    };
    var onEnd = function(ev){
      if(ev.target === mask) finish();
    };
    // 只监听遮罩自身那条 maskOut（面板那条与之同时长，不必重复监听）
    mask.addEventListener('animationend', onEnd);
    // 兜底：prefers-reduced-motion / 动画被浏览器跳过时，靠超时收尾
    setTimeout(finish, CLOSE_MS + 80);
  }

  function hookExit(mask){
    if(mask.__exitHook) return; mask.__exitHook = true;
    new MutationObserver(function(muts){
      muts.forEach(function(mu){
        var was   = mu.oldValue || '';
        var hadShow = was.indexOf('show') >= 0;
        var hasShow = mask.classList.contains('show');
        // __exitDone：本轮关闭已完成，这次 remove('show') 是收尾动作，放行
        // __closing ：退场动画正在播，放行
        if(hadShow && !hasShow && !mask.__closing && !mask.__exitDone){
          mask.classList.add('show');
          playExit(mask);
        }
        // 重新打开时清掉"已完成"标记，下次关闭仍能正常播动画
        if(!hadShow && hasShow) mask.__exitDone = false;
      });
    }).observe(mask, { attributes: true, attributeFilter: ['class'], attributeOldValue: true });
  }

  /* 退场途中被重新打开（典型：aiCfgMask 复用，关掉又在 260ms 内打开）→ 撤销退场，原地复活 */
  function cancelExit(mask){
    if(!mask.__closing) return;
    mask.__closing = false;
    mask.classList.remove('is-closing');
    if(!mask.classList.contains('show')) mask.classList.add('show');
  }

  function hook(mask){
    if(mask.__a11yHook) return; mask.__a11yHook = true;
    if(!mask.classList.contains('show')) mask.setAttribute('aria-hidden', 'true');
    decorate(mask);
    new MutationObserver(function(){ sync(mask); })
      .observe(mask, { attributes: true, attributeFilter: ['class'] });
    hookExit(mask);
    var m = mask.querySelector('.modal');
    if(m){
      // 只观察 .modal 的直接子节点：innerHTML 替换会触发，回答区内部追加不会
      new MutationObserver(function(){
        if(pending) clearTimeout(pending);
        pending = setTimeout(function(){ pending = null; reDecorate(mask); }, 60);
      }).observe(m, { childList: true });
    }
    sync(mask);
  }
  function scan(root){
    if(!root || root.nodeType !== 1 || !root.classList) return;
    if(root.classList.contains('modal-mask')) hook(root);
    if(root.querySelectorAll) Array.prototype.forEach.call(root.querySelectorAll('.modal-mask'), hook);
  }
  Array.prototype.forEach.call(document.querySelectorAll('.modal-mask'), hook);
  new MutationObserver(function(muts){
    muts.forEach(function(mu){ Array.prototype.forEach.call(mu.addedNodes, scan); });
  }).observe(document.body, { childList: true, subtree: true });

  /* --- Esc：关闭最上层弹窗。优先点它自带的「关闭/取消」按钮，等价于用户手动操作 --- */
  document.addEventListener('keydown', function(e){
    if(e.key !== 'Escape' && e.key !== 'Esc') return;
    var shown = Array.prototype.filter.call(document.querySelectorAll('.modal-mask'),
      function(x){ return x.classList.contains('show'); });
    if(!shown.length) return;
    var top = shown[shown.length - 1];
    var btns = top.querySelectorAll('button'), target = null;
    for(var i = btns.length - 1; i >= 0; i--){
      if(/(close|cancel)$/.test((btns[i].id || '').toLowerCase())){ target = btns[i]; break; }
    }
    e.preventDefault(); e.stopPropagation();
    if(target && !target.disabled) target.click();
    else top.classList.remove('show');
  }, true);

  /* --- Tab：把焦点圈定在当前弹窗内 --- */
  document.addEventListener('keydown', function(e){
    if(e.key !== 'Tab' || !curMask) return;
    var m = curMask.querySelector('.modal'); if(!m) return;
    var f = focusables(m);
    if(!f.length) return;
    var first = f[0], last = f[f.length - 1], ae = document.activeElement;
    if(!m.contains(ae)){ e.preventDefault(); first.focus(); return; }
    if(e.shiftKey && ae === first){ e.preventDefault(); last.focus(); }
    else if(!e.shiftKey && ae === last){ e.preventDefault(); first.focus(); }
  }, true);
})();
