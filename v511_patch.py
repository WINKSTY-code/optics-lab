# -*- coding: utf-8 -*-
"""
V5.1.1 补丁：实验报告自动生成（探究六要素结构化输出 + 一键导出）
基线：光学交互实验室_AI_v5.1.0.html
产物：光学交互实验室_AI_v5.1.1.html
所有替换均带命中数断言，任一处不符立即中止。
"""
import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v5.1.0.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v5.1.1.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


# ============================================================ 报告面板 CSS
CSS_BLOCK = r"""
/* ==========================================================================
   V5.1.1 · 实验报告（科学探究六要素）
   ========================================================================== */
.rpt-head{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:flex-end;
  background:var(--panel);border:var(--hard-border);border-radius:10px;padding:12px 14px;box-shadow:var(--shadow);}
.rpt-hl{min-width:240px;flex:1 1 auto;}
.rpt-h2{margin:0 0 5px;font-size:18px;line-height:1.35;}
.rpt-sub{margin:0;font-size:12.5px;color:var(--muted);line-height:1.65;}
.rpt-hr{display:flex;flex-wrap:wrap;gap:9px;align-items:center;}
.rpt-sel{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--muted);font-weight:700;}
.rpt-sel select,.rpt-sel input{font-family:inherit;font-size:12.5px;font-weight:700;color:var(--txt);
  background:var(--panel);border:2px solid var(--line);border-radius:7px;padding:5px 8px;box-shadow:2px 2px 0 var(--line);}
.rpt-sel input#rpt-name{width:96px;}
.rpt-sel input#rpt-peerName{width:88px;font-size:12px;padding:3px 7px;box-shadow:none;}
.rpt-prog{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:12px;padding:10px 14px;
  background:var(--panel);border:var(--hard-border);border-radius:10px;box-shadow:var(--shadow);}
.rpt-bar{flex:1 1 180px;height:14px;background:var(--sec-bg);border:2px solid var(--line);border-radius:20px;overflow:hidden;min-width:140px;}
.rpt-bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .45s cubic-bezier(.16,1,.3,1);}
#rpt-progTxt{font-size:13px;font-weight:700;white-space:nowrap;}
.rpt-dots{display:flex;gap:5px;}
.rpt-dot{width:11px;height:11px;border-radius:50%;border:2px solid var(--line);background:transparent;display:inline-block;}
.rpt-dot.on{background:var(--green);}
.rpt-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;}
.rpt-card{background:var(--panel);border:var(--hard-border);border-radius:10px;padding:0 0 12px;
  box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column;}
.rpt-card.wide{grid-column:1 / -1;}
.rpt-ch{display:flex;align-items:center;gap:8px;padding:9px 12px;background:var(--sec-bg);color:var(--sec-txt);
  border-bottom:2px solid var(--line);}
.rpt-ch b{font-size:15px;}
.rpt-no{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;flex:0 0 22px;
  border-radius:50%;background:var(--accent);color:var(--accent-ink);border:2px solid var(--line);font-size:12.5px;font-weight:800;}
.rpt-badge{margin-left:auto;font-size:11.5px;font-weight:700;padding:2px 9px;border-radius:20px;
  border:1px solid var(--line);background:var(--accent);color:var(--accent-ink);white-space:nowrap;}
.rpt-badge.todo{background:transparent;color:var(--muted);border-style:dashed;}
.rpt-badge.warn{background:var(--red);color:#fff;}
.rpt-cb{padding:11px 12px 0;font-size:13.5px;line-height:1.7;overflow-wrap:anywhere;}
.rpt-cb p{margin:0 0 8px;}
.rpt-q{font-size:14.5px;font-weight:700;line-height:1.65;padding-left:11px;border-left:5px solid var(--accent);}
.rpt-row{display:flex;gap:9px;margin-bottom:9px;}
.rpt-k{flex:0 0 62px;font-size:12.5px;color:var(--muted);font-weight:700;line-height:1.75;}
.rpt-v{flex:1 1 auto;min-width:0;}
.rpt-v ol{margin:0;padding-left:19px;}
.rpt-v ol li{margin-bottom:3px;}
.rpt-v .vr{display:block;margin-bottom:2px;}
.rpt-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}
.rpt-chip{background:var(--panel);color:var(--txt);border:1px dashed var(--line);border-radius:20px;
  padding:3px 10px;font-size:12px;font-weight:700;cursor:pointer;transition:background .18s,transform .18s;}
.rpt-chip:hover{background:var(--accent);transform:translateY(-1px);}
.rpt-card textarea{width:100%;font-family:inherit;font-size:13.5px;line-height:1.7;color:var(--txt);
  background:var(--panel);border:2px solid var(--line);border-radius:8px;padding:8px 10px;box-shadow:inset 2px 2px 0 var(--sep);
  resize:vertical;margin-bottom:9px;}
.rpt-card textarea:focus{outline:2px solid var(--blue);outline-offset:1px;}
.rpt-databox{border:2px solid var(--line);border-radius:8px;overflow:auto;max-height:260px;background:var(--panel);}
.rpt-dt{width:100%;border-collapse:collapse;font-size:12px;}
.rpt-dt th,.rpt-dt td{border:1px solid var(--line);padding:5px 7px;text-align:center;white-space:nowrap;}
.rpt-dt th{background:var(--sec-bg);color:var(--sec-txt);font-weight:700;position:sticky;top:0;}
.rpt-dt td:last-child{text-align:left;white-space:normal;min-width:120px;}
.rpt-live{margin-top:8px;font-size:12.5px;color:var(--muted);line-height:1.7;}
.rpt-live b{color:var(--blue);}
body.light .rpt-live b{color:var(--accent);}
.rpt-empty{border:2px dashed var(--line);border-radius:8px;padding:14px;font-size:13px;color:var(--muted);line-height:1.7;}
.rpt-concl{background:var(--verdict-bg);border:2px solid var(--verdict-line);border-left-width:8px;
  border-radius:8px;padding:10px 12px;}
.rpt-concl .claim{font-size:14px;line-height:1.75;}
.rpt-concl .evid{margin-top:7px;font-size:12.5px;color:var(--muted);line-height:1.7;}
.rpt-concl .sup{margin-top:7px;font-size:12.5px;line-height:1.7;padding-top:7px;border-top:1px dashed var(--line);}
.rpt-eval{margin-top:4px;border-top:1px dashed var(--line);padding-top:9px;display:flex;flex-direction:column;gap:7px;}
.rpt-evrow{display:flex;align-items:center;gap:9px;flex-wrap:wrap;font-size:13px;font-weight:700;}
.rpt-evrow>span:first-child{flex:0 0 34px;color:var(--muted);font-size:12.5px;}
.rpt-stars{display:inline-flex;gap:3px;}
.rpt-star{font-size:19px;line-height:1;color:var(--sep);cursor:pointer;user-select:none;
  transition:color .15s,transform .15s;}
.rpt-star:hover{transform:scale(1.18);}
.rpt-star.on{color:var(--accent);text-shadow:1px 1px 0 var(--line);}
.rpt-star:focus-visible{outline:2px solid var(--blue);outline-offset:2px;border-radius:4px;}
.rpt-act{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-top:12px;padding:12px 14px;
  background:var(--panel);border:var(--hard-border);border-radius:10px;box-shadow:var(--shadow);}
.rpt-tip{font-size:12.5px;color:var(--muted);font-weight:700;margin-left:auto;}
@media(max-width:880px){
  .rpt-grid{grid-template-columns:1fr;}
  .rpt-card.wide{grid-column:auto;}
  .rpt-h2{font-size:16px;}
}
html[data-mode="mobile"] .rpt-head,html[data-mode="mobile"] .rpt-prog,
html[data-mode="mobile"] .rpt-act{padding:10px 11px;}
html[data-mode="mobile"] .rpt-h2{font-size:15.5px;}
html[data-mode="mobile"] .rpt-sub{font-size:11.5px;}
html[data-mode="mobile"] .rpt-cb{font-size:13px;padding:10px 10px 0;}
html[data-mode="mobile"] .rpt-cb textarea,
html[data-mode="mobile"] .rpt-sel select,
html[data-mode="mobile"] .rpt-sel input{font-size:16px;}   /* 防 iOS 聚焦缩放 */
html[data-mode="mobile"] .rpt-dt{font-size:11px;}
html[data-mode="mobile"] .rpt-dt th,html[data-mode="mobile"] .rpt-dt td{padding:4px 5px;}
html[data-mode="mobile"] .rpt-databox{max-height:210px;}
html[data-mode="mobile"] .rpt-act button{flex:1 1 46%;font-size:12.5px;padding:8px 10px;}
html[data-mode="mobile"] .rpt-tip{flex:1 1 100%;margin-left:0;text-align:center;}
html[data-mode="mobile"] .rpt-star{font-size:22px;}
html[data-mode="mobile"] .rpt-k{flex:0 0 54px;}
"""

# ============================================================ 报告面板 HTML
PANEL_HTML = r"""
  <!-- ================= 12 实验报告（V5.1.1 六要素自动生成） ================= -->
  <section id="tab-report" class="panel">
    <div class="rpt-head">
      <div class="rpt-hl">
        <h2 class="rpt-h2" data-i18n="rpt.title">📝 实验报告 · 科学探究六要素</h2>
        <p class="rpt-sub" data-i18n="rpt.sub">按「问题 → 猜想 → 方案 → 数据 → 结论 → 反思」组织。问题、方案、数据表、结论由各实验画布的真实参数自动取值；猜想与反思由你填写，写完即可一键导出。</p>
      </div>
      <div class="rpt-hr">
        <label class="rpt-sel"><span data-i18n="rpt.exp">实验</span><select id="rpt-exp" aria-label="选择实验"></select></label>
        <label class="rpt-sel"><span data-i18n="rpt.who">姓名</span><input id="rpt-name" type="text" maxlength="12" placeholder="选填"></label>
        <label class="rpt-sel"><span data-i18n="rpt.date">日期</span><input id="rpt-date" type="date"></label>
        <button id="rpt-refresh" class="sec" data-i18n="rpt.refresh">↻ 重新取值</button>
      </div>
    </div>

    <div class="rpt-prog">
      <div class="rpt-bar"><i id="rpt-bar"></i></div>
      <span id="rpt-progTxt" aria-live="polite">六要素完成度 0 / 6</span>
      <span class="rpt-dots" id="rpt-dots" aria-hidden="true"></span>
    </div>

    <div class="rpt-grid">
      <div class="rpt-card">
        <div class="rpt-ch"><span class="rpt-no">1</span><b data-i18n="rpt.s1">问题</b><span class="rpt-badge" id="rpt-b1">自动</span></div>
        <div class="rpt-cb" id="rpt-q"></div>
      </div>

      <div class="rpt-card">
        <div class="rpt-ch"><span class="rpt-no">2</span><b data-i18n="rpt.s2">猜想</b><span class="rpt-badge todo" id="rpt-b2">待填写</span></div>
        <div class="rpt-cb">
          <div class="rpt-chips" id="rpt-guess"></div>
          <textarea id="rpt-hypo" rows="3" data-i18n-ph="rpt.ph.hypo" placeholder="写下你的猜想（可点上方预设句一键填入）"></textarea>
        </div>
      </div>

      <div class="rpt-card">
        <div class="rpt-ch"><span class="rpt-no">3</span><b data-i18n="rpt.s3">方案</b><span class="rpt-badge" id="rpt-b3">自动</span></div>
        <div class="rpt-cb" id="rpt-plan"></div>
      </div>

      <div class="rpt-card">
        <div class="rpt-ch"><span class="rpt-no">4</span><b data-i18n="rpt.s4">数据</b><span class="rpt-badge" id="rpt-b4">数据表 · 自动取值</span></div>
        <div class="rpt-cb" id="rpt-data"></div>
      </div>

      <div class="rpt-card wide">
        <div class="rpt-ch"><span class="rpt-no">5</span><b data-i18n="rpt.s5">结论</b><span class="rpt-badge" id="rpt-b5">自动</span></div>
        <div class="rpt-cb" id="rpt-concl"></div>
      </div>

      <div class="rpt-card wide">
        <div class="rpt-ch"><span class="rpt-no">6</span><b data-i18n="rpt.s6">反思</b><span class="rpt-badge todo" id="rpt-b6">待填写</span></div>
        <div class="rpt-cb">
          <div class="rpt-chips" id="rpt-reflChips"></div>
          <textarea id="rpt-reflect" rows="3" data-i18n-ph="rpt.ph.reflect" placeholder="这次探究哪里做得好？哪里还能改进？数据有没有异常？"></textarea>
          <div class="rpt-eval">
            <div class="rpt-evrow"><span data-i18n="rpt.self">自评</span><span class="rpt-stars" id="rpt-selfStars" role="radiogroup" aria-label="自评星级"></span><b id="rpt-selfTxt">未评</b></div>
            <div class="rpt-evrow"><span data-i18n="rpt.peer">互评</span><input id="rpt-peerName" type="text" maxlength="8" placeholder="同伴姓名"><span class="rpt-stars" id="rpt-peerStars" role="radiogroup" aria-label="互评星级"></span><b id="rpt-peerTxt">未评</b></div>
          </div>
        </div>
      </div>
    </div>

    <div class="rpt-act">
      <button id="rpt-export" class="play-btn" data-i18n="rpt.export">⬇ 一键导出报告（HTML）</button>
      <button id="rpt-print" class="sec" data-i18n="rpt.print">🖨 打印 / 存 PDF</button>
      <button id="rpt-copy" class="sec" data-i18n="rpt.copy">复制报告文本</button>
      <button id="rpt-csv" class="sec" data-i18n="rpt.csv">导出数据 CSV</button>
      <span class="rpt-tip" id="rpt-tip"></span>
    </div>
  </section>
"""

# ============================================================ I18N 追加
I18N_ADD = r"""/* ---- V5.1.1 实验报告 ---- */
'tab.report':     {zh:'12 · 实验报告 📝', zht:'12 · 實驗報告 📝', en:'12 · Lab Report 📝'},
'rpt.title':      {zh:'📝 实验报告 · 科学探究六要素', zht:'📝 實驗報告 · 科學探究六要素', en:'📝 Lab Report · Six Elements'},
'rpt.sub':        {zh:'按「问题 → 猜想 → 方案 → 数据 → 结论 → 反思」组织。问题、方案、数据表、结论由各实验画布的真实参数自动取值；猜想与反思由你填写，写完即可一键导出。', zht:'按「問題 → 猜想 → 方案 → 數據 → 結論 → 反思」組織。問題、方案、數據表、結論由各實驗畫布的真實參數自動取值；猜想與反思由你填寫，寫完即可一鍵匯出。', en:'Structured as Question → Hypothesis → Method → Data → Conclusion → Reflection. Question, Method, Data table and Conclusion are filled from the real canvas parameters; you write the Hypothesis and Reflection, then export in one click.'},
'rpt.exp':        {zh:'实验', zht:'實驗', en:'Experiment'},
'rpt.who':        {zh:'姓名', zht:'姓名', en:'Name'},
'rpt.date':       {zh:'日期', zht:'日期', en:'Date'},
'rpt.refresh':    {zh:'↻ 重新取值', zht:'↻ 重新取值', en:'↻ Refresh'},
'rpt.s1':         {zh:'问题', zht:'問題', en:'Question'},
'rpt.s2':         {zh:'猜想', zht:'猜想', en:'Hypothesis'},
'rpt.s3':         {zh:'方案', zht:'方案', en:'Method'},
'rpt.s4':         {zh:'数据', zht:'數據', en:'Data'},
'rpt.s5':         {zh:'结论', zht:'結論', en:'Conclusion'},
'rpt.s6':         {zh:'反思', zht:'反思', en:'Reflection'},
'rpt.self':       {zh:'自评', zht:'自評', en:'Self'},
'rpt.peer':       {zh:'互评', zht:'互評', en:'Peer'},
'rpt.export':     {zh:'⬇ 一键导出报告（HTML）', zht:'⬇ 一鍵匯出報告（HTML）', en:'⬇ Export report (HTML)'},
'rpt.print':      {zh:'🖨 打印 / 存 PDF', zht:'🖨 列印 / 存 PDF', en:'🖨 Print / PDF'},
'rpt.copy':       {zh:'复制报告文本', zht:'複製報告文字', en:'Copy as text'},
'rpt.csv':        {zh:'导出数据 CSV', zht:'匯出數據 CSV', en:'Export data CSV'},
'rpt.ph.hypo':    {zh:'写下你的猜想（可点上方预设句一键填入）', zht:'寫下你的猜想（可點上方預設句一鍵填入）', en:'Write your hypothesis (tap a preset above to fill in)'},
'rpt.ph.reflect': {zh:'这次探究哪里做得好？哪里还能改进？数据有没有异常？', zht:'這次探究哪裡做得好？哪裡還能改進？數據有沒有異常？', en:'What went well? What could improve? Any odd data?'},
'rpt.apparatus':  {zh:'实验器材', zht:'實驗器材', en:'Apparatus'},
'rpt.vars':       {zh:'变量控制', zht:'變數控制', en:'Variables'},
'rpt.iv':         {zh:'自变量', zht:'自變數', en:'Independent'},
'rpt.dv':         {zh:'因变量', zht:'因變數', en:'Dependent'},
'rpt.cv':         {zh:'控制变量', zht:'控制變數', en:'Controlled'},
'rpt.steps':      {zh:'实验步骤', zht:'實驗步驟', en:'Procedure'},
'rpt.livenow':    {zh:'当前画布参数', zht:'當前畫布參數', en:'Current canvas values'},
'rpt.gosnapshot': {zh:'＋ 记录当前画布参数', zht:'＋ 記錄當前畫布參數', en:'＋ Record current values'},
'rpt.empty':      {zh:'这张数据表还没有内容：切到「{0}」实验，拖动滑块或直接在画布上拖动，停止操作 1 秒后会自动落表；也可以点下面的按钮，先把当前画布参数记下来。', zht:'這張數據表還沒有內容：切到「{0}」實驗，拖動滑桿或直接在畫布上拖動，停止操作 1 秒後會自動落表；也可以點下面的按鈕，先把當前畫布參數記下來。', en:'No rows yet: open the “{0}” experiment, drag a slider or the canvas — a row lands 1s after you stop. Or use the button below to record the current values now.'},
'rpt.noconcl':    {zh:'还没有数据，暂时无法归纳结论。上面「数据表」里有了记录后，结论会自动生成。', zht:'還沒有數據，暫時無法歸納結論。上面「數據表」裡有了記錄後，結論會自動生成。', en:'No data yet, so no conclusion can be drawn. It will be generated once the data table has rows.'},
'rpt.done':       {zh:'已完成', zht:'已完成', en:'Done'},
'rpt.todo':       {zh:'待填写', zht:'待填寫', en:'To fill'},
'rpt.auto':       {zh:'自动', zht:'自動', en:'Auto'},
'rpt.autoData':   {zh:'数据表 · 自动取值', zht:'數據表 · 自動取值', en:'Data table · auto'},
'rpt.unrated':    {zh:'未评', zht:'未評', en:'Not rated'},
'rpt.progress':   {zh:'六要素完成度 {0} / 6', zht:'六要素完成度 {0} / 6', en:'Completed {0} / 6'},
'rpt.chipReflect':{zh:'数据完整、结论可靠', zht:'數據完整、結論可靠', en:'Solid data, reliable conclusion'},
'rpt.chipReflect2':{zh:'操作有误差，读数要更准', zht:'操作有誤差，讀數要更準', en:'Some error — read more carefully'},
'rpt.chipReflect3':{zh:'下次多测几组再下结论', zht:'下次多測幾組再下結論', en:'Take more trials next time'},
'rpt.tip.needData':{zh:'还没有可导出的数据，先在上面的数据表里记一组。', zht:'還沒有可匯出的數據，先在上面的數據表裡記一組。', en:'No data to export yet.'},
'rpt.tip.snapped':{zh:'已把当前画布参数记入数据表。', zht:'已把當前畫布參數記入數據表。', en:'Recorded current canvas values.'},
'rpt.tip.copied': {zh:'报告文本已复制。', zht:'報告文字已複製。', en:'Report copied.'},
'rpt.tip.copyfail':{zh:'复制失败，请手动选中文本复制。', zht:'複製失敗，請手動選中文字複製。', en:'Copy failed.'},
'rpt.tip.exported':{zh:'已导出报告：{0}', zht:'已匯出報告：{0}', en:'Exported: {0}'},
'rpt.tip.print':  {zh:'已在新标签打开报告，按 Ctrl+P（Mac 用 ⌘P）即可打印或存为 PDF。', zht:'已在新標籤開啟報告，按 Ctrl+P（Mac 用 ⌘P）即可列印或存為 PDF。', en:'Report opened in a new tab — press Ctrl+P (⌘P) to print.'},
'rpt.tip.printFail':{zh:'浏览器拦截了新窗口，已改为下载报告文件，打开后按 Ctrl+P 打印。', zht:'瀏覽器攔截了新視窗，已改為下載報告檔案，開啟後按 Ctrl+P 列印。', en:'Popup blocked — report downloaded instead; open it and press Ctrl+P.'},
'rpt.tip.csv':    {zh:'已导出数据 CSV。', zht:'已匯出數據 CSV。', en:'CSV exported.'},
'rpt.tip.refresh':{zh:'已按最新画布参数刷新。', zht:'已按最新畫布參數刷新。', en:'Refreshed from the canvas.'},
/* I18N-PART2 */
"""

# ============================================================ 报告 JS 模块
REPORT_JS = r"""
/* ==========================================================================
   V5.1.1 · 实验报告自动生成（科学探究六要素）
   --------------------------------------------------------------------------
   目标：把 V5.1.0 的「数据记录」补成完整的科学探究闭环，一键产出结构化报告。
   六要素：问题 → 猜想 → 方案 → 数据 → 结论 → 反思
     · 问题 / 方案 / 数据 / 结论 —— 自动生成；数据取自各实验【画布的真实参数】
       来源 1：V5.1.0 通用记录器 REC 已落表行（每条都是画布真实读数）
       来源 2：REC.snapshot() 取当前画布实时读数，并可一键补记入表
     · 猜想 / 反思 —— 学生填写，附预设句一键填入；另含 自评 / 互评 五星
   导出：HTML（自包含 / A4 打印友好 / 内嵌画布截图）/ 纯文本 / CSV / 打印存 PDF
   零依赖、零网络、零 API Key —— 断网也能生成完整报告。
   ========================================================================== */
var REPORT = (function(){
  /* tab 名 → 数据表 key（历史命名不一致：refl↔reflect、disp↔disperse、lfx↔lensfx…） */
  var TAB2KEY = { reflect:'refl', mirror:'mirr', lens:'lens', refract:'refr', line:'line',
                  disperse:'disp', lensfx:'lfx', eye:'eye', instr:'instr', combo:'combo' };
  var ORDER = ['reflect','mirror','lens','refract','line','disperse','lensfx','eye','instr','combo'];

  /* 版本号：第 1 段脚本里的 BUILD 作用域在 IIFE 内部，跨块引用会抛 ReferenceError，
     这里自带一份，并优先从右下角版本角标读取，保证与主版本始终一致。 */
  var RPT_BUILD = (function(){
    try{
      var el = document.querySelector('.ver-badge');
      var t = el ? String(el.textContent || '').trim() : '';
      if(t) return t;
    }catch(e){}
    return 'v5.1.1';
  })();

  /* ---------- 小工具（函数声明会提升，可被下面的 META 引用） ---------- */
  function E(s){ return (typeof escHtml === 'function') ? escHtml(s) : String(s == null ? '' : s); }
  function TT(k){ try{ return (typeof T === 'function') ? T(k) : k; }catch(e){ return k; } }
  function FMT(k){
    var a = Array.prototype.slice.call(arguments, 1);
    var s = TT(k);
    for(var i = 0; i < a.length; i++) s = s.split('{' + i + '}').join(String(a[i]));
    return s;
  }
  function val(id){ var el = $(id); return el ? String(el.value || '').trim() : ''; }
  function pair(rows, ai, bi){
    var n = 0, cnt = 0, maxd = 0, vals = [];
    rows.forEach(function(r){
      var a = parseFloat(r[ai]), b = parseFloat(r[bi]);
      if(!isFinite(a) || !isFinite(b)) return;
      n++;
      var d = Math.abs(a - b);
      if(d > maxd) maxd = d;
      if(d <= 0.06) cnt++;
      vals.push([a, b]);
    });
    return { n:n, cnt:cnt, maxd:maxd, vals:vals };
  }
  function rangeOf(rows, ai, unit){
    var lo = null, hi = null;
    rows.forEach(function(r){
      var v = parseFloat(r[ai]);
      if(!isFinite(v)) return;
      if(lo === null || v < lo) lo = v;
      if(hi === null || v > hi) hi = v;
    });
    if(lo === null) return '';
    return (lo === hi) ? (lo + unit) : (lo + unit + ' ~ ' + hi + unit);
  }
  function todayStr(){
    var d = new Date(), p = function(n){ return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }

  /* ---------- 各实验六要素元数据 ----------
     约定：question / apparatus / guess / vars / steps 为纯文本（插入时统一转义）；
           claim / evid / sup 为受控 HTML 片段（插入时原样使用，比较号写 &lt; &gt;） */
  var META = {
    refl: {
      name:'光的反射', canvas:'cv-refl',
      question:'光在平面镜上反射时，反射角 r 与入射角 i 之间有什么关系？反射光线与入射光线相对法线是怎样分布的？',
      apparatus:'激光笔（红光）、平面镜、画有法线的白纸、量角器、直尺',
      guess:['反射角等于入射角（r = i）','反射角大于入射角（r > i）','反射角小于入射角（r < i）'],
      vars:{ iv:'入射角 i（改变入射光线的方向）', dv:'反射角 r', cv:'平面镜的位置与角度、入射点位置、光的颜色、介质（空气）' },
      steps:['把平面镜平放在白纸上，沿镜面画一条直线，并在入射点 O 处画出垂直于镜面的法线。','用激光笔沿某个角度射向入射点 O，记下入射角 i。','观察反射光线的方向，读出反射光线与法线的夹角 r。','改变入射角（如 30°、45°、60°），重复 3~5 次并逐组记录。','比较每一组的 i 与 r，判断二者是否始终相等。'],
      concl:function(rows){
        var s = pair(rows, 0, 1); if(!s.n) return null;
        var ok = s.cnt === s.n;
        return { claim:'光在平面镜上发生反射时，<b>反射角等于入射角</b>（r = i）；反射光线与入射光线总是<b>分居法线两侧</b>。',
                 evid:'本次共记录 ' + s.n + ' 组数据（入射角 i = ' + rangeOf(rows, 0, '°') + '），其中 ' + s.cnt + ' 组满足 r = i，最大偏差仅 ' + s.maxd.toFixed(1) + '°。',
                 sup: ok ? '数据支持「反射角等于入射角」，且与入射角大小无关（0°~85° 均成立）。'
                         : '有数据与 r = i 不符，请检查读数是否<b>以法线为基准</b>（不是与镜面的夹角）。' };
      }
    },
    mirr: {
      name:'平面镜成像', canvas:'cv-mirr',
      question:'物体在平面镜中成的像，与物体的大小、到镜面的距离有什么关系？像是实像还是虚像？',
      apparatus:'玻璃板（或平面镜）、两支相同的蜡烛（或两个相同的棋子）、白纸、刻度尺、支架',
      guess:['像与物到镜面的距离相等（v = u）','像比物体小','像比物体大'],
      vars:{ iv:'物体到镜面的距离 u', dv:'像到镜面的距离 v、像的大小与正倒', cv:'玻璃板的位置与垂直度、物体本身的大小与形状、观察位置' },
      steps:['把玻璃板竖直架在白纸上，沿玻璃板画一条线作为镜面位置。','把物体放在镜前某处，从镜前观察像的位置。','用另一支等大的蜡烛（棋子）在镜后移动，直到与像完全重合，记下像的位置。','量出物距 u 和像距 v，并比较像与物的大小、正倒。','改变物距 u，重复 3~5 次并逐组记录。'],
      concl:function(rows){
        var s = pair(rows, 0, 1); if(!s.n) return null;
        return { claim:'平面镜成的像是<b>正立、等大的虚像</b>：像与物到镜面的距离相等（v = u），像与物关于镜面对称。',
                 evid:'本次共记录 ' + s.n + ' 组数据，像距 v 与物距 u 的最大差值为 ' + s.maxd.toFixed(1) + ' cm。',
                 sup: (s.maxd <= 0.6) ? '数据支持「像距等于物距、像与物等大等距」。'
                                      : '像距与物距偏差偏大，请确认两段距离都是<b>从镜面量起</b>的。' };
      }
    },
    lens: {
      name:'凸透镜成像', canvas:'cv-lens',
      question:'改变物距 u，凸透镜所成像的大小、正倒、虚实会怎样变化？规律与焦距 f 有什么关系？',
      apparatus:'凸透镜、光具座（或刻度尺）、蜡烛（发光体）、光屏',
      guess:['物距越小，像越大','物距大于二倍焦距时成缩小的像','物距小于焦距时成正立的像'],
      vars:{ iv:'物距 u', dv:'像距 v、像的大小 / 正倒 / 虚实', cv:'凸透镜的焦距 f、烛焰高度、光屏位置、三者共轴' },
      steps:['把凸透镜固定在光具座中间，读出它的焦距 f。','把发光体放在 u > 2f 处，移动光屏直到出现清晰的像，记录 u、v 和像的性质。','依次把物距调整为 u = 2f、f < u < 2f、u < f，分别记录成像情况。','比较各组中 u 与 f 的大小关系 → 像的性质，归纳规律。'],
      concl:function(rows){
        if(!rows.length) return null;
        var f = null, n = 0, cases = [];
        rows.forEach(function(r){
          var u = parseFloat(r[0]), v = parseFloat(r[2]);
          if(f === null && isFinite(v)) f = v;
          if(isFinite(u)) n++;
        });
        if(isFinite(f)){
          rows.forEach(function(r){
            var u = parseFloat(r[0]), nat = String(r[3] || '').trim();
            if(!isFinite(u) || !nat) return;
            var tag = (u > 2*f) ? 'u &gt; 2f' : (Math.abs(u-2*f) < 0.8 ? 'u ≈ 2f'
                    : (u > f) ? 'f &lt; u &lt; 2f' : (Math.abs(u-f) < 0.8 ? 'u ≈ f' : 'u &lt; f'));
            var one = tag + ' → ' + E(nat);
            if(cases.indexOf(one) < 0) cases.push(one);
          });
        }
        return { claim:'凸透镜成像规律：<b>u &gt; 2f</b> 成倒立、缩小的实像（f &lt; v &lt; 2f）；<b>u = 2f</b> 成倒立、等大的实像；<b>f &lt; u &lt; 2f</b> 成倒立、放大的实像（v &gt; 2f）；<b>u &lt; f</b> 成正立、放大的虚像（放大镜原理）。',
                 evid:'本次共记录 ' + n + ' 组' + (isFinite(f) ? '（f ≈ ' + f + ' cm）' : '') + '。' + (cases.length ? '实测组合：' + cases.slice(0, 6).join('；') + '。' : ''),
                 sup:'口诀：<b>一倍焦距分虚实，二倍焦距分大小</b>；物距减小，像距增大、像变大。' };
      }
    },
    refr: {
      name:'光的折射', canvas:'cv-refr',
      question:'光从空气斜射入水或玻璃中时，折射角 r 与入射角 i 谁大谁小？折射光线偏向哪边？',
      apparatus:'激光笔、玻璃砖（或水槽）、量角器、白纸',
      guess:['折射角小于入射角（r < i）','折射角大于入射角（r > i）','折射角等于入射角'],
      vars:{ iv:'入射角 i', dv:'折射角 r、折射光线的偏折方向', cv:'介质的种类与界面位置、入射点、光的颜色、光从空气射入' },
      steps:['把玻璃砖放在白纸上并描出界面，画出入射点处的法线。','让激光沿某个角度射向界面，记下入射角 i。','观察折射光线的方向，读出折射光线与法线的夹角 r。','改变入射角，重复 3~5 次并逐组记录。','比较每一组的 i 与 r，判断折射光线是偏向还是偏离法线。'],
      concl:function(rows){
        var s = pair(rows, 1, 2); if(!s.n) return null;
        var less = 0;
        s.vals.forEach(function(p){ if(p[1] < p[0] - 1e-9) less++; });
        return { claim:'光从空气斜射入水（或玻璃）中时，折射光线<b>偏向法线</b>，折射角小于入射角（r &lt; i）；入射角增大，折射角也增大。',
                 evid:'本次共记录 ' + s.n + ' 组数据（入射角 i = ' + rangeOf(rows, 1, '°') + '），其中 ' + less + ' 组满足 r &lt; i，最大角差 ' + s.maxd.toFixed(1) + '°。',
                 sup: (less === s.n) ? '数据支持「空气 → 水（玻璃）时折射角小于入射角」。'
                                     : '出现 r ≥ i 的读数，注意介质方向（空气→水）以及角度是否以法线为基准。' };
      }
    },
    line: {
      name:'光的直线传播与小孔成像', canvas:'cv-line',
      question:'光在均匀介质中是怎样传播的？影子和小孔成像说明了什么？',
      apparatus:'激光笔、手电筒、不透明物体、带小孔的挡板、光屏、直尺',
      guess:['光沿直线传播','小孔成的是倒立的像','影子的形状与物体形状相同'],
      vars:{ iv:'物体（光源）到小孔 / 挡板的距离 u', dv:'影子或像的位置、大小与正倒', cv:'介质均匀、光的颜色、小孔大小、光屏位置' },
      steps:['用激光笔照射不透明物体，观察影子的位置和形状。','改变物体到光源的距离，观察影子大小的变化。','在挡板上开一个小孔，让光穿过小孔照到光屏上，观察光斑形状。','前后移动光屏或挡板，观察像的大小与正倒变化并逐组记录。'],
      concl:function(rows){
        if(!rows.length) return null;
        var ex = rows.slice(0, 4).map(function(r){ return E(r[0] || '') + (r[4] ? '（' + E(r[4]) + '）' : ''); }).join('；');
        return { claim:'光在同种均匀介质中<b>沿直线传播</b>：影子随物体与光源位置的变化而改变；<b>小孔成像</b>成的是<b>倒立的实像</b>，像的大小由物到小孔、小孔到光屏的距离共同决定。',
                 evid:'本次共记录 ' + rows.length + ' 组：' + ex + '。',
                 sup:'影随物动、小孔成倒像，都是「光沿直线传播」的直接证据。' };
      }
    },
    disp: {
      name:'色散与物体颜色', canvas:'cv-disp',
      question:'白光是单一颜色的光吗？白光通过三棱镜后会发生什么？色光的三原色是哪三种？',
      apparatus:'三棱镜、白屏、白光光源、红绿蓝三色滤光片',
      guess:['白光是复色光，可以分解成多种色光','红光偏折最大','色光三原色是红、绿、蓝'],
      vars:{ iv:'通过棱镜或相互叠加的色光（红 / 绿 / 蓝）', dv:'白屏上光斑的颜色与顺序、混合后的颜色', cv:'光源的亮度与方向、棱镜的位置、白屏距离、环境光' },
      steps:['让一束白光斜射到三棱镜的一个面上，在白屏上观察光斑的颜色排列。','记录从上到下的色光顺序，观察哪种色光偏折最明显。','分别用红、绿、蓝三种色光两两叠加，观察混合后的颜色。','把红、绿、蓝三种色光同时叠加，观察是否得到白光。'],
      concl:function(rows){
        if(!rows.length) return null;
        var ex = rows.slice(0, 3).map(function(r){ return E(r[1] || '') + ' → ' + E(r[2] || ''); }).join('；');
        return { claim:'白光是<b>复色光</b>，经三棱镜折射后分解为红、橙、黄、绿、蓝、靛、紫（<b>光的色散</b>）；<b>色光三原色</b>是红、绿、蓝，三者等比例混合可得白光。',
                 evid:'本次共记录 ' + rows.length + ' 组：' + ex + '。',
                 sup:'不同色光在同种介质中偏折程度不同：紫光偏折最大，红光最小。' };
      }
    },
    lfx: {
      name:'透镜对光的作用', canvas:'cv-lfx',
      question:'凸透镜和凹透镜对光分别有什么作用？平行于主光轴的光通过透镜后会怎样？',
      apparatus:'凸透镜、凹透镜、平行光源（激光笔组）、白纸、直尺',
      guess:['凸透镜对光有会聚作用','凹透镜对光有发散作用','平行光通过凸透镜后会聚于焦点'],
      vars:{ iv:'透镜的类型（凸 / 凹）、透镜的焦距 f', dv:'折射光线的会聚 / 发散情况、焦点位置', cv:'透镜正对平行光、光源的平行度、光屏位置、介质' },
      steps:['让一束平行于主光轴的光射向凸透镜，观察折射光线是否交于一点。','量出焦点到光心的距离，即焦距 f。','换用焦距不同的凸透镜，比较会聚能力的强弱。','换成凹透镜重复实验，观察折射光线的走向。'],
      concl:function(rows){
        if(!rows.length) return null;
        var ex = rows.slice(0, 4).map(function(r){ return E(r[0] || '') + (r[3] ? '（' + E(r[3]) + '）' : ''); }).join('；');
        return { claim:'<b>凸透镜对光有会聚作用</b>：平行于主光轴的光经凸透镜折射后会聚于焦点；<b>凹透镜对光有发散作用</b>：平行于主光轴的光经凹透镜折射后发散，其反向延长线过虚焦点。',
                 evid:'本次共记录 ' + rows.length + ' 组：' + ex + '。',
                 sup:'焦距 f 越短，透镜的会聚（或发散）能力越强。' };
      }
    },
    eye: {
      name:'近视与远视的矫正', canvas:'cv-eye',
      question:'近视眼和远视眼分别把像成在视网膜的哪一侧？各需要用什么透镜矫正？',
      apparatus:'眼球模型（凸透镜 + 光屏）、凹透镜、凸透镜、光具座',
      guess:['近视眼要用凹透镜矫正','远视眼要用凸透镜矫正','近视眼的像成在视网膜前方'],
      vars:{ iv:'眼的类型（正常 / 近视 / 远视）、矫正镜片的度数', dv:'像在视网膜上的位置、看到的清晰程度', cv:'凸透镜（晶状体）的焦距、视网膜（光屏）位置、物距' },
      steps:['用凸透镜和光屏模拟正常眼，调整位置使像正好落在光屏上。','换成厚一些的凸透镜（近视眼模型），观察像落在光屏前方还是后方。','在眼前加一块凹透镜，观察像能否重新回到光屏上。','改用较薄的凸透镜（远视眼模型），再加凸透镜观察矫正效果并逐组记录。'],
      concl:function(rows){
        if(!rows.length) return null;
        var ex = rows.slice(0, 4).map(function(r){ return E(r[0] || '') + ' → ' + E(r[2] || '') + (r[4] ? ' → ' + E(r[4]) : ''); }).join('；');
        return { claim:'<b>近视眼</b>的像成在视网膜<b>前方</b>，需佩戴<b>凹透镜</b>矫正；<b>远视眼</b>的像成在视网膜<b>后方</b>，需佩戴<b>凸透镜</b>矫正；正常眼的像正好落在视网膜上。',
                 evid:'本次共记录 ' + rows.length + ' 组：' + ex + '。',
                 sup:'矫正的本质：先用透镜让光适当发散或会聚，使像重新落在视网膜上。' };
      }
    },
    instr: {
      name:'光学仪器（照相机 / 投影仪 / 放大镜）', canvas:'cv-instr',
      question:'照相机、投影仪、放大镜的物距各满足什么条件？成的像分别有什么特点？',
      apparatus:'凸透镜、蜡烛（发光体）、光屏、光具座、刻度尺',
      guess:['照相机成像时物距大于二倍焦距','投影仪成放大的实像','放大镜成放大的虚像'],
      vars:{ iv:'物距 u（相对焦距 f 的大小关系）', dv:'像距 v、放大率 m = |v/u|、像的性质', cv:'凸透镜的焦距 f、光源高度、光屏位置、三者共轴' },
      steps:['把发光体放在 u > 2f 处，移动光屏得到清晰的像，记录 u、v 和像的性质（照相机）。','把物距调到 f < u < 2f，记录 u、v 和像的性质（投影仪）。','把物体移到 u < f 以内，从透镜另一侧观察像的性质（放大镜）。','计算各组放大率 m = |v/u|，归纳物距与像的性质的对应关系。'],
      concl:function(rows){
        if(!rows.length) return null;
        var ex = rows.slice(0, 4).map(function(r){ return E(r[0] || '') + '（u=' + E(r[1] || '') + '，v=' + E(r[2] || '') + '，m=' + E(r[3] || '') + '）'; }).join('；');
        return { claim:'光学仪器的成像规律：<b>照相机</b> u &gt; 2f，成倒立、缩小的实像；<b>投影仪（幻灯机）</b> f &lt; u &lt; 2f，成倒立、放大的实像；<b>放大镜</b> u &lt; f，成正立、放大的虚像。',
                 evid:'本次共记录 ' + rows.length + ' 组：' + ex + '。',
                 sup:'放大率 m = |v/u|：物距越小（但仍大于 f），像越大、像距越大。' };
      }
    },
    combo: {
      name:'反射与折射综合', canvas:'cv-combo',
      question:'光斜射到两种介质的界面上时，会同时发生哪些现象？反射角和折射角与入射角各有什么关系？',
      apparatus:'激光笔、水槽（或玻璃砖）、量角器、白纸',
      guess:['反射和折射同时发生','反射角等于入射角','从空气射入水中时折射角小于入射角'],
      vars:{ iv:'入射角 i、光射向的界面方向（空气→水 / 玻璃→空气）', dv:'反射角 r、折射角 r′、光斑的亮度分配', cv:'介质的种类与界面位置、入射点、光的颜色' },
      steps:['把水槽放在白纸上，画出入射点处的法线和界面。','让激光沿某个角度射向界面，同时观察反射光线和折射光线。','分别记下反射角 r 和折射角 r′，与入射角 i 比较。','改变入射角，重复 3~5 次；再把光线改为从玻璃射向空气，观察有什么不同。'],
      concl:function(rows){
        if(!rows.length) return null;
        /* 表头顺序为 mode / i / r（反射角） / i'（折射角） / 现象，
           这里只核算「反射角 r 与入射角 i」，与结论中的表述严格对应 */
        var s = pair(rows, 1, 2);
        return { claim:'光斜射到两种介质的界面上时，会<b>同时发生反射和折射</b>：反射角等于入射角；光从空气斜射入水或玻璃时折射角小于入射角（偏向法线），从水或玻璃斜射入空气时折射角大于入射角。',
                 evid:'本次共记录 ' + rows.length + ' 组' + (s.n ? '，反射角 r 与入射角 i 的最大偏差为 ' + s.maxd.toFixed(1) + '°' : '') + '。',
                 sup:'入射角增大时，反射光增强、折射光减弱；当入射角大于临界角时会发生<b>全反射</b>。' };
      }
    }
  };

  /* ---------- 数据表读取（真实落表行，源自画布参数） ---------- */
  function headText(th){
    var k = th.getAttribute && th.getAttribute('data-i18n');
    if(k) return TT(k);
    return String(th.textContent || '').trim();
  }
  function readTable(key){
    var tb = document.getElementById(key + '-dataBody');
    if(!tb) return { head:[], rows:[], vals:[] };
    var tbl = tb.closest ? tb.closest('table') : null;
    var head = tbl ? Array.prototype.map.call(tbl.querySelectorAll('thead th'), headText) : [];
    var rows = Array.prototype.map.call(tb.querySelectorAll('tr'), function(tr){
      return Array.prototype.map.call(tr.children, function(td){ return String(td.textContent || '').trim(); });
    });
    /* DOM 行首列是渲染时补的序号「#」，而各实验 getRow() 返回的是【不含序号】的值。
       结论推导必须用 vals，否则所有列索引会整体错位一位
       （真实踩坑：折射结论 r[1] 取到介质名导致永远无法生成，反射/平面镜偏差值虚高） */
    var hasIdx = head.length > 0 && String(head[0]).trim() === '#';
    var vals = hasIdx ? rows.map(function(r){ return r.slice(1); }) : rows;
    return { head:head, rows:rows, vals:vals };
  }
  function headNoIdx(head){
    var h = head.slice();
    if(h.length && String(h[0]).trim() === '#') h.shift();
    return h;
  }
  function liveRow(key){
    try{ return (window.REC && REC.snapshot) ? REC.snapshot(key) : null; }catch(e){ return null; }
  }

  /* ---------- 学生填写部分持久化（刷新不丢） ---------- */
  var LS = K + '_report';
  var lastExp = 'reflect';
  var store = (function(){
    try{ return JSON.parse(localStorage.getItem(LS) || '{}') || {}; }catch(e){ return {}; }
  })();
  var selfScore = parseInt(store.self, 10) || 0;
  var peerScore = parseInt(store.peer, 10) || 0;
  function save(){
    try{
      store.hypo = val('rpt-hypo');
      store.reflect = val('rpt-reflect');
      store.name = val('rpt-name');
      store.peerName = val('rpt-peerName');
      store.self = selfScore;
      store.peer = peerScore;
      localStorage.setItem(LS, JSON.stringify(store));
    }catch(e){}
  }

  /* 报告默认「跟随最近打开的实验」；一旦学生在这个下拉里手动选过，就尊重他的选择 */
  var pickedExp = false;
  function currentKey(){
    var sel = $('rpt-exp');
    if(!pickedExp) return META[lastExp] ? lastExp : 'refl';
    var v = sel ? sel.value : '';
    return META[v] ? v : (META[lastExp] ? lastExp : 'refl');
  }

  /* ---------- 渲染 ---------- */
  function setBadge(id, text, ok, warn){
    var el = $(id);
    if(!el) return;
    el.textContent = text;
    el.className = 'rpt-badge' + (ok ? '' : ' todo') + (warn ? ' warn' : '');
  }
  function tip(msg){
    var el = $('rpt-tip');
    if(!el) return;
    el.textContent = msg;
    clearTimeout(tip._t);
    tip._t = setTimeout(function(){ el.textContent = ''; }, 4000);
  }

  function renderQuestion(m){
    var el = $('rpt-q');
    if(!el) return;
    el.innerHTML = '<p class="rpt-q">' + E(m.question) + '</p>' +
      '<p style="margin-top:9px;font-size:12.5px;color:var(--muted)">所属实验：' + E(m.name) +
      '　·　建议器材：' + E(m.apparatus) + '</p>';
    setBadge('rpt-b1', TT('rpt.auto'), true);
  }

  function renderPlan(m){
    var el = $('rpt-plan');
    if(!el) return;
    var li = m.steps.map(function(s){ return '<li>' + E(s) + '</li>'; }).join('');
    el.innerHTML =
      '<div class="rpt-row"><span class="rpt-k">' + TT('rpt.apparatus') + '</span><span class="rpt-v">' + E(m.apparatus) + '</span></div>' +
      '<div class="rpt-row"><span class="rpt-k">' + TT('rpt.vars') + '</span><span class="rpt-v">' +
        '<span class="vr"><b>' + TT('rpt.iv') + '</b>：' + E(m.vars.iv) + '</span>' +
        '<span class="vr"><b>' + TT('rpt.dv') + '</b>：' + E(m.vars.dv) + '</span>' +
        '<span class="vr"><b>' + TT('rpt.cv') + '</b>：' + E(m.vars.cv) + '</span>' +
      '</span></div>' +
      '<div class="rpt-row"><span class="rpt-k">' + TT('rpt.steps') + '</span><span class="rpt-v"><ol>' + li + '</ol></span></div>';
    setBadge('rpt-b3', TT('rpt.auto'), true);
  }

  function renderData(key, m){
    var t = readTable(key);
    var live = liveRow(key);
    var nh = headNoIdx(t.head);
    var box = $('rpt-data');
    if(!box) return t;
    var btnId = 'rpt-snap-' + key;

    if(!t.rows.length){
      box.innerHTML = '<div class="rpt-empty">' + E(FMT('rpt.empty', m.name)) + '</div>' +
        '<div style="margin-top:9px"><button id="' + btnId + '" class="sec">' + E(TT('rpt.gosnapshot')) + '</button></div>';
      setBadge('rpt-b4', TT('rpt.autoData'), false, true);
    } else {
      var h = t.head.map(function(x){ return '<th>' + E(x) + '</th>'; }).join('');
      var b = t.rows.map(function(r){
        return '<tr>' + r.map(function(c){ return '<td>' + E(c) + '</td>'; }).join('') + '</tr>';
      }).join('');
      var lv = '';
      if(live && live.length){
        lv = '<div class="rpt-live">' + E(TT('rpt.livenow')) + '：' + nh.map(function(n, i){
          return E(n) + ' <b>' + E(live[i] == null ? '—' : live[i]) + '</b>';
        }).join('　·　') + '</div>';
      }
      box.innerHTML = '<div class="rpt-databox"><table class="rpt-dt"><thead><tr>' + h +
        '</tr></thead><tbody>' + b + '</tbody></table></div>' + lv +
        '<div style="margin-top:9px"><button id="' + btnId + '" class="sec">' + E(TT('rpt.gosnapshot')) + '</button></div>';
      setBadge('rpt-b4', TT('rpt.autoData'), true);
    }
    var btn = $(btnId);
    if(btn){
      btn.addEventListener('click', function(){
        var ok = false;
        try{ ok = (window.REC && REC.commit) ? REC.commit(key, true) : false; }catch(e){ ok = false; }
        tip(TT(ok ? 'rpt.tip.snapped' : 'rpt.tip.needData'));
        render();
      });
    }
    return t;
  }

  function renderConcl(m, t){
    var c = null;
    try{ c = m.concl(t.vals) || null; }catch(e){ c = null; }
    var el = $('rpt-concl');
    if(!el) return c;
    if(!c){
      el.innerHTML = '<div class="rpt-empty">' + E(TT('rpt.noconcl')) + '</div>';
      setBadge('rpt-b5', TT('rpt.todo'), false, true);
      return null;
    }
    el.innerHTML = '<div class="rpt-concl">' +
      '<div class="claim">' + c.claim + '</div>' +
      '<div class="evid">📊 ' + c.evid + '</div>' +
      '<div class="sup">💡 ' + c.sup + '</div>' +
      '</div>';
    setBadge('rpt-b5', TT('rpt.auto'), true);
    return c;
  }

  function renderProgress(st){
    var marks = [ true, !!st.hypo, true, st.rows > 0, !!st.concl, (!!st.reflect && st.self > 0) ];
    var done = marks.filter(Boolean).length;
    var bar = $('rpt-bar');
    if(bar) bar.style.width = Math.round(done / 6 * 100) + '%';
    var txt = $('rpt-progTxt');
    if(txt) txt.textContent = FMT('rpt.progress', done);
    var dots = $('rpt-dots');
    if(dots) dots.innerHTML = marks.map(function(mk){ return '<i class="rpt-dot' + (mk ? ' on' : '') + '"></i>'; }).join('');
    var b2 = $('rpt-b2');
    if(b2){ b2.textContent = TT(st.hypo ? 'rpt.done' : 'rpt.todo'); b2.className = 'rpt-badge' + (st.hypo ? '' : ' todo'); }
    var b6 = $('rpt-b6');
    if(b6){
      var done6 = !!st.reflect && st.self > 0;
      b6.textContent = TT(done6 ? 'rpt.done' : 'rpt.todo');
      b6.className = 'rpt-badge' + (done6 ? '' : ' todo');
    }
  }

  var chipsKey = null;
  function renderChips(key, m){
    if(chipsKey === key) return;
    chipsKey = key;
    var g = $('rpt-guess');
    if(g) g.innerHTML = m.guess.map(function(x){ return '<span class="rpt-chip" data-t="guess">' + E(x) + '</span>'; }).join('');
    var r = $('rpt-reflChips');
    if(r) r.innerHTML = ['rpt.chipReflect', 'rpt.chipReflect2', 'rpt.chipReflect3'].map(function(k){
      return '<span class="rpt-chip" data-t="reflect">' + E(TT(k)) + '</span>';
    }).join('');
  }

  function refreshStars(){
    [[$('rpt-selfStars'), selfScore, 'self'], [$('rpt-peerStars'), peerScore, 'peer']].forEach(function(a){
      var el = a[0]; if(!el) return;
      el.querySelectorAll('.rpt-star').forEach(function(s){
        var on = parseInt(s.dataset.v, 10) <= a[1];
        s.classList.toggle('on', on);
        s.setAttribute('aria-checked', on ? 'true' : 'false');
      });
      var box = (a[2] === 'self') ? $('rpt-selfTxt') : $('rpt-peerTxt');
      if(box) box.textContent = a[1] > 0 ? (a[1] + ' / 5 星') : TT('rpt.unrated');
    });
  }

  function fillExpSelect(key){
    var sel = $('rpt-exp');
    if(!sel) return;
    var sig = String(typeof LANG === 'undefined' ? '' : LANG) + '|' + ORDER.length;
    if(sel.dataset.sig !== sig){
      sel.innerHTML = ORDER.map(function(tab){
        return '<option value="' + TAB2KEY[tab] + '">' + E(TT('tab.' + tab)) + '</option>';
      }).join('');
      sel.dataset.sig = sig;
    }
    if(META[key]) sel.value = key;
  }

  function collect(){
    var key = currentKey();
    var m = META[key];
    var t = readTable(key);
    var live = liveRow(key);
    var c = null;
    try{ c = m.concl(t.vals) || null; }catch(e){ c = null; }
    return {
      key:key, meta:m, data:t, head:headNoIdx(t.head), live:live, concl:c, rows:t.rows.length,
      hypo:val('rpt-hypo'), reflect:val('rpt-reflect'),
      name:val('rpt-name'), date:val('rpt-date'),
      self:selfScore, peer:peerScore, peerName:val('rpt-peerName')
    };
  }

  var started = false;
  function render(){
    try{
      if(!$('rpt-q')) return;
      if(!started) initOnce();
      var key = currentKey();
      var m = META[key];
      fillExpSelect(key);
      renderQuestion(m);
      renderPlan(m);
      var t = renderData(key, m);
      var c = renderConcl(m, t);
      renderChips(key, m);
      var st = collect();
      st.concl = c;
      renderProgress(st);
      refreshStars();
    }catch(e){
      try{ console.warn('[REPORT] 渲染失败：', e && e.message); }catch(_){}
    }
  }

  function buildStars(el, get, set, label){
    if(!el) return;
    var html = '';
    for(var i = 1; i <= 5; i++){
      html += '<span class="rpt-star" role="radio" tabindex="0" aria-checked="false" data-v="' + i + '" title="' + i + ' 星">★</span>';
    }
    el.innerHTML = html;
    var pick = function(v){ set(v); save(); render(); };
    el.querySelectorAll('.rpt-star').forEach(function(s){
      var v = parseInt(s.dataset.v, 10);
      s.addEventListener('click', function(){ pick(v); });
      s.addEventListener('keydown', function(ev){
        if(ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); pick(v); }
      });
    });
    refreshStars();
  }

  function download(name, text, mime){
    try{
      var blob = new Blob([text], { type:mime || 'text/plain;charset=utf-8' });
      var a = document.createElement('a');
      a.download = name; a.href = URL.createObjectURL(blob);
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(function(){ try{ URL.revokeObjectURL(a.href); }catch(e){} }, 8000);
      return true;
    }catch(e){ return false; }
  }
  function fallbackCopy(text){
    try{
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.top = '-9999px'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.focus(); ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    }catch(e){ return false; }
  }
  function copyText(text){
    return new Promise(function(resolve){
      try{
        if(navigator.clipboard && window.isSecureContext){
          navigator.clipboard.writeText(text).then(function(){ resolve(true); }, function(){ resolve(fallbackCopy(text)); });
          return;
        }
      }catch(e){}
      resolve(fallbackCopy(text));
    });
  }
  function stripTags(s){
    return String(s == null ? '' : s)
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]+>/g, '')
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  }

  function initOnce(){
    if(started) return;
    started = true;
    var sel = $('rpt-exp');
    if(sel){
      fillExpSelect(lastExp);
      sel.addEventListener('change', function(){ pickedExp = true; render(); });
    }
    var d = $('rpt-date');
    if(d && !d.value) d.value = todayStr();
    var n = $('rpt-name');       if(n && store.name) n.value = store.name;
    var h = $('rpt-hypo');       if(h && store.hypo) h.value = store.hypo;
    var rf = $('rpt-reflect');   if(rf && store.reflect) rf.value = store.reflect;
    var pn = $('rpt-peerName');  if(pn && store.peerName) pn.value = store.peerName;

    ['rpt-hypo', 'rpt-reflect', 'rpt-name', 'rpt-peerName'].forEach(function(id){
      var el = $(id);
      if(!el) return;
      var on = function(){ save(); render(); };
      el.addEventListener('input', on);
      el.addEventListener('change', on);
    });
    ['rpt-guess', 'rpt-reflChips'].forEach(function(id){
      var box = $(id);
      if(!box) return;
      box.addEventListener('click', function(ev){
        var c = (ev.target && ev.target.closest) ? ev.target.closest('.rpt-chip') : null;
        if(!c) return;
        var target = (c.dataset.t === 'guess') ? $('rpt-hypo') : $('rpt-reflect');
        if(!target) return;
        var cur = String(target.value || '').trim();
        var add = String(c.textContent || '').trim();
        target.value = cur ? (cur + '；' + add) : add;
        save(); render();
      });
    });
    var rb = $('rpt-refresh');
    if(rb) rb.addEventListener('click', function(){ render(); tip(TT('rpt.tip.refresh')); });

    buildStars($('rpt-selfStars'), function(){ return selfScore; }, function(v){ selfScore = v; }, 'self');
    buildStars($('rpt-peerStars'), function(){ return peerScore; }, function(v){ peerScore = v; }, 'peer');

    var ex = $('rpt-export'), pr = $('rpt-print'), cp = $('rpt-copy'), cv = $('rpt-csv');
    if(ex) ex.addEventListener('click', function(){
      var st = collect();
      if(!st.rows){ tip(TT('rpt.tip.needData')); return; }
      var fname = '实验报告_' + st.meta.name + '_' + (st.date || todayStr()) + '.html';
      if(download(fname, buildExportHtml(st), 'text/html;charset=utf-8')) tip(FMT('rpt.tip.exported', fname));
    });
    if(pr) pr.addEventListener('click', function(){
      var st = collect();
      if(!st.rows){ tip(TT('rpt.tip.needData')); return; }
      var html = buildExportHtml(st);
      var fname = '实验报告_' + st.meta.name + '_' + (st.date || todayStr()) + '.html';
      var w = null;
      try{
        var url = URL.createObjectURL(new Blob([html], { type:'text/html;charset=utf-8' }));
        w = window.open(url, '_blank');
      }catch(e){ w = null; }
      if(w) tip(TT('rpt.tip.print'));
      else { download(fname, html, 'text/html;charset=utf-8'); tip(TT('rpt.tip.printFail')); }
    });
    if(cp) cp.addEventListener('click', function(){
      var st = collect();
      copyText(buildText(st)).then(function(ok){ tip(TT(ok ? 'rpt.tip.copied' : 'rpt.tip.copyfail')); });
    });
    if(cv) cv.addEventListener('click', function(){
      var st = collect();
      if(!st.rows){ tip(TT('rpt.tip.needData')); return; }
      var rows = [['#'].concat(st.head)].concat(st.data.rows);
      var csv = '\ufeff' + rows.map(function(r){
        return r.map(function(c){ return '"' + String(c).replace(/"/g, '""') + '"'; }).join(',');
      }).join('\r\n');
      download('实验报告数据_' + st.meta.name + '_' + (st.date || todayStr()) + '.csv', csv, 'text/csv;charset=utf-8');
      tip(TT('rpt.tip.csv'));
    });
  }

  /* ---------- 纯文本报告 ---------- */
  function buildText(st){
    var L = [];
    L.push('【' + st.meta.name + ' · 实验报告】');
    L.push('姓名：' + (st.name || '＿＿＿＿') + '　　日期：' + (st.date || todayStr()));
    L.push('');
    L.push('一、问题');
    L.push(st.meta.question);
    L.push('');
    L.push('二、猜想');
    L.push(st.hypo || '（未填写）');
    L.push('');
    L.push('三、方案');
    L.push('实验器材：' + st.meta.apparatus);
    L.push('变量控制：自变量=' + st.meta.vars.iv + '；因变量=' + st.meta.vars.dv + '；控制变量=' + st.meta.vars.cv);
    st.meta.steps.forEach(function(s, i){ L.push('  ' + (i + 1) + '. ' + s); });
    L.push('');
    L.push('四、数据（数据表，共 ' + st.rows + ' 组，取自画布真实参数）');
    L.push(st.data.head.join('\t'));
    st.data.rows.forEach(function(r){ L.push(r.join('\t')); });
    if(st.live && st.live.length){
      L.push('当前画布参数：' + st.head.map(function(h, i){
        return h + '=' + (st.live[i] == null ? '—' : st.live[i]);
      }).join('，'));
    }
    L.push('');
    L.push('五、结论');
    L.push(st.concl ? stripTags(st.concl.claim) : '（数据不足，暂无法归纳）');
    if(st.concl){
      L.push('数据支撑：' + stripTags(st.concl.evid));
      L.push('说明：' + stripTags(st.concl.sup));
    }
    L.push('');
    L.push('六、反思');
    L.push(st.reflect || '（未填写）');
    L.push('');
    L.push('自评：' + (st.self ? st.self + ' / 5 星' : '未评') +
           '　　互评：' + (st.peer ? (st.peer + ' / 5 星' + (st.peerName ? '（' + st.peerName + '）' : '')) : '未评'));
    L.push('');
    L.push('—— 由 初中光学 · 交互实验室 自动生成 ' + RPT_BUILD);
    return L.join('\n');
  }

  /* ---------- 导出 HTML（自包含 / A4 打印友好 / 内嵌画布截图） ---------- */
  function buildExportHtml(st){
    var e = E;
    var dtab = '';
    if(st.data.rows.length){
      dtab = '<table class="dt"><thead><tr>' + st.data.head.map(function(h){ return '<th>' + e(h) + '</th>'; }).join('') +
        '</tr></thead><tbody>' + st.data.rows.map(function(r){
          return '<tr>' + r.map(function(c){ return '<td>' + e(c) + '</td>'; }).join('') + '</tr>';
        }).join('') + '</tbody></table>';
    }
    var lv = '';
    if(st.live && st.live.length){
      lv = '<p class="live"><b>当前画布参数</b>：' + st.head.map(function(h, i){
        return e(h) + ' = <b>' + e(st.live[i] == null ? '—' : st.live[i]) + '</b>';
      }).join('　·　') + '</p>';
    }
    var shot = '';
    try{
      var cv = document.getElementById(st.meta.canvas);
      if(cv && cv.toDataURL) shot = '<img class="shot" alt="实验画布截图" src="' + cv.toDataURL('image/png') + '">';
    }catch(err){ shot = ''; }

    var concl = st.concl
      ? ('<div class="concl"><p class="claim">' + st.concl.claim + '</p>' +
         '<p class="evid">📊 ' + st.concl.evid + '</p>' +
         '<p class="sup">💡 ' + st.concl.sup + '</p></div>')
      : '<div class="no">数据不足，暂无法归纳结论。请先回到实验页多测几组数据。</div>';

    var steps = st.meta.steps.map(function(s){ return '<li>' + e(s) + '</li>'; }).join('');
    var stars = function(n){ var s = ''; for(var i = 1; i <= 5; i++) s += (i <= n ? '★' : '☆'); return s; };

    var css = [
      ':root{color-scheme:light}',
      '*{box-sizing:border-box}',
      'body{margin:0;padding:20px 14px;background:#f6f1d8;color:#17150e;',
      ' font:15px/1.75 "Microsoft YaHei","PingFang SC",-apple-system,system-ui,sans-serif}',
      '.page{max-width:860px;margin:0 auto;background:#fffef2;border:2px solid #17150e;border-radius:12px;',
      ' padding:26px 24px 30px;box-shadow:5px 5px 0 #17150e}',
      'h1{font-size:22px;margin:0 0 5px;line-height:1.3}',
      '.meta{display:flex;flex-wrap:wrap;gap:6px 20px;font-size:13px;color:#6b6449;',
      ' border-bottom:1px dashed #17150e;padding-bottom:10px;margin:12px 0 4px}',
      'h2{font-size:16px;margin:22px 0 9px;padding:6px 11px;background:#efe9cf;border-left:7px solid #7da914;border-radius:4px}',
      'ol,ul{margin:0;padding-left:21px}li{margin-bottom:4px}',
      '.stu{background:#f5f9e6;border:1px dashed #17150e;border-radius:8px;padding:10px 12px;white-space:pre-wrap;min-height:44px}',
      '.empty{color:#6b6449}',
      'table.dt{width:100%;border-collapse:collapse;font-size:13px}',
      'table.dt th,table.dt td{border:1px solid #17150e;padding:5px 8px;text-align:center}',
      'table.dt th{background:#efe9cf;font-weight:700}',
      'table.dt td:last-child{text-align:left}',
      '.live{font-size:12.5px;color:#6b6449;margin-top:8px}',
      '.live b{color:#185fa5}',
      '.concl{border:2px solid #17150e;border-left-width:8px;border-radius:8px;padding:11px 13px;background:#fffef2}',
      '.concl .claim{font-size:15px;margin:0 0 8px}',
      '.concl .evid,.concl .sup{font-size:13px;color:#3d3a2c;margin:6px 0 0}',
      '.concl .sup{border-top:1px dashed #17150e;padding-top:7px}',
      '.no{border:1px dashed #c8331f;background:#fff2f0;color:#c8331f;border-radius:8px;padding:10px 12px;font-size:13px}',
      'img.shot{max-width:100%;height:auto;border:2px solid #17150e;border-radius:8px;margin-top:8px;display:block}',
      '.var{background:#efe9cf;border-radius:8px;padding:9px 12px;font-size:13.5px}',
      '.var b{display:inline-block;min-width:66px}',
      '.eval{display:flex;flex-wrap:wrap;gap:10px 26px;font-size:14px;margin-top:6px;align-items:baseline}',
      '.eval span{font-weight:700}',
      '.stars{color:#7da914;font-size:17px;letter-spacing:2px}',
      'footer{margin-top:24px;border-top:1px dashed #17150e;padding-top:10px;font-size:12px;color:#6b6449;',
      ' display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}',
      '#pb{position:fixed;right:14px;top:14px;background:#c8f04f;color:#17150e;border:2px solid #17150e;',
      ' border-radius:8px;padding:8px 14px;font:700 14px/1 inherit;cursor:pointer;box-shadow:3px 3px 0 #17150e}',
      '@media print{body{background:#fff;padding:0}.page{border:none;box-shadow:none;border-radius:0;',
      ' max-width:none;padding:0 0 8px}#pb{display:none}',
      ' h2{-webkit-print-color-adjust:exact;print-color-adjust:exact;page-break-after:avoid}',
      ' .concl,table.dt,img.shot,.stu{page-break-inside:avoid}',
      ' img.shot{max-width:74%}}',
      '@page{margin:14mm 12mm}'
    ].join('\n');

    var body = [
      '<div class="page">',
      '<h1>' + e(st.meta.name) + ' · 实验报告</h1>',
      '<div class="meta"><span>姓名：' + e(st.name || '＿＿＿＿＿＿') + '</span>',
      '<span>日期：' + e(st.date || todayStr()) + '</span>',
      '<span>实验：' + e(st.meta.name) + '</span>',
      '<span>生成版本：' + e(RPT_BUILD) + '</span></div>',
      '<h2>一、问题</h2><p>' + e(st.meta.question) + '</p>',
      '<h2>二、猜想</h2><div class="stu">' + (st.hypo ? e(st.hypo) : '<span class="empty">（未填写）</span>') + '</div>',
      '<h2>三、方案</h2>',
      '<p><b>实验器材：</b>' + e(st.meta.apparatus) + '</p>',
      '<p style="margin-bottom:6px"><b>变量控制：</b></p>',
      '<div class="var"><b>自变量</b>：' + e(st.meta.vars.iv) + '<br><b>因变量</b>：' + e(st.meta.vars.dv) +
        '<br><b>控制变量</b>：' + e(st.meta.vars.cv) + '</div>',
      '<p style="margin-top:11px"><b>实验步骤：</b></p><ol>' + steps + '</ol>',
      '<h2>四、数据（数据表）</h2>',
      (st.data.rows.length
        ? dtab + lv + '<p class="live">共 ' + st.rows + ' 组，均由各实验画布的真实参数自动记录。</p>'
        : '<div class="no">暂无数据。</div>'),
      shot,
      '<h2>五、结论</h2>',
      concl,
      '<h2>六、反思</h2>',
      '<div class="stu">' + (st.reflect ? e(st.reflect) : '<span class="empty">（未填写）</span>') + '</div>',
      '<h2>七、评价</h2>',
      '<div class="eval"><span>自评：</span><span class="stars">' + stars(st.self) + '</span><span>' + (st.self ? st.self + ' / 5 星' : '未评') + '</span></div>',
      '<div class="eval"><span>互评：</span><span class="stars">' + stars(st.peer) + '</span><span>' + (st.peer ? (st.peer + ' / 5 星' + (st.peerName ? '（' + e(st.peerName) + '）' : '')) : '未评') + '</span></div>',
      '<footer><span>初中光学 · 交互实验室　科学探究六要素报告</span><span>生成时间：' + new Date().toLocaleString() + '</span></footer>',
      '</div>',
      '<button id="pb" type="button">🖨 打印 / 存为 PDF</button>',
      '<scr' + 'ipt>document.getElementById("pb").addEventListener("click",function(){window.print()});</scr' + 'ipt>'
    ].join('\n');

    return '<!DOCTYPE html>\n<html lang="zh-Hans">\n<head>\n<meta charset="utf-8">\n' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">\n' +
      '<title>实验报告 · ' + e(st.meta.name) + '</title>\n<style>\n' + css + '\n</style>\n</head>\n<body>\n' +
      body + '\n</body>\n</html>';
  }

  /* ---------- 记住最近打开的（非报告）实验 ---------- */
  document.addEventListener('click', function(ev){
    var b = (ev.target && ev.target.closest) ? ev.target.closest('.tab-btn') : null;
    if(!b) return;
    var t = b.dataset ? b.dataset.tab : null;
    if(t && TAB2KEY[t]) lastExp = TAB2KEY[t];
  }, true);

  return { render: render, collect: collect, META: META, TAB2KEY: TAB2KEY, buildExportHtml: buildExportHtml };
})();

/* 注册为第 12 个模块：switchTab('report') 与语言切换都会触发 render() */
MODULES.report = { render: function(){ if(window.REPORT) REPORT.render(); } };
"""


def main():
    s = open(SRC, encoding="utf-8").read()
    n0 = len(s)

    # ---------- 1. 版本号 ----------
    s = rep(s, "var BUILD = 'v5.1.0', MAX_SHOW = 3,", "var BUILD = 'v5.1.1', MAX_SHOW = 3,", 1, "BUILD 常量 v5.1.0 -> v5.1.1")
    s = rep(s,
            '<div class="ver-badge" title="光学交互实验室 V5.1.0 · 数据自动记录 + 判卷错因归因">v5.1.0</div>',
            '<div class="ver-badge" title="光学交互实验室 V5.1.1 · 实验报告自动生成（探究六要素）+ 一键导出">v5.1.1</div>',
            1, "右下角版本角标")

    # ---------- 2. 报告 CSS ----------
    s = rep(s,
            '  html[data-mode="mobile"] html, html[data-mode="mobile"] body{overscroll-behavior:none}\n</style>',
            '  html[data-mode="mobile"] html, html[data-mode="mobile"] body{overscroll-behavior:none}\n' + CSS_BLOCK + '</style>',
            1, "注入报告面板 CSS")

    # ---------- 3. 导航按钮 ----------
    s = rep(s,
            '    <button class="tab-btn" data-tab="judge" data-i18n="tab.judge">11 · 挑战模式 ⭐</button>\n  </div>',
            '    <button class="tab-btn" data-tab="judge" data-i18n="tab.judge">11 · 挑战模式 ⭐</button>\n'
            '    <button class="tab-btn" data-tab="report" data-i18n="tab.report">12 · 实验报告 📝</button>\n  </div>',
            1, "导航新增第 12 个标签")

    # ---------- 4. 报告面板 ----------
    s = rep(s,
            '  </section>\n\n</div>\n\n<!-- 关于弹窗 -->',
            '  </section>\n' + PANEL_HTML + '\n</div>\n\n<!-- 关于弹窗 -->',
            1, "注入 #tab-report 面板")

    # ---------- 5. I18N ----------
    s = rep(s,
            '/* I18N-PART2 */\n/* ---- 通用弹窗 / AI 设置 ---- */',
            I18N_ADD + '/* ---- 通用弹窗 / AI 设置 ---- */',
            1, "I18N 追加报告条目")

    # ---------- 6. REC 暴露 snapshot / specOf ----------
    s = rep(s,
            '  function commit(k, force){',
            '  // V5.1.1：对外暴露取值能力，供「实验报告」取画布实时参数\n'
            '  function snapshot(k){\n'
            '    var sp = specs[k];\n'
            '    if (!sp) return null;\n'
            '    try { return sp.getRow() || null; } catch(e){ return null; }\n'
            '  }\n'
            '  function specOf(k){ return specs[k] || null; }\n\n'
            '  function commit(k, force){',
            1, "REC 新增 snapshot/specOf")

    s = rep(s,
            '  return { register: register, touch: touch, commit: commit,\n'
            '           setEnabled: setEnabled, isEnabled: function(){ return enabled; } };',
            '  return { register: register, touch: touch, commit: commit,\n'
            '           setEnabled: setEnabled, isEnabled: function(){ return enabled; },\n'
            '           snapshot: snapshot, specOf: specOf };',
            1, "REC 导出 snapshot/specOf")

    s = rep(s,
            '  if (window.REC) REC.register(key, { getRow: getRow, add: addRow, node: tbody });',
            '  if (window.REC) REC.register(key, { getRow: getRow, add: addRow, node: tbody, headers: headers, csvName: csvName });',
            1, "REC.register 带上 headers")

    # ---------- 7. 报告 JS 模块 ----------
    s = rep(s, '// 通用：保存 canvas 为图片', REPORT_JS + '\n// 通用：保存 canvas 为图片', 1, "注入 REPORT 模块")

    # ---------- 8. 更新日志 ----------
    LOG_ITEM = (
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V5.1.1</span><span class="log-date">2026-09-15</span></div>\n'
        '        <p>补齐「科学探究」闭环的最后一环——<strong>实验报告自动生成</strong>。新增第 12 个实验报告页，'
        '按<strong>问题 → 猜想 → 方案 → 数据 → 结论 → 反思</strong>六要素组织：问题、方案（含<strong>变量控制</strong>：自变量 / 因变量 / 控制变量与实验步骤）、'
        '<strong>数据表</strong>、结论均由各实验<strong>画布的真实参数</strong>自动取值（复用 V5.1.0 的自动记录器，并可一键把当前画布读数补记入表）；'
        '猜想与反思由学生填写，附预设句一键填入；另含<strong>自评 / 互评</strong>五星评价与六要素完成度进度条。</p>\n'
        '        <p>一键导出：导出自包含 <strong>HTML 报告</strong>（A4 打印友好、手机可读、内嵌实验画布截图）、'
        '复制纯文本报告、导出数据 CSV，或直接在新标签打开<strong>打印 / 存为 PDF</strong>。全部离线可用，不需要任何 API Key。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V5.1.0</span>'
    )
    s = rep(s,
            '      <div class="log-item cur">\n'
            '        <div class="log-head"><span class="log-ver">V5.1.0</span>',
            LOG_ITEM,
            1, "更新日志新增 V5.1.1 条目")

    open(DST, "w", encoding="utf-8").write(s)
    print("\n".join(LOG))
    print("-" * 72)
    # 注意：len(str) 是「字符数」不是「字节数」（中文 3 字节/字），这里统一按真实字节数报告
    b0, b1 = os.path.getsize(SRC), os.path.getsize(DST)
    print("源   %.2f MB (%d 字节, %d 字符)" % (b0 / 1e6, b0, n0))
    print("产物 %.2f MB (%d 字节, %d 字符)  +%.1f KB (+%.2f%%)" % (b1 / 1e6, b1, len(s), (b1 - b0) / 1024, (b1 - b0) / b0 * 100))
    print("输出：", DST)


if __name__ == "__main__":
    main()
