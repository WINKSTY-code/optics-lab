# -*- coding: utf-8 -*-
"""V6.4.1 资产上传：Python urllib 直传（读取 upload 响应 JSON）"""
import json, os, sys, urllib.request

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"

def put(job):
    data = open(job["file"], "rb").read()
    req = urllib.request.Request("https://" + job["domain"] + job["path"], data=data, method="PUT")
    for k, v in job["headers"].items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=600) as r:
        print("PUT %-42s -> HTTP %s (%d B)" % (os.path.basename(job["file"]), r.status, len(data)))

if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1], encoding="utf-8"))
    for j in jobs:
        put(j)
