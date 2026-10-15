
// v3 视觉增强：实验数值变化时数字跳动（纯展示，只读 Observer，不改功能）
(function(){
  if(!window.MutationObserver) return;
  var io = new MutationObserver(function(muts){
    muts.forEach(function(mu){
      var el = mu.target;
      if(el && el.classList && !el.classList.contains('pop')){
        el.classList.add('pop');
        setTimeout(function(){ el.classList.remove('pop'); }, 380);
      }
    });
  });
  document.querySelectorAll('.readout .card b').forEach(function(b){
    io.observe(b, { childList:true, characterData:true, subtree:true });
  });
})();
