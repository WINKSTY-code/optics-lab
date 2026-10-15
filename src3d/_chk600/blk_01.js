
/* V5.0.1 修复：matchMedia 缺失保护 + 外层 try-catch（V5.0.0 在某些手机浏览器因
   window.matchMedia 不存在导致整个 JS 链中断，引发 noscript 兜底） */
try{
(function(){
  if(window.__v5Device) return; window.__v5Device = true;
  /* matchMedia 安全封装：缺失/抛错时返回 noop 对象 */
  function safeMq(q){
    try{
      var m = window.matchMedia(q);
      return m || {matches:false, addEventListener:function(){}, removeEventListener:function(){}};
    }catch(e){
      return {matches:false, addEventListener:function(){}, removeEventListener:function(){}};
    }
  }
  function detect(){
    try{
      var ua = navigator.userAgent || '';
      // iPadOS 13+ 在桌面 UA 下伪装 Mac，需排除
      var isPhoneUA = /Mobile|iPhone|iPad|Android.*Mobile|HarmonyOS|Windows Phone/i.test(ua)
                   && !/iPad.*Macintosh/.test(ua);
      var mq0 = safeMq('(max-width: 880px)');
      var isNarrow = mq0.matches;
      var hasTouch = (navigator.maxTouchPoints || 0) > 1;
      // 综合判定：UA 命中 或 (窄屏 + 触屏) 命中
      var mobile = isPhoneUA || (isNarrow && hasTouch);
      if(document.documentElement && document.documentElement.dataset){
        document.documentElement.dataset.mode = mobile ? 'mobile' : 'desktop';
      }
      window.__IS_MOBILE = mobile;
      return mobile;
    }catch(e){
      try{ if(document.documentElement) document.documentElement.dataset.mode = 'desktop'; }catch(_){}
      window.__IS_MOBILE = false;
      return false;
    }
  }
  detect();
  // 跟随屏幕旋转 / 窗口大小变化（matchMedia 缺失/抛错时整段静默跳过）
  try{
    var mq = safeMq('(max-width: 880px)');
    var lastNarrow = mq.matches;
    if(mq.addEventListener){
      mq.addEventListener('change', function(e){
        if(e.matches !== lastNarrow){ lastNarrow = e.matches; detect(); }
      });
    }
  }catch(e){ /* matchMedia 不可用，跳过响应式监听 */ }
})();
}catch(e){
  /* 整块 V5 IS_MOBILE 抛错兜底：必须不让它打断后续 V4.9.1 兜底 setTimeout */
  try{ window.__IS_MOBILE = false; }catch(_){}
}
