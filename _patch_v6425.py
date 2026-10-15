# -*- coding: utf-8 -*-
"""V6.4.24 -> V6.4.25
1) AI_TIMEOUT_MS 45s -> 180s（实测 glm-5.3-flash 单次 86.4s，45s 必然掐断）
2) 超时不再触发重试（模型慢时白等第二轮 180s）；网络错误/5xx 仍重试 1 次
3) 超时错误文案同步改 180 秒
4) 等待文案：诊断弹窗 diag.thinking 的括号句 -> 「可能需要 1-2 分钟」；面板内 ai.diagnosing 同步
5) 版本号四处 + 更新日志新增 V6.4.25 首条
断言式替换：每处先校验唯一性计数，全部通过才写回。
"""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

SRC = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.24.html"
DST = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.25.html"

s = io.open(SRC, encoding='utf-8').read()
orig = s
script_tags_before = s.count('<script')

# ---------------- 补丁定义 ----------------
REPL = []

# R1  超时常量 + 上方注释（整块替换）
R1_old = """  /* V6.4.21：单次请求的硬超时统一由这里给出 —— 由 V6.4.17 的 20s 放宽到 45s。
     起因：勾了「深度思考模式」的模型（glm-4.7 / MiniMax-M3 / Claude 等）思考链一长就撞 20s 线，
     「诊断」和「问 AI」会静默掉进本地知识库兜底 —— 用户只看到「AI 没回答」，猜不到其实是本地兜底。
     ⚠️ 本值只作用于「单次尝试」：外面还套着失败重试 1 次（见 fetchWithRetry 的 retries），
        所以真正最坏要等 45s × 2 = 90s 才会掉到本地兜底。若要压总时长，得改重试策略而不是改这里。 */
  const AI_TIMEOUT_MS = 45000;"""
R1_new = """  /* V6.4.25：单次请求的硬超时 45s -> 180s。
     起因（实测，2026-09-21，智谱套餐端点，与课件同款请求体）：
     GLM-5.3-Flash 思考开启时单次真实耗时 86.4s（思考 2992 token / 总输出 4085 token），
     而提示词只有 173 token —— 慢在**输出侧**（强制思考），不是输入侧。
     同一测试里：不传 thinking 128.9s、流式 47.0s、GLM-5.3-FlashX 34.1s、关思考 27.2s。
     → 45s 必然掐断，用户只看到「超时」；放宽到 180s 后 86~129s 的请求都能正常返回。
     ⚠️ 本值是**总等待上限**：V6.4.25 起「超时」不再触发重试（见 fetchWithRetry 的 catch），
        避免模型慢时白等第二轮 180s；网络错误 / 5xx 仍照旧重试 1 次。 */
  const AI_TIMEOUT_MS = 180000;"""
REPL.append(("R1 超时常量 45s->180s", R1_old, R1_new))

# R2  fetchWithRetry：超时不重试
R2_old = """        const msg = String((e && (e.message || e)) || '');
        if(attempt >= retries) break;
        // 最后一次不再重试
        continue;"""
R2_new = """        const msg = String((e && (e.message || e)) || '');
        if(attempt >= retries) break;
        // 最后一次不再重试
        // V6.4.25：超时（AbortError）不再重试 —— 模型本身慢（实测 86~129s），
        // 再等一轮 180s 只会让用户干等更久，且重试也多半再超时。网络层错误仍重试。
        if((e && e.name === 'AbortError') || /abort|timeout/i.test(msg)) break;
        continue;"""
REPL.append(("R2 超时不重试", R2_old, R2_new))

# R3  超时错误文案
R3_old = "throw new Error('请求超时（45 秒未响应），已自动重试 1 次仍失败。请检查网络或稍后再试');"
R3_new = "throw new Error('请求超时（180 秒未响应）。该模型思考耗时较长，可稍后重试；若持续超时请改用更快的模型');"
REPL.append(("R3 超时错误文案", R3_old, R3_new))

# R4  诊断弹窗等待文案
R4_old = "'diag.thinking':  {zh:'诊断中…（若未配置 API Key，将使用本地知识库生成诊断）', zht:'診斷中…（若未配置 API Key，將使用本地知識庫生成診斷）', en:'Diagnosing… (offline knowledge base if no API key)'},"
R4_new = "'diag.thinking':  {zh:'诊断中…（可能需要 1-2 分钟）', zht:'診斷中…（可能需要 1-2 分鐘）', en:'Diagnosing… (may take 1-2 minutes)'},"
REPL.append(("R4 diag.thinking 文案", R4_old, R4_new))

# R5  面板内诊断等待文案（同一动作、同一等待）
R5_old = "'ai.diagnosing':  {zh:'诊断中…', zht:'診斷中…', en:'Diagnosing…'}"
R5_new = "'ai.diagnosing':  {zh:'诊断中…（可能需要 1-2 分钟）', zht:'診斷中…（可能需要 1-2 分鐘）', en:'Diagnosing… (may take 1-2 minutes)'}"
REPL.append(("R5 ai.diagnosing 文案", R5_old, R5_new))

# R6  BUILD
R6_old = "var BUILD = 'v6.4.24', MAX_SHOW = 3"
R6_new = "var BUILD = 'v6.4.25', MAX_SHOW = 3"
REPL.append(("R6 BUILD", R6_old, R6_new))

# R7  RPT_BUILD 兜底值
R7_old = "    return 'v6.4.24';\n  })();"
R7_new = "    return 'v6.4.25';\n  })();"
REPL.append(("R7 RPT_BUILD", R7_old, R7_new))

# R8  版本角标
R8_old = ('<div class="ver-badge" title="光学交互实验室 V6.4.24 · ① 修复 AI 判卷自 V6.4.17 起整条失效'
          '（跨脚本块引用 fetchWithRetry 抛 ReferenceError）；② 判卷输出额度由硬编码 2000 改为按'
          '「判卷模型设置」里的 Provider 分档：智谱 32000、其余 8000。">v6.4.24</div>')
R8_new = ('<div class="ver-badge" title="光学交互实验室 V6.4.25 · ① 单次请求超时 45 秒放宽到 180 秒'
          '（实测智谱 GLM-5.3-Flash 单次需 86.4 秒，慢在思考输出侧）；② 超时不再触发重试，'
          '避免白等第二轮；③ 诊断等待提示改为「可能需要 1-2 分钟」。">v6.4.25</div>')
REPL.append(("R8 版本角标", R8_old, R8_new))

# R9  更新日志：V6.4.24 降级 + 新增 V6.4.25 首条
R9_old = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.24</span><span class="log-date">2026-09-21</span></div>
        <p>修复判卷链路失效，额度按厂商分档。</p>
      </div>"""
R9_new = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.25</span><span class="log-date">2026-09-21</span></div>
        <p>AI 超时 45 秒放宽到 180 秒（实测智谱 GLM-5.3-Flash 单次需 86 秒），超时不再重试。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.24</span><span class="log-date">2026-09-21</span></div>
        <p>修复判卷链路失效，额度按厂商分档。</p>
      </div>"""
REPL.append(("R9 更新日志", R9_old, R9_new))

# ---------------- 应用（先全部校验，再统一写回） ----------------
print("=== V6.4.24 -> V6.4.25 补丁校验 ===")
errs = []
for name, old, new in REPL:
    c = s.count(old)
    flag = "OK " if c == 1 else "FAIL"
    print(f"[{flag}] {name}: 命中 {c} 次")
    if c != 1:
        errs.append(f"{name} 命中 {c} 次（应为 1）")
        continue
    s = s.replace(old, new, 1)

if errs:
    print("\n❌ 校验失败，未写回：")
    for e in errs:
        print("  -", e)
    sys.exit(1)

# 收尾断言
assert 'AI_TIMEOUT_MS = 45000' not in s, "旧超时常量仍在"
assert 'AI_TIMEOUT_MS = 180000' in s, "新超时常量缺失"
assert '请求超时（45 秒未响应）' not in s, "旧超时文案仍在"
assert '（若未配置 API Key，将使用本地知识库生成诊断）' not in s, "旧等待文案仍在"
assert '可能需要 1-2 分钟' in s, "新等待文案缺失"
assert s.count('<script') == script_tags_before, "script 标签计数变化"
assert 'v6.4.24' not in s.replace('V6.4.24', ''), "仍有小写旧版本号残留（排除日志里的 V6.4.24）"

io.open(DST, 'w', encoding='utf-8').write(s)
print(f"\n✅ 全部 {len(REPL)} 处断言通过，已写出：\n   {DST}")
print(f"   源 {len(orig)} B -> 新 {len(s)} B  (Δ {len(s)-len(orig):+d})")
