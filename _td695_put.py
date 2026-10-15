# -*- coding: utf-8 -*-
"""V6.9.5 上传：读票据 JSON → 三道自检 → http.client PUT → 打印状态。
本机无 curl（§42），全程 http.client 精确控制请求头（§39）。"""
import json, re, sys, http.client, urllib.parse

tk = json.load(open(sys.argv[1], encoding="utf-8"))
t = tk["ticket"]
auth = t["headers"]["Authorization"]
tok = t["headers"]["x-cos-security-token"]

# ---- 三道自检（先于任何网络请求）----
assert len(tok) == 1024, "[FAIL] token 长度 %d != 1024" % len(tok)
assert auth.endswith("&q-url-param-list="), "[FAIL] Authorization 尾部被截断"
assert len(re.search(r"q-signature=([0-9a-f]+)", auth).group(1)) == 40, "[FAIL] signature 非 40 位"
listed = re.search(r"q-header-list=([^&]*)", auth).group(1).split(";")
assert listed == ["host", "x-cos-acl", "x-cos-storage-class"], "[FAIL] header-list %s" % listed
print("[自检] token=%d 签名40位 header-list=%s" % (len(tok), listed))

full = "https://" + t["domain"] + t["path"]
u = urllib.parse.urlparse(full)
# 只发签名清单里的头 + Authorization + 安全令牌（§39②）
hdrs = {k: v for k, v in t["headers"].items()
        if k.lower() in listed or k.lower() in ("authorization", "x-cos-security-token")}
data = open(tk["local"], "rb").read()
assert len(data) == tk["size"], "[FAIL] 实际字节 %d != 声明 %d" % (len(data), tk["size"])
hdrs["Content-Length"] = str(len(data))

conn = http.client.HTTPSConnection(u.netloc, timeout=900)
conn.request("PUT", u.path, body=data, headers=hdrs)
r = conn.getresponse()
r.read()
print("[PUT] %s  %s  %s -> %d" % (tk["local"], tk["size"], tk["file_name"], r.status))
sys.exit(0 if r.status == 200 else 1)
