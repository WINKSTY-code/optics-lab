# -*- coding: utf-8 -*-
"""V6.4.10 资产上传（修正版）

★ 踩坑记录：上传头必须**只带签名范围内**的那几个。
   Authorization 里 `q-header-list=host;x-cos-acl;x-cos-storage-class` ——
   这三个是参与签名的。第一版我漏了 `x-cos-storage-class`，
   又多带了 `Cache-Control` / `x-cos-crc32c-flag`（未签名），COS 直接 403 AccessDenied。
   正确头集合：Authorization + Content-Type + x-cos-acl + x-cos-storage-class + x-cos-security-token。
"""
import os, urllib.request

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"

JOBS = [
    {
        "file": os.path.join(BASE, "光学交互实验室_AI_v6.4.10.html"),
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl1abd96498538470400065bbc7118e3f2.html",
        "ctype": "text/html",
        "auth": "q-ak=AKID5sUcf8e8UaR3KX1h4chKjMqtzy7YwwEeYSTIWsNvAtlOzE8wAd82P4Tl1RDn4qiH&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789714769;1789721969&q-sign-algorithm=sha1&q-sign-time=1789714769;1789721969&q-signature=d428a999c40b4fcdd861c3061c4ff1ce860af4d2&q-url-param-list=",
        "token": "9N2AvNna2G7yF4vA8er503yOSRJrLMba69f623122594d577a3f56855e81b7942JvbMZSM63Mx76BxDcCnEVMYoZvXrjwHXu7rteYejisgG6qAdUslcoWwq4zHNovWJ2OM3ZeK7bshR7A4SiLfOspALcrvqIo8QnB2wvgyMSvPIXEW_RFy44HDeulmAINnHP-L-F_FWqf2nSnQCL8ftmKBA8bPAdtuH9ZJ079196w_v6jhWRZtVNwwBGcOmiwakTs2y8KloPjOLicoQHfXtQh55zRoeJdENemubDXO8l-jnc-BOA3-WQwUPcfEdBdYOxA-Io7LT67K_XX-3i0k06e-TQfOiKn620zZRmjIJx0qUW_zHriTJfJydGr0V2ZNFbecdYF-rxanWwQDVo12jIKl3M5AUz23iQsmC1r7CJd9rHD8BYMjZA3eXb5DcXnHptxxzeo9zJV7nte3oxgg8O4tBctOa1nAV19tZzJRmNGx5DJICZoK-qy8L1I6E1speoNmvXM_r5nd0t7Ucf5-0qnGEu7jjIGwK71hBLwEo5lRa_jdkmtty4MYC4W9Yj30uIgio6JR2DToeLXMQ23I3BcjP9lru101lx2FRDDfKqgr5mjwSQNTomwzABJjk8ZuurJLjkak2vUGeqEK8oEbL-6m4AZZJ_2rezknoLO6-CRgBOezILZxjUl__Dl-UbAMKK3fkvJ4DWSq9B2YAT3GBwQgSpn9fYH66c9kPbwejmMyu-WUbUob_c62NOOS_XedBgblmXRHJOiIn1N5PYiO31jmZbGl7xFQTrJ_ryxM9AL8qTr7P-oUhqcKkOryZ3QneRqDiIJfQFWWwq-1Tdbobz_o0M4la9ZeE2-mQ3ZrpjdnSZjTf8ewFit_KsZMkx7tWmNVf7p9VXPsq5QwjZEbp9YNr0vZBRhCXXmQZXw3El3SsbLYeF7XrtMPtiGQ8SacqWkNdae4pB3_J7QGqgGwOcwenMWmDCIUZBxj4iEyCX1YuTGid3ByC0Mm5ypyN3DkO",
    },
]


def put(job):
    data = open(job["file"], "rb").read()
    req = urllib.request.Request("https://" + DOMAIN + job["path"], data=data, method="PUT")
    req.add_header("Authorization", job["auth"])
    req.add_header("Content-Type", job["ctype"])
    req.add_header("x-cos-acl", "default")
    req.add_header("x-cos-storage-class", "INTELLIGENT_TIERING")
    req.add_header("x-cos-security-token", job["token"])
    with urllib.request.urlopen(req, timeout=600) as r:
        print("PUT %-42s -> HTTP %s (%d B)" % (os.path.basename(job["file"]), r.status, len(data)))


for j in JOBS:
    put(j)
