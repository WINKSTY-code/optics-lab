# -*- coding: utf-8 -*-
"""V6.5.2 三份产物上传项目资产（网盘目录「光学实验室」）
票号来源：file_upload 三次调用（本批 token 各自不同，逐个抄录）。
裸请求头只发 q-header-list 列出的 host;x-cos-acl;x-cos-storage-class + Authorization + x-cos-security-token。
"""
import json, os, re, http.client

BASE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"
TOK_HTML = "XUrimLCFGbZi5IpywQbmXHpeqytcJEXa1e877c9e90dfb93bd35ce984f540b9ffAyM3x4ARb9Isbozi4k8DvnVs6YoATKpiDwE9UqNk1sbp81kvkOCMxNRAclxUqno12UOZ6ih_af2XoypK9fvTntmtpW_qXZyMxC677vVivI9-k8JZU9yMr9krWlS4C2xRWgWLLFBc8UQrrm4IPMWEdLN2pL-arezS7qiAzrrSid67QjXqFxAAnuZALE19DDYBZSigHSu9x0j5pbmGLkGIbY6XDaspK8NhEbpnhMN_0usMTDNttj0MUReJb8ZeqDnbMBqZA2IqsuwtFJdFOKi1LMqTv3-Q3YgCUWjpBgCFnl0pV5Bs9DKi8eIjqsan3npXULRhw_sOKkYhxdgXEK0IKWisygsnTxEhya69kGg3s7L9QrgcFDl4QjB72rD1gyrML0Ae_QjFsCSMTC5S42ktavY_NhzvZUt7uED4zgLzYoyjXmzxZP4GT_TKvm1HXWCJ_wWh6H67HE-06FcdpACg8gP2If1VeVCg4D7POMkjicdeVfWaeYOGUpslYxGQq3_SXNVQqisPfiGQWYdsPHAc7G-TXzpZZfzI-Kow_4-WCNgSevApgcVtfq38cj2kX9moiZWFgZKQnu8KfYHMZQGz3KTi3HzsEG2TaMORF2uaIQZWseGc33E56Hk4MkrK_mQeC_QuaFnTNziobIBJIjuiRHmr8yoCGV6Ii8huAb30nb5D2TIjSgkEqhmbWN5dP8lW8c37ln-41D7mqxiiBBa_Nk6KnAaKPLSe9E60FlI2bOA8vGsePvvLp3Gu2oxhMTIDPA1MQcQOEA9VN0O17fauXLWEPrAeKXFbemQgkdDWo-4ep76QruRpbcfAECvcMUVUMunwTyqCxyVwydvD7wlQ6Be3IrCrnyYjfuw7v2WNAcBXu-AwI5YEE3VX9xNWJxB5qFcTr2SGVn9l9fxc0gpxz4g0nJ19m_WR0nfsbED5CDekK5SJpfQ7f2_howtqJQH1"
TOK_MD = "XUrimLCFGbZi5IpywQbmXHpeqytcJEXa3c7d72a1339b0e9828f9a06d80964348AyM3x4ARb9Isbozi4k8Dvg45nO4tTHLpHtR10I0MQnY3OrXQm26uo8U43meXXOda6Z79j9ljM6PofnfLEQrFv0F1MvPBWbR1RCpnggO6hBRw4SxwaGVH-JBZfZkXdPrP4AUgu6ctyyUzYXJu6RgfAai7SSW023kmcPbC4E5GWNhGXo-vM9HX7frVekeRGZzDYqLgu1W0e5YBChYdxeLoQr9mTiJpJm6HAgdb0H0Jk4Z3Dp2twNAqN4MoqckGyHA5G_X8n1DqBEQpUoYCNJJXclgsZgM7zzYJT0xmwzgUotDHUAuLG5cBS4CO2-36bS1yA-LeCEoFC7mKm4CZ2XtcbkhqodC5lOsD0J-rNPLRc_uPRMm9xOSebv_7g8001JwA-jZbN0_fz6kP-NT_mtuo-fzVajp1dXgMqM6bRcmnOka0OfELGXC7R3vzSLd4-qY7uY0IlkyWoBuGrPLe68A6yMG9KLKXM4uGdScPrlKMxXo0-Nh81_zCUFb37PvzUWmygm80Dr80HErjZEZ_s-JvSKOJTG1Q-TM5MPv6kTHgWS6u3Pq27naRNm6d4IsDBMf1C4cWhSweqiSja1E5ddg1U1oQ6VlK_BGcPGmJRGksGQXetueMG2bbTAcXrVMSQQzqFZTcghh6izEbXOr10thCe07lDPWTegdRg7DqRuFaTreexo9odMDVdRx-goi6tVOnCYDsBzUTv355ed_ycy2HAPUHpujSuHP6GMXQi67eXjKiNG5qGbd1vV9aUghiLydRwzGUeo9GT9B-FOo6KqZ04iZFidaWCCsqmtF6JnTKBeA3MEnqtSJ5lYklabC8klWmbZ0tCJBDXAvDufCEeJ_jSnsg1trHRMIJwjogrBzIXVRzrG2_cTiDtpvn0godZ-F1W11ELLIiSseC9oUq-HJ2dxcYYqB6vR6gFVKApzh3wAuY-icu2sQ_W-HKfPwB1jmT"
TOK_PNG = "XUrimLCFGbZi5IpywQbmXHpeqytcJEXa42e10c736d18e5fed32372efddbc30dbAyM3x4ARb9Isbozi4k8Dvtu3N6uctgs9BKAr76pIEscq3KsQ7NAiV9Zs39gFzxHSLKt0Zrh9lMxBQw50_yS64n16hgQVhDBUhAcEvEahgXkvR07DNcQkJz02hs-slqT597lCCqvcwLvaWfQfaMRY9svGfuWM9WUJSsH6AnFai0UyOOjw4SBmCbotuNqTk1X3QHxrF80W0qqtfuEnho2qJkT65pKw4_CKT98WgFebgK-buEFoOl8j227Ic89ZJTFWrrs1FJo5C1R3vAU7FG1CLowCFQa5msDy45gKjrEXoDywRquaJ07ZChC1sb9Q9TkEgCTQiw6nPwYDWHkFsp2m1Y8xQRChqlm2VqW2ly2X9Eea6ice75XpBfarmhdeqrnqxfXyAbm7NIzKP3_gUL06Pxlnxr_hNvcEtUYf4eqIRoxJTdSq4tjsV3mmA3G4rQ15yjXFPGyA1E8Y83EIvPoDH2UYloyACloRQZ1CDglYBOCnvaesueOFNgO65GUGKIrQ34VzB0D3tKsqPq1XfSeCtOgaXd7Bo6pnND-lmyx9x2tGVacmTLiCWFGhb3uroDtdg2TvXeBU2Bysp7NL9DTWbPGLsVF66EbrzZ2QG-MeGh0-jNj3PFAL4AGTLBeV0rVAimvFbeLSlVOhchiKYGml2107P3wQTde58-YIQ3cIPQxRo0QHEMO5FNkoK-gQruGHw4Iv6DO2fToLg6l92TWrV9H1Y2Ewm1vghJNS2F6xUrHzptDEtL_OLVjK8_IzgJfvsvT1VrmZdjoxMp0Pl6SF53jKRzd9QfghHm6TeVTdlizu1O9Zw6f2dDVxoP5yDEw5SCGy-_z6i9TLaRIweYhWb8gyPHH8fvxFzw1G8_oU1rSsIxaOobVDgAtblPfu6M7rn55oQyjSe7vvvJhWWXkdY6dsGjBt-ICMMgFV13rBjI_nIw8e9uYCpKJUWMUcxUb1"

JOBS = [
    {
        "local": os.path.join(BASE, "光学交互实验室_AI_v6.5.2.html"),
        "auth": "q-ak=AKIDCV0890FnJRgdalKPzDaS9c4zwz3qQHCzKzaE8065uYvVyV7foX3KrYwgb9gNV7JG&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1790640540;1790647740&q-sign-algorithm=sha1&q-sign-time=1790640540;1790647740&q-signature=2788fa5f20c2695551ca0656013cb177c8670af3&q-url-param-list=",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl9bdb06bdba2c20fd00065c93fd544259.html",
        "tok": TOK_HTML,
        "confirm_key": "9bdb06bdba2c20fd00065c93fd544259",
        "task_id": "drivetask_f334f4dabac241c3b9646e7c93b531af",
        "name": "光学交互实验室_AI_v6.5.2.html",
    },
    {
        "local": os.path.join(BASE, "工作记录V6.5.2.md"),
        "auth": "q-ak=AKIDY5cX8SF1GwfWeuPSBM9lXizhiEOWGL1ubyNMXQDtn542tT118d-HhY8cGgf-HSl9&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1790640550;1790647750&q-sign-algorithm=sha1&q-sign-time=1790640550;1790647750&q-signature=aced52b78cb6db77f970ddae2eafe776ccd40352&q-url-param-list=",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYld9d06a9dc6405de800065c93fdf094d4.md",
        "tok": TOK_MD,
        "confirm_key": "d9d06a9dc6405de800065c93fdf094d4",
        "task_id": "drivetask_28c8daa3486e47cd882ec0a5b9bef507",
        "name": "工作记录V6.5.2.md",
    },
    {
        "local": os.path.join(BASE, "_chk652", "自检_V652_模型与更新日志.png"),
        "auth": "q-ak=AKIDh1n5WckTHIp7uE8Sh-_NnTkaXjwCllymVY6fpnFhL9gx1UbdPkDSjr9-qcAACAcc&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1790640550;1790647750&q-sign-algorithm=sha1&q-sign-time=1790640550;1790647750&q-signature=c2461e82587aac72e075972d7d22df953849b675&q-url-param-list=",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYlca58a7e2bbfb237300065c93fdf0a206.png",
        "tok": TOK_PNG,
        "confirm_key": "ca58a7e2bbfb237300065c93fdf0a206",
        "task_id": "drivetask_558218df0e6044d6b12c10bbd2699c0b",
        "name": "自检_V652_模型与更新日志.png",
    },
]

def headers_of(job, size):
    h = job["auth"]
    # 三道自检（§59⑥）
    assert len(job["tok"]) == 1024, "[FAIL] %s token 长度 %d != 1024" % (job["name"], len(job["tok"]))
    assert h.endswith("&q-url-param-list="), "[FAIL] %s Authorization 尾部被截断" % job["name"]
    assert len(re.search(r"q-signature=([0-9a-f]+)", h).group(1)) == 40, "[FAIL] %s 签名长度异常" % job["name"]
    listed = re.search(r"q-header-list=([^&]*)", h).group(1).split(";")
    assert listed == ["host", "x-cos-acl", "x-cos-storage-class"], "[FAIL] %s header-list 异常 %s" % (job["name"], listed)
    return {
        "Authorization": h,
        "x-cos-acl": "default",
        "x-cos-storage-class": "INTELLIGENT_TIERING",
        "x-cos-security-token": job["tok"],
        "Content-Length": str(size),
    }

res = []
for job in JOBS:
    size = os.path.getsize(job["local"])
    data = open(job["local"], "rb").read()
    assert len(data) == size
    hd = headers_of(job, size)
    conn = http.client.HTTPSConnection(DOMAIN, timeout=600)
    conn.request("PUT", job["path"], body=data, headers=hd)
    r = conn.getresponse()
    body = r.read()[:400]
    print("PUT %-40s -> %s %s  (%d B)" % (job["name"], r.status, r.reason, size))
    if r.status != 200:
        print("   body:", body.decode("utf-8", "replace"))
    conn.close()
    res.append((job, r.status, size))

print("\n--- 结果 ---")
for job, st, size in res:
    print("%s  %s  %d B  confirm_key=%s" % ("OK " if st == 200 else "!! ", job["name"], size, job["confirm_key"]))
json.dump([{"name": j["name"], "size": s, "status": st,
            "task_id": j["task_id"], "confirm_key": j["confirm_key"]} for j, st, s in res],
          open(os.path.join(BASE, "_tk652_result.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
assert all(st == 200 for _, st, _ in res), "[FAIL] 有文件 PUT 失败"
print("[PASS] 三份文件全部 PUT 200")
