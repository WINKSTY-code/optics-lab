
/* V5.0.1 修复：外层 try-catch + 内部细粒度 try-catch
   任何抛错都被兜底，不影响其他 JS（包括 V4.9.1 兜底） */
try{
(function(){
  if(window.__v5Mobile) return; window.__v5Mobile = true;

  // 监听 ready 事件统一处理（addEventListener 可能抛错，安全包裹）
  function onReady(fn){
    try{
      if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', fn);
      } else { fn(); }
    }catch(e){ /* DOM API 异常时直接同步执行 */ try{ fn(); }catch(_){} }
  }

  onReady(function(){
    if(!window.__IS_MOBILE) return;   // 桌面端整体跳过

    /* ---------- 1) 触控抖动抑制（只对 canvas pointermove 生效） ---------- */
    var lastPt = null;
    function shouldThrottle(e){
      if(!e.isPrimary) return false;  // 多点触控时不抑制
      var now = Date.now();
      if(lastPt && (now - lastPt.t < 16)) return true;          // < 60fps 上限
      if(lastPt && Math.hypot(e.clientX - lastPt.x, e.clientY - lastPt.y) < 2
                 && (now - lastPt.t < 60)) return true;        // < 2px 微抖动
      lastPt = {x:e.clientX, y:e.clientY, t:now};
      return false;
    }
    document.querySelectorAll('canvas[id^="cv-"]').forEach(function(cv){
      cv.addEventListener('pointermove', function(e){
        if(e.pointerType !== 'touch') return;   // 鼠标/笔不抑制
        if(shouldThrottle(e)){ e.stopPropagation(); }
      }, true);
    });

    /* ---------- 2) 长按气泡（补偿触屏无 hover） ---------- */
    var bubble = null, holdTimer = null, holdActiveCv = null;
    function ensureBubble(){
      if(bubble) return bubble;
      bubble = document.createElement('div');
      bubble.id = '__v5HoldBubble';
      bubble.style.cssText = 'position:fixed;z-index:60;display:none;pointer-events:none;'+
        'background:var(--panel);color:var(--txt);border:2px solid var(--line);border-radius:8px;'+
        'padding:6px 10px;font-size:12px;font-weight:700;box-shadow:3px 3px 0 var(--line);'+
        'font-family:inherit;line-height:1.4;max-width:60vw;';
      document.body.appendChild(bubble);
      return bubble;
    }
    function showBubble(cv, x, y, text){
      var b = ensureBubble();
      b.textContent = text;
      b.style.display = 'block';
      // 防止溢出屏幕
      var rect = b.getBoundingClientRect();
      var left = Math.min(x + 12, window.innerWidth - rect.width - 8);
      var top  = Math.min(y + 12, window.innerHeight - rect.height - 8);
      b.style.left = Math.max(8, left) + 'px';
      b.style.top  = Math.max(8, top) + 'px';
    }
    function hideBubble(){ if(bubble) bubble.style.display = 'none'; }

    document.querySelectorAll('canvas[id^="cv-"]').forEach(function(cv){
      cv.addEventListener('pointerdown', function(e){
        if(e.pointerType !== 'touch') return;
        holdActiveCv = cv;
        var rect = cv.getBoundingClientRect();
        var localX = e.clientX - rect.left;
        var localY = e.clientY - rect.top;
        clearTimeout(holdTimer);
        holdTimer = setTimeout(function(){
          if(!holdActiveCv) return;
          var r = cv.getBoundingClientRect();
          // 通用文案：实际坐标（用户可据此估计入射/反射/折射等角度）
          var px = Math.round(localX * (cv.width / r.width));
          var py = Math.round(localY * (cv.height / r.height));
          var id = cv.id.replace('cv-', '');
          showBubble(cv, e.clientX, e.clientY, '✋ ' + id + ' · (' + px + ', ' + py + ')');
        }, 600);
      });
      function cancelHold(){
        clearTimeout(holdTimer);
        holdTimer = null;
        holdActiveCv = null;
        hideBubble();
      }
      cv.addEventListener('pointermove', function(e){
        if(e.pointerType === 'touch' && holdTimer){ clearTimeout(holdTimer); holdTimer = null; }
      });
      cv.addEventListener('pointerup', cancelHold);
      cv.addEventListener('pointercancel', cancelHold);
      cv.addEventListener('pointerleave', cancelHold);
    });

    /* ---------- 3) iOS 全屏 fallback ---------- */
    var fsBtn = document.getElementById('fsBtn');
    if(fsBtn){
      fsBtn.addEventListener('click', function(ev){
        // iOS Safari / 微信内置浏览器不支持 fullscreen API
        var isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;
        var noFsApi = !(document.documentElement.requestFullscreen ||
                        document.documentElement.webkitRequestFullscreen);
        if(isIOS || noFsApi){
          ev.stopImmediatePropagation();
          ev.preventDefault();
          var tip = isIOS
            ? '💡 iOS 暂不支持网页全屏，请点击「分享 → 添加到主屏幕」，可获得类 App 体验'
            : '💡 当前浏览器不支持全屏 API';
          if(window.__IS_MOBILE && typeof alert === 'function'){
            // 简易提示气泡，2.5s 自动消失（不阻塞）
            var t = document.createElement('div');
            t.style.cssText = 'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);'+
              'background:var(--panel);color:var(--txt);border:2px solid var(--line);border-radius:10px;'+
              'padding:14px 18px;font-size:14px;z-index:100;box-shadow:4px 4px 0 var(--line);'+
              'max-width:80vw;text-align:center;line-height:1.5;';
            t.textContent = tip;
            document.body.appendChild(t);
            setTimeout(function(){ if(t.parentNode) t.parentNode.removeChild(t); }, 3000);
          }
          return false;
        }
      }, true);
    }

    /* ---------- 4) AI 弹窗键盘适配（iOS 输入法弹出时页面回弹修复） ---------- */
    document.addEventListener('focusin', function(e){
      if(!e.target.matches || !e.target.matches('input,textarea')) return;
      // iOS 在虚拟键盘弹出时可能把视口滚动到奇怪位置
      setTimeout(function(){
        try{ window.scrollTo(0, 0); }catch(_){}
        // 让被遮挡元素滚到视口中央
        try{ e.target.scrollIntoView({block:'center', behavior:'smooth'}); }catch(_){}
      }, 280);
    });
  });
})();
}catch(e){
  /* V5.0.1：外层兜底。任何抛错都吃掉，绝不让它打断后续 V4.9.1 兜底启动看门狗 */
  try{ if(window.console && console.warn) console.warn('[V5 移动端交互] 初始化失败', e); }catch(_){}
}
