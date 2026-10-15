# -*- coding: utf-8 -*-
"""网盘 PUT 上传：_tdrive_put.py <ticket.json> <local_file>

只用 q-header-list 里列出的头 + Authorization + x-cos-security-token。
（本机没有 curl，一律走 http.client；urllib 会自作主张加头，不用。）
"""
import http.client
import json
import os
import re
import sys
import urllib.parse


def main():
    tk_path, local = sys.argv[1], sys.argv[2]
    t = json.load(open(tk_path, encoding="utf-8"))
    full = t.get("url") or ("https://" + t["domain"] + t["path"])
    u = urllib.parse.urlparse(full)
    hdrs = dict(t["headers"])
    auth = hdrs.get("Authorization", "")
    allow = set(x.strip().lower() for x in re.search(r"q-header-list=([^&]*)", auth).group(1).split(";") if x.strip())
    allow |= {"authorization", "x-cos-security-token"}
    send = {k: v for k, v in hdrs.items() if k.lower() in allow}
    data = open(local, "rb").read()
    print("PUT %s  (%d B, 磁盘 %d B)" % (u.netloc + u.path[:40] + "...", len(data), os.path.getsize(local)))
    print("发送头: %s" % sorted(send.keys()))
    conn = http.client.HTTPSConnection(u.netloc, timeout=600)
    conn.request("PUT", u.path, body=data, headers=send)
    r = conn.getresponse()
    body = r.read()[:400]
    print("HTTP %d  %s" % (r.status, body.decode("utf-8", "replace")))
    assert r.status == 200, "PUT 失败"
    print("OK")


if __name__ == "__main__":
    main()
