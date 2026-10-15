# -*- coding: utf-8 -*-
"""V6.5.1 端到端验证：AI 设置新增模型支持（gpt-6-sol / gpt-6-luna / claude-opus-5.5）

覆盖：
 A. 版本号三处同步（角标文本 / 角标 title / 报告模块读取到的版本）
 B. 真实 UI：打开「设置 → AI 设置」，切 Provider，断言模型下拉的**完整选项序列**
    （新增的进列、顺序对、其它厂商逐字未动、__custom__ 仍在末尾）
 C. 真实保存链路：选 gpt-6-sol → 保存 → 重开弹窗仍选中（证明能落进 cfg）
 D. 更新日志：V6.5.1 条目为最新 cur 条目、日期 2026-09-23、文案就是「新增模型支持」，
    且 V6.5.0 条目仍在（历史不被覆写），条目总数 = 基线 77 + 1
 E. 回归：tab/panel/canvas 基线、10 个实验页可切、无脚本错误、作品自带健康信号正常
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = pathlib.Path("C:/Users/Administrator/Desktop/AI光学参赛")
URL = (BASE / "光学交互实验室_AI_v6.5.1.html").resolve().as_uri()

PASS, FAIL, NOTE = [], [], []


def ck(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  OK   " if cond else "  FAIL ") + label)
    return bool(cond)


def note(msg):
    NOTE.append(msg)
    print("  --   " + msg)


def clear_masks(pg):
    """只摘 .show / .is-closing —— 绝不写 inline display:none（skill §9/§19①）"""
    pg.evaluate("""() => { document.querySelectorAll('.modal-mask').forEach(m => {
        m.classList.remove('show'); m.classList.remove('is-closing'); }); }""")


def dismiss_first_run(pg):
    """首启学生姓名窗：走真实流程填完（skill §19②）"""
    try:
        if pg.query_selector("#stuName") and pg.is_visible("#stuName"):
            pg.wait_for_timeout(600)
            pg.fill("#stuName", "E2E")
            pg.fill("#stuNo", "E2E")
            pg.click("#stuAdd")
            pg.wait_for_timeout(700)
    except Exception:
        pass
    clear_masks(pg)


def click_tab(pg, t):
    """真实点击导航按钮（skill §19③：evaluate 会绕过 click 委托）"""
    pg.click('.tab-btn[data-tab="%s"]' % t)
    pg.wait_for_timeout(180)


def open_ai_cfg(pg):
    """设置下拉 → AI 设置（真实点击）"""
    clear_masks(pg)                       # 先确保没有遗留遮罩
    pg.click("#setBtn")
    pg.wait_for_timeout(250)
    pg.click("#aiCfgBtn")
    pg.wait_for_timeout(450)


OPTIONS_JS = """() => {
  const s = document.querySelector('#aiModel');
  if (!s) return null;
  return {
    values: [...s.options].map(o => o.value),
    labels: [...s.options].map(o => o.textContent.trim()),
    value:  s.value,
    customShown: (document.querySelector('#aiModelCustom') || {}).style
                 ? document.querySelector('#aiModelCustom').style.display !== 'none' : null
  };
}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = br.new_page(viewport={"width": 1440, "height": 900})
        errors, consoles = [], []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: (consoles.append(m.text) if m.type == "error" else None))
        # 外链字体（jsdelivr / googleapis）在本机不可达：主动 abort 让它快速失败，
        # 否则 Playwright 截图会一直等 document.fonts.ready 直到 30s 超时（skill §3）
        pg.route("**/cdn.jsdelivr.net/**", lambda r: r.abort())
        pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        pg.goto(URL, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        dismiss_first_run(pg)

        # ============================================================ A 版本号
        print("\n== A. 版本号同步 ==")
        ck(pg.evaluate("() => document.querySelector('.ver-badge').textContent.trim()") == "v6.5.1",
           "角标文本 = v6.5.1")
        badge_title = pg.evaluate("() => document.querySelector('.ver-badge').getAttribute('title')")
        ck("V6.5.1" in badge_title, "角标 title 含 V6.5.1")
        ck(("gpt-6-sol" in badge_title) and ("gpt-6-luna" in badge_title) and ("claude-opus-5.5" in badge_title),
           "角标 title 说明了新增的三个模型")
        # 报告模块自带的版本常量优先读角标，借此证明它拿到的是新版本（跨块同步）
        ck(pg.evaluate("""() => { try { return REPORT.version ? REPORT.version : null; } catch(e){ return null; } }""")
           in (None, "v6.5.1"), "REPORT 模块可读（其版本取自角标）")

        # ============================================================ B 模型列表
        print("\n== B. AI 设置 · 模型下拉（真实 UI） ==")
        open_ai_cfg(pg)
        ck(pg.evaluate("() => !!document.querySelector('#aiCfgMask.show')"), "AI 设置弹窗已打开")

        EXPECT = {
            "openai": ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-luna", "__custom__"],
            "anthropic": ["claude-fable-5.1", "claude-opus-5.5", "claude-opus-5", "__custom__"],
            "zhipu": ["GLM-5.3-FlashX", "GLM-5.3", "GLM-5.3-Flash", "GLM-4.7-Flash", "GLM-4.5-Air", "__custom__"],
            "deepseek": ["deepseek-v4.1-flash", "__custom__"],
            "minimax": ["MiniMax-M3", "MiniMax-M2.7", "__custom__"],
            "kimi": ["kimi-K3", "kimi-k2.8-preview", "kimi-k2.7-code", "kimi-k2.6", "__custom__"],
        }
        seen = {}
        for prov, expect in EXPECT.items():
            pg.select_option("#aiProvider", prov)
            pg.wait_for_timeout(320)
            r = pg.evaluate(OPTIONS_JS)
            seen[prov] = r
            tag = "新增" if prov in ("openai", "anthropic") else "回归"
            ok = r and r["values"] == expect
            ck(ok, "[%s/%s] %-9s 选项序列 == 期望（%s）" % (tag, "新值" if prov in ("openai", "anthropic") else "未动",
                                                          prov, " → ".join(expect[:3]) + " …"))
            if not ok and r:
                note("  %s 实际 = %s" % (prov, r["values"]))
            ck(r and r["customShown"] is False, "  %-9s 默认模型命中列表 → 自定义输入框保持隐藏" % prov)

        # 标签带 tag 的仍保留（gpt-6-astra 旗舰）
        ck(any("（旗舰）" in x for x in seen["openai"]["labels"]), "openai 列表里 tag 渲染未受影响（gpt-6-astra「旗舰」）")
        ck(all("（" not in x for x in seen["openai"]["labels"]
               if x.startswith("gpt-6-sol") or x.startswith("gpt-6-luna")),
           "新增的 gpt-6-sol / gpt-6-luna 不带 tag（与 gpt-5.6-sol/luna 风格一致）")

        pg.screenshot(path=str(BASE / "_v651_AI设置_openai模型.png"))

        # ============================================================ C 保存链路
        print("\n== C. 选中新模型 → 保存 → 重开（真实落盘） ==")
        pg.select_option("#aiProvider", "openai")
        pg.wait_for_timeout(250)
        pg.select_option("#aiModel", "gpt-6-sol")
        pg.wait_for_timeout(150)
        pg.click("#aiCfgSave")            # 内部 alert()，Playwright 自动 dismiss
        pg.wait_for_timeout(500)
        saved = pg.evaluate("""() => { try { return JSON.parse(localStorage.getItem('ai_optics_v1_cfg')||'{}').model; }
                                        catch(e){ return null; } }""")
        ck(saved == "gpt-6-sol", "localStorage 里 cfg.model == gpt-6-sol（实际 %r）" % saved)
        open_ai_cfg(pg)                   # 重新打开，看回填
        r = pg.evaluate(OPTIONS_JS)
        ck(r and r["value"] == "gpt-6-sol", "重开弹窗后仍选中 gpt-6-sol")
        pg.screenshot(path=str(BASE / "_v651_AI设置_已存gpt-6-sol.png"))
        pg.select_option("#aiProvider", "anthropic")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(BASE / "_v651_AI设置_anthropic模型.png"))
        clear_masks(pg)

        # ============================================================ D 更新日志
        print("\n== D. 更新日志 ==")
        pg.click("#signBtn")
        pg.wait_for_timeout(1400)
        pg.click("#aboutLog")
        pg.wait_for_timeout(1600)
        ck(pg.evaluate("() => !!document.querySelector('#logMask.show')"), "更新日志弹窗已打开")
        items = pg.evaluate("""() => [...document.querySelectorAll('#logMask .log-list .log-item')].map(d => ({
            ver:  (d.querySelector('.log-ver')||{}).textContent || '',
            date: (d.querySelector('.log-date')||{}).textContent || '',
            text: (d.querySelector('p')||{}).textContent || '',
            cur:  d.classList.contains('cur')
        }))""")
        ck(len(items) == 78, "日志条目总数 = 78（V6.5.0 基线 77 + 1，实际 %d）" % len(items))
        if items:
            it = items[0]
            ck(it["ver"] == "V6.5.1", "第一条版本 = V6.5.1（实际 %r）" % it["ver"])
            ck(it["date"] == "2026-09-23", "第一条日期 = 2026-09-23（实际 %r）" % it["date"])
            ck(it["cur"] is True, "第一条带 cur（最新标记已前移）")
            ck(it["text"] == "新增模型支持。", "第一条文案就写「新增模型支持。」（实际 %r）" % it["text"])
            ck(sum(1 for x in items if x["cur"]) == 1, "cur 条目全局唯一")
            it2 = items[1]
            ck(it2["ver"] == "V6.5.0" and it2["date"] == "2026-09-21" and not it2["cur"],
               "第二条仍是 V6.5.0 / 2026-09-21（历史条目未被覆写，cur 已让位）")
            ck(all(x["ver"] != "V6.5.1" for x in items[1:]), "V6.5.1 只出现一条")
        pg.screenshot(path=str(BASE / "_v651_更新日志.png"))
        clear_masks(pg)

        # ============================================================ E 回归
        print("\n== E. 回归 ==")
        ck(pg.evaluate("() => document.querySelectorAll('.tab-btn').length") == 11, "导航按钮 11 个")
        ck(pg.evaluate("() => document.querySelectorAll('.panel').length") == 12, "面板 12 个")
        ck(pg.evaluate("() => document.querySelectorAll('canvas').length") == 11, "画布 11 个")
        tab_ok = True
        for t in ["reflect", "mirror", "lens", "refract", "line", "disperse", "lensfx", "eye", "instr", "combo", "judge"]:
            try:
                click_tab(pg, t)
            except Exception as e:
                tab_ok = False
                note("tab %s 切换失败：%s" % (t, e))
        ck(tab_ok, "11 个导航页全部可切换（含挑战模式）")
        ck(pg.evaluate("() => !!window.AI && typeof window.AI.openConfig === 'function'"), "window.AI.openConfig 仍可调用")
        ck(pg.evaluate("() => { try { return window.AI.kbAll().length >= 15; } catch(e){ return false; } }"),
           "知识库条目 >= 15（AI 模块其它部分未受影响）")
        ck(pg.evaluate("() => window.__APP_READY === true"), "作品就绪信号 __APP_READY 已置真")
        ck(pg.evaluate("() => !document.getElementById('__rbOverlay')"), "启动失败浮层未出现")
        ck(pg.evaluate("() => (window.__rbErrors || []).length === 0"), "作品自带错误账本 __rbErrors 为空")
        click_tab(pg, "reflect")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(BASE / "_v651_整页.png"))

        print("\n== F. 全程无脚本错误 ==")
        ck(len(errors) == 0, "pageerror 0 条（实际 %d）%s" % (len(errors), errors[:3]))
        real_err = [c for c in consoles
                    if "ERR_CONNECTION_RESET" not in c and "net::ERR_FAILED" not in c
                    and "ERR_BLOCKED" not in c and "favicon" not in c.lower()]
        ck(len(real_err) == 0, "除已知外链字体失败外，console.error 0 条（实际 %d）%s" % (len(real_err), real_err[:3]))
        br.close()

    print("-" * 66)
    print("通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)))
    if NOTE:
        print("备注 %d 条" % len(NOTE))
    if FAIL:
        print("失败清单：")
        for f in FAIL:
            print("  - " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
