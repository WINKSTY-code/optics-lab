# -*- coding: utf-8 -*-
"""网盘文件下载 / 上传工具（Windows 无 curl，全程用 http.client / urllib）

用法：
  python _tdrive.py down <url_file> <out_path>
  python _tdrive.py up   <ticket_json> <local_path>
ticket_json 是 file_upload 返回的完整 JSON（含 url / headers / confirm_key / task_id）
"""
import sys, json, http.client, urllib.request, urllib.parse, re, os

MODE = sys.argv[1]

if MODE == "down":
    url = open(sys.argv[2], encoding="utf-8").read().strip()
    out = sys.argv[3]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(out, "wb") as f:
        f.write(r.read())
    print("downloaded", out, os.path.getsize(out), "B")

elif MODE == "up":
    t = json.load(open(sys.argv[2], encoding="utf-8"))
    local = sys.argv[3]
    data = open(local, "rb").read()
    # 票据给的是 domain + path，不是完整 url
    full = t.get("url") or ("https://" + t["domain"] + t["path"])
    u = urllib.parse.urlparse(full)
    # 只发 q-header-list 里列出的头 + Authorization + 安全令牌（§39）
    hl = re.search(r"q-header-list=([^&]*)", t["headers"].get("Authorization", "")).group(1)
    allow = set(hl.split(";")) | {"authorization", "x-cos-security-token"}
    hdrs = {k: v for k, v in t["headers"].items() if k.lower() in allow}
    print("发送请求头:", sorted(hdrs.keys()))
    conn = http.client.HTTPSConnection(u.netloc, timeout=900)
    conn.request("PUT", u.path + ("?" + u.query if u.query else ""), body=data, headers=hdrs)
    resp = conn.getresponse()
    body = resp.read()[:400]
    print("PUT", resp.status, body)
    assert resp.status == 200, "上传失败 %s" % resp.status
    print("confirm_key=", t.get("confirm_key"), "task_id=", t.get("task_id"))
