# -*- coding: utf-8 -*-
"""通用网盘 PUT 上传（本机 Git Bash 无 curl，改用 urllib）"""
import sys, json, urllib.request
local_path, domain, path, headers_json = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
headers = json.loads(headers_json)
url = "https://" + domain + path
with open(local_path, "rb") as f:
    data = f.read()
req = urllib.request.Request(url, data=data, method="PUT")
for k, v in headers.items():
    req.add_header(k, v)
try:
    with urllib.request.urlopen(req, timeout=180) as r:
        print("HTTP", r.status, "bytes=", len(data))
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.read()[:300]); sys.exit(1)
