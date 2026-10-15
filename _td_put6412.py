# -*- coding: utf-8 -*-
"""V6.4.12 资产上传（沿用已验证口径：urllib 直传 + 只带签名范围内的头）"""
import os, urllib.request, urllib.error

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"

JOBS = [
    {
        "file": os.path.join(BASE, "光学交互实验室_AI_v6.4.12.html"),
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl0467a341409cb95e00065bbd0d0b088f.html",
        "ctype": "text/html",
        "auth": ("q-ak=AKIDRPyNI7gnyCCiNNojoP6oyBimxF2cBNm5Sh6KIh21muaRN_YkSqCVsAuDSEBZRVpg"
                 "&q-header-list=host;x-cos-acl;x-cos-storage-class"
                 "&q-key-time=1789717386;1789724586"
                 "&q-sign-algorithm=sha1&q-sign-time=1789717386;1789724586"
                 "&q-signature=e35a183dad3e339cbb1d82c5b4172a3b04e2305d"
                 "&q-url-param-list="),
        "token": ("9N2AvNna2G7yF4vA8er503yOSRJrLMbadf890c94922ad339af09114228259f23"
                  "JvbMZSM63Mx76BxDcCnEVITyh8fzgl3bJddrcxsxW8mb0Wz_FeqpIytSQFGqddKKwW6dFdFjFxYHQZ3TCLS1UaE93oa74Ci77X8DNZMptHlZ_GspUeSZAlVf_ZUxiYuo2N1OKIoMx820zhcZd0gk-u-0GPnme8lflgK9Q6_bPTjz5A3Oz2TX8ZmU0LOZ3R8RBGQbjD67F-97Yn2xeHAYmluqZUiyB5Mbx73GBCiCPf4InPjQb36k-A_jkwLNlYyAmHK9oDHehUwxSRKnCxZfsYwNCt2Z6fGc5srE0UcLGGGK-XuLVytxFDG8-410SdxjO7tWUATh-Dc_t_CtGT-3NphrLRNTTMkypPz6LAjKhepqUppUrwc4Qq1njeaFjb6WGoM8vu3lj_0uhnq-MOpV4Ch4qlWSzALyViwrmAPo8JU_nFaKuUDt8V8enPOPZWp7dl2mP9eVWouH4ITCwg9DDHys27pQo2GNkULaxyflAaVxiM6kNzO9I2umzRjmuFSa-XOxXFMGa0W8eecnV6_bd7V-OZhpBP50Vec0QTnp0YjACtGmlOi78xOtm7LllsgJlqFqsgPi092C3RM716n3A2CEDzUdoMyeDzuXOzQc5_A2w05M3SHioWLGYRBG2j0XnwR4aWTrPyxfSsjF_cjVVXhpRvpzXkpO4RRwnFADoerp5lKPzljx6d_UVt01T70okWqY9teFD-LNrOqVj9NfvtwerhN8mSgEFkgPjz0Bhc_wyo7y-F2X28Q_3kCbtyqHNm6HNJguWXmV_WEZ3FXK9Z0tJ2mEjzxfi_YFB1RxSRNqMKwWO4SEvwL_srU9Eu62YuN4FNOcYAt6ib1P8T8WkIbcZWnvJklxA614-ovTJYQcAUfNWSXcGFgnWhD9In7My_eYTHN_8eS-NLM7ZU2rswmAa0-PvBKCX7XeylntfAKDkzkIfC5y_j4OA-2Es44f"),
    },
    {
        "file": os.path.join(BASE, "工作记录V6.4.12.md"),
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl1f6442fdcef194fd00065bbd0dae68aa.md",
        "ctype": "text/markdown",
        "auth": ("q-ak=AKIDN7IQ4C-giBHGHa1IoeWePsNeetH3_Qzgxfxd7H6pyYtnS8FL7w-BNlBaML9vHuOU"
                 "&q-header-list=host;x-cos-acl;x-cos-storage-class"
                 "&q-key-time=1789717396;1789724596"
                 "&q-sign-algorithm=sha1&q-sign-time=1789717396;1789724596"
                 "&q-signature=99be139529d02a93813879974ec883b02caa2b6f"
                 "&q-url-param-list="),
        "token": ("9N2AvNna2G7yF4vA8er503yOSRJrLMbad4c80e3ee6d6c94bbc5f1ad9f87170a6"
                  "JvbMZSM63Mx76BxDcCnEVBd2c8SqROJ5elLGixusPDPbE_qeoxgd9wpsDRkWVWKZgL2M8UG7FpXnRIIH8nETSkziD_hA2sxNPKGC3UDV4wZBZ37UW2mM0QEqrvXgaQwduYw22f1eYGU5kaXabZBGoBzQV2jgv9WVzLvEIKPtG-i0VV2wPghU53suNbaU21VhLa8ydlIcsIdYOCbD5PTZuo53TDuel5NmZwr-csUSrNFsvWnCI7P3RdO1sIItQvk_Hv6IU1mwLNxRmD8PPjCPo2QYaM-WhZ8xGbFptwaO93GtFlyKmEIUz7zff1cMgytKRmikHBli-GOr1sZLElG3GmsatR0LwyQSIIVFZQaMJ59cYM2EDFV0DmApUJ7uBhhVu94K_nXW5FBJUqF0oZ-D8NtFaoCAACa-Z5he2KBO3KJIQdG2BxkUr-5u3IsABeZO4OoCk6XFR41HPKIkn0vN3c2FnEfuriv0tgtdY_ryfHkGSrThmpaZvQyapWdtzT0H5oKyd6FHHmy1Kqom216fR9PabWrSm6Sg1Ex5hS_I4cnlIw_1M4AQOvAT_DqWNkSLqUr2Y5aSHhn2q1DzotRK5Y6OeNF7DwfgZ5Si0TPye7-OAlXpSM-qiKjdJkQmTe-udSqj30NYX_ZTuGfmN74gg30sGC8iqN4qPDNQwAMGpIj7WgGGEWfMzGgsGmTq1hGXVgdKNCjEDc8rjR0QxKFeHSIIERltUjgvTAu0SSp7jm-7DT47fa-0u0V2nVi08P_7jW9pkEPXORbr3LPhSy5qghr-o1kv-lt-fWsK7ZUvclyZdNBfZH9kG8dirClkIgi1-SoM736z1dT9mdaGTkzczGk_x0mNfXKKtflYylkEMM90OUcMgicTWFfBTS1t3qhH0XAHExQ1yB6VED_Kl5DwQSyKvkDsMgz22qYXl6FOQVO5UHlCKpHW87iT13EBoye2"),
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
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            print("PUT %-40s -> HTTP %s (%d B)" % (os.path.basename(job["file"]), r.status, len(data)))
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "replace")
        raise SystemExit("PUT %s -> HTTP %s\n%s" % (os.path.basename(job["file"]), e.code, body))


for j in JOBS:
    put(j)
