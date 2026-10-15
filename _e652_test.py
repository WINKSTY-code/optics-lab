# -*- coding: utf-8 -*-
"""
V6.5.2 e2e：真实 Chromium 验证「AI 设置新增 MiniMax-M3.1-Flash-Preview」
同时把 V6.5.1 跑一遍做前后对照（前者不应含新条目）。
"""
import os, re, json, pathlib
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.5.2.html")
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.5.1.html")

PROVIDERS = ["none", "zhipu", "deepseek", "minimax", "kimi", "openai", "anthropic"]

# 本作品基线（V6.5.1 实测：11 nav / 11 canvas / 12 panel / 11 tab-btn）
BASE_LINE = {"tabBtnPrefix": 11, "canvas": 11, "panel": 12}

PROBE = """
() => {
  const q = s => document.querySelector(s);
  const badge = q('.ver-badge');
  const out = {
    badge: badge ? badge.textContent.trim() : null,
    badgeTitle: badge ? badge.getAttribute('title') : null,
    ready: window.__APP_READY === true,
    rbErrs: (window.__rbErrors || []).length,
    overlay: !!q('#__rbOverlay'),
    navs: document.querySelectorAll('.tab-btn').length,
    canvases: document.querySelectorAll('canvas').length,
    panels: document.querySelectorAll('.panel').length,
  };
  return out;
}
"""

def run(pg, url, tag):
    pg.goto(url, wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    # ① 首启弹窗（学生姓名窗）走真实流程（§19②）
    if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
        pg.fill("#stuName", "E2E测试")
        pg.fill("#stuNo", "E2E")
        pg.click("#stuAdd")
        pg.wait_for_timeout(800)
    # 清遮罩（只认 .modal-mask，.show / .is-closing 都摘）
    clear_masks(pg)

    info = pg.evaluate(PROBE)

    # ② 走真实 UI 打开 AI 设置：设置 → AI 设置
    pg.click("#setBtn")
    pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn")
    pg.wait_for_timeout(500)
    assert pg.is_visible("#aiProvider"), "[FAIL] AI 设置弹窗未打开"

    # ③ 逐厂商枚举模型下拉的完整选项序列
    opts = {}
    for p in PROVIDERS:
        pg.select_option("#aiProvider", p)
        pg.wait_for_timeout(160)
        opts[p] = pg.eval_on_selector(
            "#aiModel", "el => [...el.options].map(o => o.value)")

    # ④ 选新模型 → 自定义输入框必须保持隐藏（基线版本没有该条目，对照组改选已存在项）
    pg.select_option("#aiProvider", "minimax")
    pg.wait_for_timeout(200)
    NEWM = "MiniMax-M3.1-Flash-Preview"
    if NEWM in opts["minimax"]:
        pg.select_option("#aiModel", NEWM)
        pg.wait_for_timeout(200)
        pick = pg.evaluate("""() => {
          const ml = document.getElementById('aiModel'), cu = document.getElementById('aiModelCustom');
          const o = ml.options[ml.selectedIndex];
          return { val: ml.value, label: o.textContent,
                   customHidden: getComputedStyle(cu).display === 'none' };
        }""")
    else:
        pg.select_option("#aiModel", "MiniMax-M2.7")
        pg.wait_for_timeout(200)
        pick = None

    if tag == "DST":
        box = pg.eval_on_selector(".modal", "e => { const r = e.getBoundingClientRect();"
                                           "return {x:r.x, y:r.y, width:r.width, height:r.height}; }")
        pg.screenshot(path=os.path.join(BASE, "_chk652", "cfg_minimax.png"),
                      clip={"x": max(0, box["x"] - 8), "y": max(0, box["y"] - 8),
                            "width": box["width"] + 16, "height": box["height"] + 16})

    # ⑤ 保存（alert 自动 dismiss）→ 关闭 → 重新打开确认回显
    pg.click("#aiCfgSave")
    pg.wait_for_timeout(400)
    saved = pg.evaluate("() => JSON.parse(localStorage.getItem('ai_optics_v1_cfg')||'{}').model")
    pg.click("#aiCfgClose")
    pg.wait_for_timeout(300)
    pg.click("#setBtn"); pg.wait_for_timeout(200)
    pg.click("#aiCfgBtn"); pg.wait_for_timeout(500)
    reopen = pg.evaluate("""() => {
      const ml = document.getElementById('aiModel');
      return { prov: document.getElementById('aiProvider').value, model: ml.value,
               opts: [...ml.options].map(o => o.value) };
    }""")
    pg.click("#aiCfgClose")
    pg.wait_for_timeout(300)

    # ⑥ 更新日志（两级弹窗：关于 → 更新日志）
    pg.click("#signBtn")
    pg.wait_for_timeout(1300)
    pg.click("#aboutLog")
    pg.wait_for_timeout(1400)
    log = pg.evaluate("""() => {
      const items = [...document.querySelectorAll('#logMask .log-item')];
      return { n: items.length,
               cur: items.filter(i => i.classList.contains('cur')).map(i => i.querySelector('.log-ver').textContent),
               curText: (items.find(i => i.classList.contains('cur')) || {}).innerText,
               vers: items.map(i => i.querySelector('.log-ver').textContent),
               first3: items.slice(0, 3).map(i => i.innerText.replace(/\\s+/g, ' ')) };
    }""")
    if tag == "DST":
        box = pg.eval_on_selector("#logMask .modal", "e => { const r = e.getBoundingClientRect();"
                                                     "return {x:r.x, y:r.y, width:r.width, height:r.height}; }")
        pg.screenshot(path=os.path.join(BASE, "_chk652", "changelog.png"),
                      clip={"x": max(0, box["x"] - 8), "y": max(0, box["y"] - 8),
                            "width": box["width"] + 16, "height": box["height"] + 16})

    return {"info": info, "opts": opts, "pick": pick, "saved": saved,
            "reopen": reopen, "log": log}


def clear_masks(pg):
    pg.evaluate("""() => {
      document.querySelectorAll('.modal-mask').forEach(function(m){
        m.classList.remove('show'); m.classList.remove('is-closing');
      });
    }""")


CK = []
def ck(cond, msg):
    CK.append(("  OK  " if cond else "  !!  ") + msg)
    assert cond, "[FAIL] " + msg


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    # 外链字体/脚本一律 abort：否则截图会卡在 document.fonts.ready（§59③）
    for pat in ("**/cdn.jsdelivr.net/**", "**/fonts.googleapis.com/**",
                "**/fonts.gstatic.com/**", "**/unpkg.com/**"):
        pg.route(pat, lambda r: r.abort())
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

    print("=== 基线（V6.5.1）===")
    A = run(pg, pathlib.Path(SRC).resolve().as_uri(), "SRC")
    print("  badge:", A["info"]["badge"])
    print("  minimax opts:", A["opts"]["minimax"])
    print("  log cur:", A["log"]["cur"], "| n =", A["log"]["n"])

    print("\n=== 产物（V6.5.2）===")
    B = run(pg, pathlib.Path(DST).resolve().as_uri(), "DST")
    print("  badge:", B["info"]["badge"])
    print("  minimax opts:", B["opts"]["minimax"])
    print("  all opts:", json.dumps(B["opts"], ensure_ascii=False))
    print("  pick:", B["pick"])
    print("  log cur:", B["log"]["cur"], "| n =", B["log"]["n"])
    for ln in B["log"]["first3"]:
        print("    -", ln)
    print("  console errors:", [e for e in errs if not re.search(
        r"favicon|Failed to load resource|net::ERR_FAILED|ERR_BLOCKED", e)])

    print("\n=== 断言 ===")
    # 健康信号
    ck(B["info"]["ready"] is True, "V6.5.2：__APP_READY 已置真")
    ck(B["info"]["rbErrs"] == 0, "V6.5.2：作品自带错误账本为空")
    ck(B["info"]["overlay"] is False, "V6.5.2：无启动失败浮层")
    ck(not [e for e in errs if not re.search(
        r"favicon|Failed to load resource|net::ERR_FAILED|ERR_BLOCKED", e)],
       "V6.5.2：控制台无真实错误（已滤掉测试自身 abort CDN 的噪声）")
    # 回归基线
    ck(B["info"]["navs"] == BASE_LINE["tabBtnPrefix"], "回归：.tab-btn = %d" % B["info"]["navs"])
    ck(B["info"]["canvases"] == BASE_LINE["canvas"], "回归：canvas = %d" % B["info"]["canvases"])
    ck(B["info"]["panels"] == BASE_LINE["panel"], "回归：.panel = %d" % B["info"]["panels"])
    # 版本号三处
    ck(B["info"]["badge"] == "v6.5.2", "版本角标文本 = v6.5.2")
    ck("V6.5.2" in (B["info"]["badgeTitle"] or ""), "角标 title 含 V6.5.2")
    ck("MiniMax-M3.1-Flash-Preview" in (B["info"]["badgeTitle"] or ""), "角标 title 写明新模型")
    ck("gpt-6-sol" not in (B["info"]["badgeTitle"] or ""), "角标 title 不再挂上一版说明")
    # ★ 核心：完整选项序列
    ck(B["opts"]["minimax"] == ["MiniMax-M3", "MiniMax-M3.1-Flash-Preview", "MiniMax-M2.7", "__custom__"],
       "minimax 完整选项序列 = %s" % B["opts"]["minimax"])
    ck(A["opts"]["minimax"] == ["MiniMax-M3", "MiniMax-M2.7", "__custom__"],
       "对照：V6.5.1 原本没有该条目（%s）" % A["opts"]["minimax"])
    ck(B["opts"]["openai"] == B["opts"]["openai"] and
       B["opts"]["openai"] == ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-luna", "__custom__"],
       "不该动的：openai 序列逐项未变")
    ck(B["opts"]["anthropic"] == ["claude-fable-5.1", "claude-opus-5.5", "claude-opus-5", "__custom__"],
       "不该动的：anthropic 序列逐项未变")
    ck(B["opts"]["zhipu"] == A["opts"]["zhipu"] and B["opts"]["kimi"] == A["opts"]["kimi"]
       and B["opts"]["deepseek"] == A["opts"]["deepseek"],
       "不该动的：zhipu / kimi / deepseek 与 V6.5.1 逐项一致")
    # 选择与持久化
    ck(B["pick"]["val"] == "MiniMax-M3.1-Flash-Preview", "可选中新模型")
    ck(B["pick"]["label"] == "MiniMax-M3.1-Flash-Preview", "选项标签无多余 tag：%r" % B["pick"]["label"])
    ck(B["pick"]["customHidden"] is True, "选中预置模型时自定义输入框保持隐藏")
    ck(B["saved"] == "MiniMax-M3.1-Flash-Preview", "保存后 localStorage.model 落库正确")
    ck(B["reopen"]["model"] == "MiniMax-M3.1-Flash-Preview" and
       B["reopen"]["prov"] == "minimax", "重开弹窗回显正确")
    # 更新日志
    ck(B["log"]["cur"] == ["V6.5.2"], "更新日志 cur 唯一且为 V6.5.2")
    ck("新增模型支持：MiniMax-M3.1-Flash-Preview。" in (B["log"]["curText"] or ""),
       "新日志正文正确")
    ck(B["log"]["vers"][1] == "V6.5.1", "V6.5.1 历史条目仍在第二位（历史不被覆写）")
    ck(B["log"]["n"] == A["log"]["n"] + 1, "日志条数 %d = 基线 %d + 1" % (B["log"]["n"], A["log"]["n"]))
    ck(B["log"]["vers"][2:] == A["log"]["vers"][1:], "第三条起与基线逐条一致（顺序未乱）")

    b.close()

print("\n".join(CK))
print("\n[PASS] %d 项断言全部通过" % len(CK))
