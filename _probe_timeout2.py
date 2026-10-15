# -*- coding: utf-8 -*-
"""第二轮：定位可行的修复路径。
1) glm-5.3-flash + thinking:disabled —— 强制思考模型能否被关掉？关掉后多快？
2) glm-5.3-flash 流式 —— 首字(TTFT)多久？（决定"改流式渲染"是否可行）
3) GLM-5.3-FlashX / GLM-4.7-Flash —— 换模型是否够快？
"""
import json, time, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

KEY = open(r"C:\Users\Administrator\.workbuddy\secrets\glm_api_key.txt", encoding='utf-8').read().strip()
URL = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

SYS = "你是初中物理光学 AI 错题诊断老师，严格基于苏科版2024新教材。\n【回答语言】简体中文"
PROMPT = ("学生【凸透镜成像】实验的学情画像：\n总操作 42 次，会话 6 分钟\n"
          "- 凸透镜成像：120 秒，操作 18 次\n- 平面镜成像：60 秒，操作 9 次\n"
          "- 错误 物距像距判断：3 次\n- 错误 光屏位置：1 次\n"
          "\n请输出：\n1) 知识掌握度（强项/弱项）\n2) 典型错因推测（≤3 条）\n"
          "3) 下一步学习建议\n4) 1 道针对性练习题（含答案解析）。")

def body_of(model, max_tokens, stream=False, think=None):
    o = {"model": model, "messages": [{"role": "system", "content": SYS},
                                      {"role": "user", "content": PROMPT}],
         "temperature": 0.5, "max_tokens": max_tokens}
    if think is not None:
        o["thinking"] = {"type": think}
    if stream:
        o["stream"] = True
    return json.dumps(o, ensure_ascii=False).encode('utf-8')

def post(body, timeout=300):
    req = urllib.request.Request(URL, data=body, method='POST')
    req.add_header("Authorization", "Bearer " + KEY)
    req.add_header("Content-Type", "application/json")
    return urllib.request.urlopen(req, timeout=timeout)

def run(tag, model, max_tokens=32000, stream=False, think=None):
    print("=" * 72)
    print(f"[{tag}] model={model} max_tokens={max_tokens} stream={stream} thinking={think}")
    t0 = time.time()
    try:
        resp = post(body_of(model, max_tokens, stream, think))
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code} 用时 {time.time()-t0:.1f}s :: {e.read().decode('utf-8','replace')[:300]}")
        return
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e} 用时 {time.time()-t0:.1f}s")
        return

    if not stream:
        d = json.loads(resp.read().decode('utf-8'))
        total = time.time() - t0
        u = d.get("usage", {}) or {}
        ch = (d.get("choices") or [{}])[0]
        msg = ch.get("message", {}) or {}
        rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        print(f"  ✅ 总耗时 {total:.1f}s | finish={ch.get('finish_reason')} | "
              f"思考token={rt} 补全token={u.get('completion_tokens')}")
        print(f"     正文 {len(msg.get('content') or '')} 字 / 思考 {len(msg.get('reasoning_content') or '')} 字")
    else:
        ttft = first_content = None
        rlen = clen = 0
        for line in resp:
            line = line.decode('utf-8', 'replace').strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                ev = json.loads(data)
            except Exception:
                continue
            for c in (ev.get("choices") or []):
                dl = c.get("delta") or {}
                if dl.get("reasoning_content"):
                    if ttft is None:
                        ttft = time.time() - t0
                    rlen += len(dl["reasoning_content"])
                if dl.get("content"):
                    if first_content is None:
                        first_content = time.time() - t0
                    clen += len(dl["content"])
        total = time.time() - t0
        print(f"  ✅ 流式总耗时 {total:.1f}s")
        print(f"     首个思考块 {None if ttft is None else round(ttft,1)}s | 首个正文块 "
              f"{None if first_content is None else round(first_content,1)}s")
        print(f"     思考 {rlen} 字 / 正文 {clen} 字")

print("### 第二轮：修复路径定位（套餐端点 coding/paas/v4）")
print(f"时间 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
run("1 GLM-5.3-Flash 关思考(thinking:disabled)", "GLM-5.3-Flash", think="disabled")
run("2 GLM-5.3-Flash 不传 thinking 字段",        "GLM-5.3-Flash", think=None)
run("3 GLM-5.3-Flash 流式",                      "GLM-5.3-Flash", stream=True, think="enabled")
run("4 GLM-5.3-FlashX (界面标'超高速')",          "GLM-5.3-FlashX", think="enabled")
run("5 GLM-4.7-Flash (界面标'免费')",             "GLM-4.7-Flash", think="enabled")
