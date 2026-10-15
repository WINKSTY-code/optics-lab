# -*- coding: utf-8 -*-
"""实测 glm-5.3-flash 诊断请求的真实耗时。
复刻课件 callLLM 的请求体：非流式 + thinking:{type:'enabled'} + max_tokens 分档值。
用 socket 超时 300s，看它到底要多久才回来（远超 45s 也照等，才能知道真实数字）。
"""
import json, time, sys, socket, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

KEY = open(r"C:\Users\Administrator\.workbuddy\secrets\glm_api_key.txt", encoding='utf-8').read().strip()
MODEL = "GLM-5.3-Flash"

SYS = ("你是初中物理光学 AI 错题诊断老师，严格基于苏科版2024新教材。\n【回答语言】简体中文")
PROMPT = ("学生【凸透镜成像】实验的学情画像：\n"
          "总操作 42 次，会话 6 分钟\n"
          "- 凸透镜成像：120 秒，操作 18 次\n"
          "- 平面镜成像：60 秒，操作 9 次\n"
          "- 错误 物距像距判断：3 次\n"
          "- 错误 光屏位置：1 次\n"
          "\n请输出：\n1) 知识掌握度（强项/弱项）\n2) 典型错因推测（≤3 条）\n"
          "3) 下一步学习建议\n4) 1 道针对性练习题（含答案解析）。")

def build(max_tokens, stream, think=True):
    o = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": PROMPT}],
        "temperature": 0.5,
        "max_tokens": max_tokens,
    }
    if think:
        o["thinking"] = {"type": "enabled"}
    if stream:
        o["stream"] = True
    return json.dumps(o, ensure_ascii=False).encode('utf-8')

def post(url, body, timeout=300):
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header("Authorization", "Bearer " + KEY)
    req.add_header("Content-Type", "application/json")
    return urllib.request.urlopen(req, timeout=timeout)

def run(tag, url, max_tokens, stream, think=True):
    print("=" * 72)
    print(f"[{tag}] url={url}  max_tokens={max_tokens}  stream={stream}  thinking={think}")
    body = build(max_tokens, stream, think)
    t0 = time.time()
    try:
        resp = post(url, body)
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        print(f"  ❌ HTTP {e.code}  用时 {dt:.1f}s")
        print("  " + (e.read().decode('utf-8', 'replace')[:400]))
        return
    except Exception as e:
        print(f"  ❌ 异常 {type(e).__name__}: {e}  用时 {time.time()-t0:.1f}s")
        return

    if not stream:
        raw = resp.read()
        total = time.time() - t0
        d = json.loads(raw.decode('utf-8'))
        u = d.get("usage", {}) or {}
        ch = (d.get("choices") or [{}])[0]
        msg = ch.get("message", {}) or {}
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""
        print(f"  ✅ HTTP {resp.status}  总耗时 {total:.1f}s")
        print(f"  finish_reason = {ch.get('finish_reason')}")
        print(f"  usage = {json.dumps(u, ensure_ascii=False)}")
        print(f"  正文长度 = {len(content)} 字 | 思考长度 = {len(reasoning)} 字")
        rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
        if rt is not None:
            print(f"  ⚠️ 思考 token = {rt} / 补全 token = {u.get('completion_tokens')}")
        print(f"  正文前 120 字：{content[:120]!r}")
    else:
        ttft = None
        reasoning_tokens = None
        content_parts, reasoning_parts = [], []
        for line in resp:
            if not line:
                continue
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
            u = ev.get("usage") or {}
            if u:
                reasoning_tokens = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", reasoning_tokens)
            for c in (ev.get("choices") or []):
                delta = c.get("delta") or {}
                if delta.get("reasoning_content"):
                    if ttft is None:
                        ttft = time.time() - t0
                    reasoning_parts.append(delta["reasoning_content"])
                if delta.get("content"):
                    if ttft is None:
                        ttft = time.time() - t0
                    content_parts.append(delta["content"])
        total = time.time() - t0
        print(f"  ✅ 流式结束  总耗时 {total:.1f}s | 首字(TTFT) {ttft if ttft is None else round(ttft,1)}s")
        print(f"  思考长度 = {sum(len(x) for x in reasoning_parts)} 字 | 正文长度 = {sum(len(x) for x in content_parts)} 字")
        if reasoning_tokens is not None:
            print(f"  ⚠️ 思考 token = {reasoning_tokens}")

print("### 实测 glm-5.3-flash（复刻课件 callLLM 请求体）")
print(f"当前时间 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

PAAS = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
CODING = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

run("A 课件现状(按量端点·非流式·32000)", PAAS, 32000, False)
run("B 同A但流式(看首字延迟)",            PAAS, 32000, True)
run("C 套餐端点(非流式·32000)",           CODING, 32000, False)
run("D 旧额度(非流式·8000)",              PAAS, 8000, False)
