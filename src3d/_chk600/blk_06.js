
(function(){
  'use strict';
  if(!window.gsap) return;                 /* 降级：无 GSAP 则一切照旧 */
  if(window.__opticsGsapReady) return;     /* 防重复注入 */
  window.__opticsGsapReady = true;

  gsap.defaults({ ease:'power2.out', duration:0.45 });

  /* 无障碍：系统开启"减少动态效果"时不创建任何动画 */
  var motionOK = true;
  try{ motionOK = !window.matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){}

  /* 收集一个面板内需要入场动画的内容元素 */
  function panelItems(sel){
    return document.querySelectorAll(sel+' canvas, '+sel+' .ctrl, '+sel+' .card, '+
                                     sel+' .verdict, '+sel+' .data-panel');
  }
  var obs = [];
  function watch(el, cfg, fn){
    var o = new MutationObserver(fn); o.observe(el, cfg); obs.push(o); return o;
  }

  if(motionOK){
    /* ---- 1. 首屏进入：顶栏 → tab 按钮 → 首个实验内容（时间线编排） ----
          用 fromTo 显式端点 + clearProps，避免 from() 端点被自身起始态污染，
          动画结束后不残留内联 transform（否则 tab 按钮会停在偏移位置）
          V4.9.2：原「副标题 .sub」一步已移除——该行已移入关于弹窗，首屏不再存在 */
    gsap.timeline({ defaults:{ ease:'power3.out' } })
      .fromTo('.topbar', { y:-16, autoAlpha:0 }, { y:0, autoAlpha:1, duration:0.5, clearProps:'transform' })
      .fromTo('.topbar-right > *', { y:-8, autoAlpha:0 },
              { y:0, autoAlpha:1, duration:0.3, stagger:0.05, clearProps:'transform' }, 0.15)
      .fromTo('.tab-btn', { y:12, autoAlpha:0 },
              { y:0, autoAlpha:1, duration:0.35, stagger:0.045, clearProps:'transform' }, '-=0.18')
      .fromTo(panelItems('#tab-reflect'), { y:16, autoAlpha:0 },
              { y:0, autoAlpha:1, duration:0.45, stagger:0.05, clearProps:'transform' }, '-=0.12');
  }

  /* ---- 2. tab 切换：增强原生 switchTab（只追加动画，不替换逻辑） ----
        新面板内容交错上浮 + 当前 tab 按钮回弹 Pop（panelIn CSS 保留） */
  if(typeof window.switchTab === 'function'){
    var _switchTab = window.switchTab;
    window.switchTab = function(name){
      _switchTab(name);
      if(!motionOK) return;
      gsap.fromTo(panelItems('#tab-'+name),
        { y:14, autoAlpha:0 },
        { y:0, autoAlpha:1, duration:0.4, stagger:0.04, overwrite:'auto', clearProps:'transform' });
      var btn = document.querySelector('.tab-btn[data-tab="'+name+'"]');
      if(btn) gsap.fromTo(btn, { scale:0.9 },
        { scale:1, duration:0.4, ease:'back.out(3)', overwrite:'auto', clearProps:'scale' });
    };
  }

  if(motionOK){
    /* ---- 3. 全局按钮按压微交互（事件委托，动态创建的按钮同样生效） ----
          按下轻缩放，松开弹性回弹；clearProps 后交还 V3 自带 CSS hover 位移 */
    var pressed = null;
    function pressable(t){
      return t && t.closest && t.closest('button, .ai-status');
    }
    var onDown = function(e){
      var el = pressable(e.target);
      if(!el) return;
      pressed = el;
      gsap.to(el, { scale:0.93, duration:0.1, ease:'power2.out', overwrite:'auto' });
    };
    var onUp = function(){
      if(!pressed) return;
      gsap.to(pressed, { scale:1, duration:0.45, ease:'elastic.out(1,0.45)',
                         overwrite:'auto', clearProps:'scale' });
      pressed = null;
    };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('pointerup', onUp, true);
    document.addEventListener('pointercancel', onUp, true);

    /* ---- 4. 弹窗遮罩淡入（.modal 本体由 V3 自带 modalIn/staggerIn 负责，不重复做） ---- */
    function hookMask(mask){
      if(mask.__gsapHook) return; mask.__gsapHook = true;
      watch(mask, { attributes:true, attributeFilter:['class'] }, function(){
        if(mask.classList.contains('show'))
          gsap.fromTo(mask, { autoAlpha:0 }, { autoAlpha:1, duration:0.22, overwrite:'auto' });
      });
    }
    document.querySelectorAll('.modal-mask').forEach(hookMask);

    /* ---- 5. 数据记录表：新增行左滑入 ---- */
    document.querySelectorAll('.dtable tbody').forEach(function(tb){
      watch(tb, { childList:true }, function(muts){
        muts.forEach(function(mu){
          mu.addedNodes.forEach(function(n){
            if(n.nodeType===1 && n.tagName==='TR')
              gsap.from(n, { x:-16, autoAlpha:0, duration:0.35, clearProps:'transform' });
          });
        });
      });
    });

    /* ---- 6. 判定结论 verdict：结论标签 Pop（300ms 节流，防止拖滑块时刷屏） ---- */
    document.querySelectorAll('.verdict').forEach(function(v){
      var last = 0;
      watch(v, { childList:true, subtree:true }, function(){
        var now = Date.now(); if(now - last < 300) return; last = now;
        var tags = v.querySelectorAll('.tag');
        if(tags.length) gsap.from(tags, { scale:0.6, autoAlpha:0, duration:0.32,
          stagger:0.04, ease:'back.out(2.2)', overwrite:'auto', clearProps:'scale' });
      });
    });

    /* ---- 7. AI 学伴回答框：展示时上滑淡入 ---- */
    function hookTalk(box){
      if(box.__gsapHook) return; box.__gsapHook = true;
      watch(box, { attributes:true, attributeFilter:['class'] }, function(){
        if(box.classList.contains('show'))
          gsap.fromTo(box, { y:10, autoAlpha:0 },
            { y:0, autoAlpha:1, duration:0.35, overwrite:'auto' });
      });
    }
    document.querySelectorAll('.ai-talk').forEach(hookTalk);

    /* ---- 8. 主题按钮：黑板/纸黄切换时弹性旋转反馈 ---- */
    var themeBtn = document.getElementById('themeBtn');
    if(themeBtn) themeBtn.addEventListener('click', function(){
      gsap.fromTo(themeBtn, { rotation:-10 },
        { rotation:0, duration:0.55, ease:'elastic.out(1,0.4)', overwrite:'auto', clearProps:'rotation' });
    });

    /* ---- 9. 后续动态插入的弹窗 / AI 面板自动挂钩 ---- */
    new MutationObserver(function(muts){
      muts.forEach(function(mu){
        mu.addedNodes.forEach(function(n){
          if(n.nodeType!==1 || !n.classList) return;
          if(n.classList.contains('modal-mask')) hookMask(n);
          if(n.classList.contains('ai-talk')) hookTalk(n);
          if(n.querySelectorAll){
            n.querySelectorAll('.modal-mask').forEach(hookMask);
            n.querySelectorAll('.ai-talk').forEach(hookTalk);
          }
        });
      });
    }).observe(document.body, { childList:true, subtree:true });
  }
})();
