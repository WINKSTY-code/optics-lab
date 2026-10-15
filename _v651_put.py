# -*- coding: utf-8 -*-
"""V6.5.1 网盘上传：票据落盘 + PUT（本机无 curl，全程 http.client）

三张票据分两批，x-cos-security-token 各批逐字相同，故每批只精确抄录一次。
自带校验：Authorization 结尾完整（&q-url-param-list=）/ token 长度 1024 / 签名 40 位十六进制。
"""
import http.client
import json
import os
import re
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"

# ---- 批次 A（file_upload 第一批，3 张共用同一 token）----
TOK_A = ("iBDLCckaiAXheyt1h1R250hXis34MG7aa15f0cf180caaf68d2a2ec62bedc86c3TTTbj0RIK1xIestYmOwnXNEshlsgXmzPyzU3O"
         "JXxR8GkR1szZhVgfFnVu_cnlQ90TuoEHE4j6SK2zUeJiExxlZZY2S63zJYgw4n5QqTlNsH1a_phLHi2oW3c_CiUCTeDWcU5u5b6vt"
         "b5hC_qp9rfv6rpmB_O7q3S0ceajc7fkUSH2-uHV2xVhe7Kl6qczqj8RXM-6UBtZ25_bjTVg_mICL5BzmRZVeR0GBHfp71QHCuwehL"
         "yTt3uA7Do5GqqI-eKd324G2u0UZ86pq8dC7Wpf9_I7VieE3enoecw3C54AeavtQ0q5gfdxpjseerzeI69HqRSoKd0DcETAVCgGKzAx"
         "dV0I3K3bIDT1Dlr-jPnS2kKRwJeEaVtSv6AVq0sHjZk7HC4xnHQtb8WKa7i5qLv6TNEVJtCL_6oAlpabmsZnt_Lh4SQAm-TdRf9hL"
         "JcuT7n8fwpboBdjtjLb3zi_cEMZEkZuA2qb9g7EsFZpGO0EenVUD77ghhT9q-9gc_d21u-dRDa7luYAyT1ZMLl_S2dHZIrG3f7OIN"
         "omdENcaPGrOiYOBhNfQgbwy4G6yrO-xFE_0Qkb0Nl6qTh1I9-OfoiBNJ5WGhGXs0yEx6QdS7m4Gu4aCce-lRNhCe13rGji-OrO1ruZ"
         "9AEA0QpPrjSk91yZVguRotT0q58IKO7nTtNNUj4vNM2uh9CmEwZCbnhRoYmiZJVvetNgp7JDR643CLq-gjfokhFMkVQE4Mg3XIiNh"
         "aXn85Y7F1_Otsk7zQE9Z_PdQm62jsWey09l2vOyJ7bVRUWF_-DCtHkCmtbE5QeSLU7wFKN126xNvvps-2j9E12kW74oWxNWkrpRm"
         "iV9OFtEQOWiutIv8R_1kz_lbpTz-BruQpSOmiA1r46tOVrwSJmHli-Orasyrtz2R0Pw9les-mqoZ3Pcf7yp47vtSUoy1A8Yk4WCS"
         "Jl8tHi9u-kw-AL")
AUTH_A = ("q-ak=AKID_Go7sel5nEM8BTTx_tuQGCvWRr48rOy3ALh6ApjFmTdZUnf3D13PRLlTvD3HWLtn"
          "&q-header-list=host;x-cos-acl;x-cos-storage-class"
          "&q-key-time=1790145751;1790152951"
          "&q-sign-algorithm=sha1"
          "&q-sign-time=1790145751;1790152951"
          "&q-signature=%s"
          "&q-url-param-list=")

# ---- 批次 B（合成证据图，另一次 file_upload，token 与批次 A 不同）----
TOK_B = ("iBDLCckaiAXheyt1h1R250hXis34MG7afc60035e4ae6eaea005d0e948a0b3e99TTTbj0RIK1xIestYmOwnXLI2AUL4lq7_AxX-py1"
         "EbnmBKIJR6S4ERiw51Hyg8mZovdqRHICuRYt-AI_B_vYC0FC5yd57ubBWTt1Lgzbuoc5O5O9hRoCdRDGhCNhRG3jzLn3ha718ivvMkQ"
         "qQkAC4C7G4yG7tt62mwzEYKhiEiZJYkT3lhrOOgjl1tddMYoY6gdAZzDtYaceMBUoIbDWpJdvKnsVPHIFh4DIVMK6ArUTUalUYrt7p8"
         "ya2tT4StX0ynh_3X9UwSSPI46M3li2pmXfuG0NwKIDC9mtVdSvbfUJfJRKFCIyb29azgl28BQlfXB4O3pNDwbI0w3GsILE3oA2EMFn"
         "-79yRhTqcBLaZM2Iqxyzwygs8SrbxzRkCET_EsjogzIlA93Y9hOK0vj3z3NzWUYNq5o3zkod8J9C1ovqj-x1EnKBgdpbYkf0BS1sYy"
         "MnJ6SFcDl-cZSOU2IDEIU8KedjV4Vk6MHqgqF12_cuZexU9iJOF0ISbVKEt6fqehycyjyhCA-RPVpoQDrmO4iCGNzZB4zCdPPQHkEF"
         "cCVNC56OB3P90c-L7VbXK-99gXVgN-PUowvH9tCZaXAiu6ivjIgE9Yavsj74TUVUhSUeYCnp2OkZNEXnCL2wxe6GV7Lj0s_-2Vrrk"
         "RpMtS8lP6cxHwcvyFRyRViSsCKnIycmULuk-XDIS9oppmlo0JZg1VzfsB5JkC4cDBSLX_BstnUsHhiAhPCwx5Gd8D07WlHsR2eM7b"
         "Jz-e0EvO1UwgPz9nx6fMHYttsynl8Oc3yEsW29UYxbsLQ7KMIbeZLKKFfSHguJwBoFrs_-o-gk566n5ib8DDij8q3yE9cfL_HUfc_"
         "EZ2LSsqeisrFFqwIAFd4-mXG_AR0OCYOJghNes5mUyR9hErnTy7ons1qEXYFqkHSj3nF8git_S14UMQ_AD9TGlbLIzFkfDwe7xa9vx6jIY")
AUTH_B = ("q-ak=AKIDiNGhpULiy1DPYUriousll5a8NfR_Q65qkWTr2gQDCh5VMjIiIiobaCGbt92KImg_"
          "&q-header-list=host;x-cos-acl;x-cos-storage-class"
          "&q-key-time=1790145809;1790153009"
          "&q-sign-algorithm=sha1"
          "&q-sign-time=1790145809;1790153009"
          "&q-signature=%s"
          "&q-url-param-list=")

P = "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl"
JOBS = [
    {"local": "光学交体实验室_placeholder", "name": None},   # 占位，下面按真实名重建
]
JOBS = [
    {"local": "光学交互实验室_AI_v6.5.1.html", "ct": "text/html", "batch": "A",
     "path": P + "46d8576a9727e21500065c20c9974177.html",
     "confirm_key": "46d8576a9727e21500065c20c9974177",
     "task_id": "drivetask_726a26014bf445eeafce87c70328513a",
     "sig": "ecd191578396b4a94e3d87bde7cd0d90a5ee5b89"},
    {"local": "工作记录V6.5.1.md", "ct": "text/markdown", "batch": "A",
     "path": P + "d0a649d0ab1fb54800065c20c9989e30.md",
     "confirm_key": "d0a649d0ab1fb54800065c20c9989e30",
     "task_id": "drivetask_3d0bebeeb1724879be3d64e6cfc0eeae",
     "sig": "a663ac91a2c60471a853410bb668404a88dc2491"},
    {"local": "自检_AI设置新增模型与更新日志_V651.png", "ct": "image/png", "batch": "B",
     "path": P + "071c7050e4c4e43c00065c20cd0d6990.png",
     "confirm_key": "071c7050e4c4e43c00065c20cd0d6990",
     "task_id": "drivetask_0355e88f14884439addb0063f4daf39d",
     "sig": "f012f3cee2860f462377d7f1c70ba4765175d06b"},
]

# ---------------------------------------------------------------- 票据自检
assert len(TOK_A) == 1024, "[FAIL] 批次 A token 长度 %d ≠ 1024" % len(TOK_A)
assert len(TOK_B) == 1024, "[FAIL] 批次 B token 长度 %d ≠ 1024" % len(TOK_B)
for j in JOBS:
    a = (AUTH_A if j["batch"] == "A" else AUTH_B) % j["sig"]
    assert a.endswith("&q-url-param-list="), "[FAIL] %s Authorization 尾部被截断" % j["local"]
    assert len(re.search(r"q-signature=([0-9a-f]+)", a).group(1)) == 40, "[FAIL] %s 签名长度异常" % j["local"]
print("票据自检 OK：两批 token 各 1024 字符，Authorization 尾部完整，签名各 40 位")

allow = {"host", "x-cos-acl", "x-cos-storage-class", "authorization", "x-cos-security-token"}
ok = []
for j in JOBS:
    hdrs = {
        "Authorization": (AUTH_A if j["batch"] == "A" else AUTH_B) % j["sig"],
        "Content-Type": j["ct"],
        "x-cos-acl": "default",
        "x-cos-storage-class": "INTELLIGENT_TIERING",
        "x-cos-security-token": TOK_A if j["batch"] == "A" else TOK_B,
    }
    t = {"url": "https://" + DOMAIN + j["path"], "domain": DOMAIN, "path": j["path"],
         "confirm_key": j["confirm_key"], "task_id": j["task_id"], "headers": hdrs}
    tkf = os.path.join(BASE, "_tk_651_%s.json" % re.sub(r"[^0-9A-Za-z._-]", "_", j["local"]))
    json.dump(t, open(tkf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    local = os.path.join(BASE, j["local"])
    data = open(local, "rb").read()
    assert len(data) == os.path.getsize(local)
    send = {k: v for k, v in hdrs.items() if k.lower() in allow}
    u = urllib.parse.urlparse(t["url"])
    conn = http.client.HTTPSConnection(u.netloc, timeout=900)
    conn.request("PUT", u.path, body=data, headers=send)
    r = conn.getresponse()
    body = r.read()[:300].decode("utf-8", "replace")
    print("PUT %-46s %8d B -> HTTP %d %s" % (j["local"], len(data), r.status, body))
    if r.status != 200:
        raise SystemExit("[FAIL] PUT 失败：%s" % j["local"])
    ok.append((j["local"], len(data), j["confirm_key"], j["task_id"]))

print("\n全部 PUT 成功，接下来逐个调 file_upload_complete：")
for n, sz, ck_, td in ok:
    print("  %s | %d B | confirm_key=%s | task_id=%s" % (n, sz, ck_, td))
