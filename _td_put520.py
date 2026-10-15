# -*- coding: utf-8 -*-
"""V5.2.0 资产上传：Python urllib 直传（本机 Git Bash 无 curl）"""
import os
import sys
import urllib.request

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"

JOBS = [
    {
        "file": os.path.join(BASE, "光学交互实验室_AI_v5.2.0.html"),
        "domain": "smhwb-gz-002.data-tencentsmh.com",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl8a51a57c30bb7aeb00065b9116ef9a48.html",
        "headers": {
            "Authorization": "q-ak=AKID-7tF641wLj1feK5P21xOhANpbKRcM7WTahCSUOvV1ZmKW3Qcm4WJEBq9JBFNAZds&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789528573;1789535773&q-sign-algorithm=sha1&q-sign-time=1789528573;1789535773&q-signature=e0006cb0d0bf9b3b48ff42d850c96948cbfd90df&q-url-param-list=",
            "Cache-Control": "max-age=31104000",
            "Content-Type": "text/html",
            "x-cos-acl": "default",
            "x-cos-crc32c-flag": "cosn",
            "x-cos-security-token": "yg7GR1BdVDxG8TThKIy0pM7ZAARQ238ac05c171550f30365221dcf2d58330103fVGJwxBLcaIpDDJsREQURcl-uwK1hHkmTyN3TTRTECndmy1IRI_-goGmf-tN217A9Da9v0YPWEwcx1QPSEpdp26_JVAX1eRRiM6WvRjEKnxplzIPxVhpgOPCc4vc7HlC4RMV0lCiNAw-P-58zy0_mdeXXP5H3ZYBGPaWauXNhYfD9A8bDa0MVqNwvGC0i3MMaV_Qo6aiSAAT95sYVhEbFt1yGgeux_f1D7yEIUZwP7WzLx_nUsiyytxDiK7INGoQlbkmwBYmcPLE-cieiuWoSgwWrRQidsY2wODZunQnQu_wQaBb-sze1XxPSuh5DHQifXviRoKvEUx9-CZxggq-UJj7_MdqzAIqIiA4hLpR8QvtyXGflYrEDlm1Y8mOpLvbIXgzoBXOjF7dWebW6nP0_utLTw04UcTIy5SIUKo53Dt1Y5kIhW8PJ36E1vuh1O2RvTde67ObhOJ1nv4kabMSyA19ClPMy7OJa5k_YFtjXcxA3rfGQCNi6F8-RQX-wkW9cefi12zzxSQNsn4XFFeU-RRQ8EQh3Cf4xhmJ27EO0HmLO1JYErwAqb6YUJmWOQjRXiZsj7vDWi2FTgNrlkX0oZvVxLOWe_ts4VCxW7Uz_kgX4kqNKg81Xy8EY7gwSHoRNO1s-NNqG40Xvlmc0wtOOqRfr2Flhc5vmQ0L9i5FUHQw19Xq6YIHBNro67R6kFI1ml2mHF3yekq434-CFdv9Rrw85J_Uo-nUQmoVHK_uy0vc8cT66Ke_QStPWXk4ptg00uh5SsLKRvl207EkP-2ZgFls1uUltSFiwtMb8jqomqrk-8Tmr-m56FmV_IEtSvECMxmjRCHOMmJh1z6vlwiyHcSAkV_f5FIRz3GnxZXLtX6YgcIxXzWzYSDxWh-EyIJJKKf_XsHSg08IJXnOv3gGpA2Pt5U4sx_ZcOtHAtRUMMs51wPhFTpNahpEoviru9eS",
            "x-cos-storage-class": "INTELLIGENT_TIERING",
        },
    },
    {
        "file": os.path.join(BASE, "工作记录V5.2.0.md"),
        "domain": "smhwb-gz-002.data-tencentsmh.com",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl4e7428a6ef9f70de00065b9116ef615b.md",
        "headers": {
            "Authorization": "q-ak=AKID8UvykHcQkzuDuoeg7iG3Ud58NyVXbSdPSXgwMzKbHbW3riKxriRKh2BxVgw006lZ&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789528573;1789535773&q-sign-algorithm=sha1&q-sign-time=1789528573;1789535773&q-signature=378b03b94dc215b4b51a63dffb3950384e699c3c&q-url-param-list=",
            "Cache-Control": "max-age=31104000",
            "Content-Type": "text/markdown",
            "x-cos-acl": "default",
            "x-cos-crc32c-flag": "cosn",
            "x-cos-security-token": "eKxFEONx2qVMcdp20BHTObcRQBtEpqKa07b6ccc92dedb93538a6fba051c29105mEVSovgJSdGRXgh2quOe8z4nb2APpNbaL5f83RHrPjTrkBkFAdD_97Bv8lNgWBYdm5Ftc5rbf4h1GWOmRii08xErh3Xi55JiHlOT79EGKZgA3uCVWukV0wm075ipL2rPKy6g44r00DG94M1N1_Q91OmAXgW9qVcW1hD93KDe86Lg__bBlxjb0kfoLEAWywdBMmt7XFw_NqHiNLGolDc_7o0VwOP1_D9sRA8LXc9eR8KVTVNsSKTc_EGPSVDU1uHTUnSeJstq3QZ3wSCCsYX-i3c3EWSPtZ-FXkKnLn2ut4m4uwurK2cJcSH9Pba4UeFo84GjC0GYwAMGjkj7j5IfHV-YNW5Xj4s60CHoy48Vm3DHEoi_8ZfZo8oRKAD-bJtJR7SKOztAsd8xlej_5ZUlsfLUgxA3UGw0-a_L_YqqsGoaePO07k0YrtJcsq9JBqikEK_ifhhPo_dGoM23l08Ae3iy8WCawySntyeLNMR3SP8V7GJaQj3z4MebwHr2SyNb6jdEg3Mp-97Ypcr7r-rmEGEOZs4QRd6ew9f-y7DBRb2crMBP18DGlN3tCnnFd_PAgT499AVNOilFDi0sMfDZi1ULInjKRK-2KCq3KQyDWQ-tpU8zF-qLyYvziC_ao4pWYgUycpMePvps3-q_LwqkOnnjZvuHH7HS1AKZWIMS8dnf6Sitye5zONoS8PoPoRb_Au84RokM6EG0d1GzK0g160rmqIj2ZUoZuTVlnUG5pRBTsfJtpm2adRxkAs2P0jYfCE_ZHrIxU1WFEPMERgj6Bk-X6RIIQyfcqgULD_iMJ27buju0kzQLojNS7VTTJ3q6yZcJemqgtqfcfAVCWowbI4nW-rNFaj0ITdWp4cZoK1pfe-NHvslumO6wCcYvVR8fHuD5tMLwZUJSc7eiccAhpbz8owS74I4J1Ilpg_MDIqLhw9Ma9WrBmpbSQ1rHevza",
            "x-cos-storage-class": "INTELLIGENT_TIERING",
        },
    },
]

for j in JOBS:
    fp = j["file"]
    data = open(fp, "rb").read()
    url = "https://" + j["domain"] + j["path"]
    req = urllib.request.Request(url, data=data, method="PUT")
    for k, v in j["headers"].items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            print("PUT %-46s -> HTTP %s (%d bytes)" % (os.path.basename(fp), r.status, len(data)))
    except Exception as e:
        print("PUT %-46s -> FAIL %r" % (os.path.basename(fp), e))
        sys.exit(1)
