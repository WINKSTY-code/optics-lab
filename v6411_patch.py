# -*- coding: utf-8 -*-
"""V6.4.11 补丁（v6.4.10 → v6.4.11）
用户反馈：「配置指南不一定非要用智谱，就说一个你想用的 AI 大模型就行了」。

V6.4.10 的指南第①步把「智谱 GLM ⭐ 推荐」当成了指定动作，等于替用户做了选型。
本版把第①步改成泛指 —— 只要求「把 Provider 从『离线（仅 TTS）』换成你想用的 AI 大模型」，
具体选哪家交给用户（Provider 下拉里本来就把可选项都列出来了）。

纯文案改动，不动任何结构，因此补丁面极小。
"""
import os, re

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.10.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.11.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, "r", encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)
closes0 = len(re.findall(r"</script(?=[\s>/])", s))
opens0 = len(re.findall(r"<script(?=[\s>/])", s))
V6410_BEFORE = s.count("V6.4.10")

# ============================================================
# ① 指南第①步：不指定平台，改为「你想用的 AI 大模型」
# ============================================================
s = rep(s,
        "'aiCfg.g1':       {zh:'选平台：把上面的 Provider 从「离线（仅 TTS）」换成「智谱 GLM ⭐ 推荐」。', "
        "zht:'選平台：把上面的 Provider 從「離線（僅 TTS）」換成「智譜 GLM ⭐ 推薦」。', "
        "en:'Pick a provider — switch Provider from “Offline (TTS only)” to “Zhipu GLM ⭐”.'},",
        "'aiCfg.g1':       {zh:'选平台：把上面的 Provider 从「离线（仅 TTS）」换成你想用的 AI 大模型即可。', "
        "zht:'選平台：把上面的 Provider 從「離線（僅 TTS）」換成你想用的 AI 大模型即可。', "
        "en:'Pick a provider — switch Provider from “Offline (TTS only)” to any AI model you want to use.'},",
        1, "① 指南第①步改为泛指（三语）")

# 第②步里的「先在①选好平台」保留（顺序依赖仍然成立），只把「平台」统一成「大模型」更好读
s = rep(s,
        "先在①选好平台，再点上面的「前往官网」注册登录",
        "先在①选好大模型，再点上面的「前往官网」注册登录",
        1, "① 第②步措辞与第①步对齐（zh）")
s = rep(s,
        "先在①選好平台，再點上面的「前往官網」註冊登入",
        "先在①選好大模型，再點上面的「前往官網」註冊登入",
        1, "① 第②步措辞与第①步对齐（zht）")

# ============================================================
# ② 版本号四处同步 + 更新日志
# ============================================================
s = rep(s, "var BUILD = 'v6.4.10'", "var BUILD = 'v6.4.11'", 1, "版本：BUILD")
s = rep(s, "    return 'v6.4.10';", "    return 'v6.4.11';", 1, "版本：报告兜底 RPT_BUILD")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.10 · AI设置新增配置指南，教新手一步步填好Key。">v6.4.10</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.11 · 配置指南改为泛指，任选大模型。">v6.4.11</div>',
        1, "版本：右下角角标（title + 文本）")
s = rep(s,
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.10</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>AI设置新增配置指南按钮。</p>\n'
        '      </div>',
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.11</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>配置指南不再指定平台，任选模型。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.10</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>AI设置新增配置指南按钮。</p>\n'
        '      </div>',
        1, "更新日志：插入 V6.4.11 首条")

# ============================================================
# 硬校验
# ============================================================
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
opens1 = len(re.findall(r"<script(?=[\s>/])", s))
assert closes1 == closes0, "[FAIL] 脚本收尾标签字面量数变了: %d -> %d" % (closes0, closes1)
assert opens1 == opens0, "[FAIL] 脚本开标签数变了: %d -> %d" % (opens0, opens1)
assert s.count("v6.4.10") == 0, "[FAIL] 小写 v6.4.10 残留: %d" % s.count("v6.4.10")
assert s.count("v6.4.11") == 3, "[FAIL] 小写 v6.4.11 应为 3 处，实际 %d" % s.count("v6.4.11")
assert s.count("V6.4.11") == 2, "[FAIL] 大写 V6.4.11 应为 2 处（更新日志 + 角标 title），实际 %d" % s.count("V6.4.11")
assert s.count("V6.4.10") == V6410_BEFORE - 1, \
    "[FAIL] V6.4.10 处数异常: %d -> %d" % (V6410_BEFORE, s.count("V6.4.10"))
# 指南文案：不再出现特定平台的推荐（★ 只看 aiCfg.g1 那一行 ——
# Provider 下拉里的 'aiCfg.optZhipu' 仍是「智谱 GLM ⭐ 推荐」，那是既有 UI，必须保留）
_g1 = re.search(r"'aiCfg\.g1':\s*\{.*?\},", s, re.S)
assert _g1, "[FAIL] 未能定位 aiCfg.g1 词条"
_g1txt = _g1.group(0)
assert "智谱" not in _g1txt and "智譜" not in _g1txt, \
    "[FAIL] 指南第①步仍指定了具体平台: %s" % _g1txt
assert "Zhipu" not in _g1txt, "[FAIL] EN 指南第①步仍指定了具体平台"
assert "换成你想用的 AI 大模型即可" in _g1txt and "to any AI model you want to use." in _g1txt, \
    "[FAIL] 泛指文案未落地"
assert "'aiCfg.optZhipu': {zh:'智谱 GLM ⭐ 推荐'" in s, \
    "[FAIL] Provider 下拉里的既有推荐项被误改"
LOG.append("OK  %-52s %s" % ("指南①泛指 / 下拉推荐项保留", "g1 不含任何具体平台；optZhipu 原样"))
# 更新日志字数
_log = re.search(r'<span class="log-ver">V6\.4\.11</span>.*?<p>(.*?)</p>', s, re.S)
assert _log, "[FAIL] 未能取到 V6.4.11 更新日志正文"
assert len(_log.group(1)) <= 20, "[FAIL] 更新日志 %d 字 > 20: %s" % (len(_log.group(1)), _log.group(1))
LOG.append("OK  %-52s %s" % ("更新日志字数", "%d 字：%s" % (len(_log.group(1)), _log.group(1))))

# ---- DOM 嵌套体检（硬门）----
import importlib.util
_spec = importlib.util.spec_from_file_location("v649s", os.path.join(BASE, "v649_structure.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_t = _mod.Tree()
_t.feed(s[:s.find('window.__S3D_LENS__')])
_bad = [(p, par) for p, par in _t.section_parents if par != ".wrap"]
assert len(_t.section_parents) == 12, "[FAIL] .panel 数量应为 12，实际 %d" % len(_t.section_parents)
assert not _bad, "[FAIL] 有面板掉出 .wrap：%s" % _bad
assert not _t.errors, "[FAIL] 未匹配收尾标签：%s" % _t.errors[:5]
LOG.append("OK  %-52s %s" % ("DOM 嵌套体检", "12 个面板父级均为 .wrap；未匹配收尾标签 0 个"))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 66)
print("脚本标签：opens %d -> %d, closes %d -> %d" % (opens0, opens1, closes0, closes1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
