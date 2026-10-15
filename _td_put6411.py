# -*- coding: utf-8 -*-
"""V6.4.11 资产上传

★ 头集合教训（V6.4.10 实测，沿用）：只带签名范围内的项 ——
  Authorization 的 q-header-list=host;x-cos-acl;x-cos-storage-class，
  所以必须带 x-cos-storage-class: INTELLIGENT_TIERING；
  不要带未签名的 Cache-Control / x-cos-crc32c-flag，否则 403 AccessDenied。
  另：本机 Bash 的 PATH 里没有 curl，直接用 urllib。
"""
import os, urllib.request

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"

JOBS = [
    {
        "file": os.path.join(BASE, "光学交互实验室_AI_v6.4.11.html"),
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl6a219ac61aff981b00065bbc9c31ab98.html",
        "ctype": "text/html",
        "auth": "q-ak=AKIDqSfioOSfSIntOqYXcz2vKDRRwo5fvWQ-oppQr2kDmbAOdWk3Ve1CKxluCoy3iCc6&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789715492;1789722692&q-sign-algorithm=sha1&q-sign-time=1789715492;1789722692&q-signature=90ee201a8ebef5144307b8a54874b6baebb15564&q-url-param-list=",
        "token": "9N2AvNna2G7yF4vA8er503yOSRJrLMba5c558b701ba4a80eda38ed289fa7748bJvbMZSM63Mx76BxDcCnEVJZ51AIbb8COqgaN5ASbB1yGA50ycI9f-7v-kSM5gz-QPQbfK2powgGaDs_4JYqeSWXISzZFDiOQB_SeJdgJYkCia3yQ7KHAFEfz9ht0HBHOVdEeWXL-u3dBeSMa9lZ33YkM29VMBG6i9_iEqODZkIWwH3-td8Z6bZ7El6JKbxaS6S0O3gXxOKhbULSaMVgEbUyzuuxfc2q7mJYXX9jU7xCJ1e1A49pl6UZv0O2iyBOQ12sXTYeBrCsssup4SGG_Dnquya3j9BVB-jDWztwLJokfNkzGK8JHT10BgBT1VF-cm7lHiYeUDGdvCPkKPlzi9shYDW9FeQeT1yojExdFfpZDc2zwqIXT7JbvDxugu6kNUCGogbnxFRgYk0-KQB9ds8bdBetpI6pD_hLa_uXBFbnYXmi4CgKxiRvt5yLs6cx40k0mUrfADnlm14S689GncsfoAvYPM6aBCwqEgWPMC2IROHFJ8i3mZ-rRrChdNisqCSSoFdumRZNhQNxrmY7Kg0lqLVkyGrCZmDnkphKPNYiwz-POqa9b1ZSaGrpypssL5dMzoUM-HxJTqq987OVTGQM2_ZX-Lacb8VCG2SNbZQhpg-6DXvSPJH9VBYCUikPbgwq2NqG1hNWGHIccUvle4PKb-5yAWuxKBGSbY08gPD-e2ON4HgGF1UDUTnTo_9r3RbZV_LVHnwzMTolUMlFYn3Yd4bl91FhGVMJsZGyHxHHf0vEqeh8P8a-1yAP-wLOb3r7U8Q08EcMH-rEqNkp7Iwwl0b25z-m82MsNBiWAS5pRaZFP5Xdji7ujCJ4201fammVngOVzeNB9BZFLNiEW4clIJmA1OvjUWSqo9-XlC7Q3z4aHlwmffI8JHPZWJOZ_ZfAbQ5yCO51xW0aJJNPirwCAyR47Za82qH7BrMkxxflvADG0efE8a8uLlHxi1_bE",
    },
    {
        "file": os.path.join(BASE, "工作记录V6.4.11.md"),
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl1645664f5110ab4f00065bbc9cbe3c46.md",
        "ctype": "text/markdown",
        "auth": "q-ak=AKIDvYsCAJFrS-syiEzJbGtLFdC8jB7rSLSdUYdxsRKKKNxkGoD9PKgWd8xoIFL66UTN&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789715501;1789722701&q-sign-algorithm=sha1&q-sign-time=1789715501;1789722701&q-signature=34e107ffbb040cc0df47ec13ccd50eeeb419338d&q-url-param-list=",
        "token": "9N2AvNna2G7yF4vA8er503yOSRJrLMba982786ddb9339a9c792456574ceaec9aJvbMZSM63Mx76BxDcCnEVL3HzlbMTh1vImQF7qixX-0WGh_POMjzMvRFkkOi0UFj3nqIBAgbJfIxa20K8OXNDZM94HSnm7kdFAebxBTar3_bOABzMMo3DJlXdeVagPX4glm4T6-qZ2OwsTbkGYqKFAFwak7OmMsVLuJHNLYzoC_kW7qv9Oj-TlBiIgpZIJ1hHflCYbRSeU-navlWbyS4TIzJ1wT_3PDgFH6x2lsdA4qKpsWDYFWH8ttruqT-nXb-mJBw8nv8erd6itdewv7AURAlyxC2NB72ZYBeJGmwX5NE2oMov5Om10G4k2prW_GhmbEyucJZLJjBKqkSXv1VimbPMloXbCzLmThV6VJZHP-406K0rtGVXwbh96CRHtmyNC7yzrpQ5cJWrxcogRIxjtnYKs7JqVnvVLFFgwSje79Pzpp4nmoudqFc3uMGkoXOgVfcV8ObJcP-1URNJ7cZnzYJbtqIqlvLXMYq7r0MsernUv3-n4KTRD53d9sqlPt_BAfncxI0X3mQSybiCbYukDNnzVHJVm_46ESqkcn6DzebLL_6T3_TWBckPA7PwOfuDXkn3YwUmJPUcNeElVHTHr20a7EfJ0vRc-8y8J8IjnLjG9IAO9hVOWZzrE5_bSZ0gBJK1537A-KK1MJEuQr1vdWo0UFIMlxaJLdIrm17isI08V-K9k2bp91hZMJNUG8CvCMvviHxqX2Wyh4LFzEr79fXf4iVSKoFt7m01y67HdlOQRKmt9FZlCJtDI-skWw4U1VJHTqL3M6IyRpY5GXuD3EDt6hc66EqsA66P-yIHU14HzBuTpF9owbE-cNtE09akSxP-qXxDSH6kiHdccSmiqs1sdnJvuCQvNqxHjZfwdDQ7mD7QxJtlcw9o2sS2GVSR1oZuvWbLidQ-mqrtfwavEIhEGd9yOoxB2P14UA1LS7uhL4PDYqfWlh2eDAYAqGlWH2U1eosruZYPKlp8b1Ix2nZFRjNAwEaV7C2mUDmLZHHszsRN45BfgFEaHKytx8ny1WIrPjsqxsZwIEvzllCSXhkngPFBzZCbCx80fdg_2-N_S6DFzK4Wj1nZbK4MaAT-dO0Pxht84Y-3LOYGzcpKvA9T3KCAayTtUfchSGnj0zL_nGqw3EI_Tia4cGxS-sT01GEbhqseVWN0-A2dSDFrzY",
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
        print("PUT %-40s -> HTTP %s (%d B)" % (os.path.basename(job["file"]), r.status, len(data)))


for j in JOBS:
    put(j)
