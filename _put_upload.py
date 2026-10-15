# -*- coding: utf-8 -*-
"""网盘上传辅助：读取 spec.json（url / headers / file），用 http.client PUT 上传。
本机无 curl，故用此脚本代替。
用法：python _put_upload.py spec.json
"""
import sys, json, os, http.client, urllib.parse

spec = json.load(open(sys.argv[1], encoding="utf-8"))
url, headers, path = spec["url"], spec["headers"], spec["file"]
assert os.path.isfile(path), "文件不存在: " + path
size = os.path.getsize(path)
hdrs = dict(headers)
hdrs["Content-Length"] = str(size)

u = urllib.parse.urlsplit(url)
target = u.path + (("?" + u.query) if u.query else "")
conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=600)
with open(path, "rb") as f:
    body = f.read()
conn.request("PUT", target, body=body, headers=hdrs)
r = conn.getresponse()
txt = r.read()
print("STATUS", r.status, r.reason, "bytes_sent=%d" % size)
if txt:
    print(txt[:500])
conn.close()
if r.status not in (200, 201, 204):
    sys.exit(1)
