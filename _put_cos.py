# -*- coding: utf-8 -*-
"""用 http.client 精确控制请求头（不额外添加 urllib 自带头），完成 COS PUT 上传。"""
import json, http.client, urllib.parse, os, sys

t = json.load(open('_tk.json', encoding='utf-8'))
u = urllib.parse.urlparse(t['url'])
path = u.path

local = sys.argv[1] if len(sys.argv) > 1 else '光学交互实验室_AI_v6.4.18.html'
data = open(local, 'rb').read()

# 只发签名覆盖的头 + Content-Length（CORS 签名忽略 content-length）
hdrs = {}
for k, v in t['headers'].items():
    if k.lower() == 'cache-control':
        continue          # 不在 q-header-list 中，别发
    hdrs[k] = v
hdrs['Content-Length'] = str(len(data))

conn = http.client.HTTPSConnection(u.netloc, timeout=600)
conn.request('PUT', path, body=data, headers=hdrs)
r = conn.getresponse()
body = r.read()
print('STATUS', r.status)
if r.status in (200, 204):
    print('UPLOADED OK  %s  %d B  ETag=%s' % (local, len(data), r.getheader('ETag')))
else:
    print(body[:600].decode('utf-8', 'replace'))
conn.close()
