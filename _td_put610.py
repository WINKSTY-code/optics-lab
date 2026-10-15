# -*- coding: utf-8 -*-
"""V6.1.0 资产上传：Python urllib 直传"""
import os
import sys
import urllib.request

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"

JOBS = [
    {"file": os.path.join(BASE, "光学交互实验室_AI_v6.1.0.html"),
     "domain": "smhwb-gz-002.data-tencentsmh.com",
     "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYld0bc6a220a51c32e00065b95bce1c7f5.html",
     "headers": {
         "Authorization": "q-ak=AKIDlF3iB41rq2iT4aPwv0YuHqDm7kLsyCl2Z0Hryxkp-e2btqAc2IKXwkxrFCz1Xqvg&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789548537;1789555737&q-sign-algorithm=sha1&q-sign-time=1789548537;1789555737&q-signature=f1ff7983c7f679eec7dba4cbb2e53750b70e4912&q-url-param-list=",
         "Cache-Control": "max-age=31104000", "Content-Type": "text/html", "x-cos-acl": "default",
         "x-cos-crc32c-flag": "cosn",
         "x-cos-security-token": "eKxFEONx2qVMcdp20BHTObcRQBtEpqKaf0688220a6767fdcd5fd0de240bf9027mEVSovgJSdGRXgh2quOe85IdVTqIqQxB51Wnjaxs9AAIejA3EEMpbjEcCUy-eQ91qUS6xSS_-QxFE9FnNOvlKfriywVNp80e-LHMWRTYro5N9NZgMspqzhPvdiytfEv686YTcMvSZTJGxmXykZIP6V5a2OoG2_eF1HFAJDqzXtL4Mgm4JCWuGYPwOObhmpAhopln8HNAEA4DoSpDP3hdWnpW0fpNC2mUexOAnce_-WcvFrJzX3csuZ3d5AVimThQGusiaz55TdQ-XnrXgLTX_eh0FNNq0zbIC5u64TKBH-6k_UDknbmKMxFWylw2qCR4tpPQiS64yc9Vy8sbmcaZxnmite2qSV9O_dVBPpq3yxcZzpL7hA8F06PZ9_2siaAs-ow56gamhP_zIZArHwi4YwJNCdPU8TKXSbwrQwjoPLMK7uIsVfW5TSCuSZa5-Nxa5WMic3R-RIX4JF5Y4m634pfnJV-8b3Pu1rW19YMjLSHQJFt4Ho63T0x6zwoCA7qAawCLn_CxypfUk7OjnwwJOALIYXjjsM6gijLdla1NN_WPkbg7OLC_5P4yUFzLfc4jQKMzMGQaWBGKQaYWt29iBuvP28l5VSxZ21YUXdFtKRzUzNrjrc3aws5mjDVe7JbWiV4rsXDSqYm138jX0puW6tklMKfILELLQ13LY7DrOY2a5ZKbVeipslWti4U-iH26s35wk_vze559tzv1iDYE9ToT2cZxnk9HcoMiLRD6tCM98AKSlbTSbziGA5FoLLDHNn94OLVtYQorFHMXL_TIm2BwgwSHl30xH6nzj0FbS1Joi93NdgfgI2_1k5zmW3k2Ql27YlfP8U6dcBP3JAME72EcrWohUrPhn1gxagKpuh03DS0o-RcN3F-VfdCfEdtXl_hV-u6yX8xUIGrL79_FJe7XjgtumTJGAn6Q8JW7aULpgrog5gxoRNZimaSASmLr",
         "x-cos-storage-class": "INTELLIGENT_TIERING"}},
    {"file": os.path.join(BASE, "工作记录V6.1.0.md"),
     "domain": "smhwb-gz-002.data-tencentsmh.com",
     "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl6909f70e1dd2034400065b95bd9169fa.md",
     "headers": {
         "Authorization": "q-ak=AKIDdS-URFopQMd0Qlapt9olwhX-LJPk6ni7S8spsz6ay3fy6HMNSAg2BP2A5kZGiLOS&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789548548;1789555748&q-sign-algorithm=sha1&q-sign-time=1789548548;1789555748&q-signature=14209440e3334e7c2188362f1bc2dbe1e078276d&q-url-param-list=",
         "Cache-Control": "max-age=31104000", "Content-Type": "text/markdown", "x-cos-acl": "default",
         "x-cos-crc32c-flag": "cosn",
         "x-cos-security-token": "eKxFEONx2qVMcdp20BHTObcRQBtEpqKa1f6dfb5e7c67333ac295d2c50bcb1fc5mEVSovgJSdGRXgh2quOe8_vLEgiXfOIvfWWfHo_pJsvubYObY4Ez3DyZ6BabjEbMC2tS2vtGDfYSik3EGGuDvntMLmp-XR8rmj5Xa9tZQdgUXqBa-Vb-1mt2OpTe336Tkc3QQUye2zIHrUgKz-WWPKWBqCQvBqjc6S2M4-AjdTUU-UkLadm7_kMGEdtadtIMKaoRnwyccte-0k3FesP1yLzcbAFy-FyufJjBovdWxkeNcbBpGKPyhHRAwvvmZETNrgv3UYdGbDwO3VbyRYia38JJ0Ul4y_N155TaKTS826sU-6wO7I4BDjCMeqpXWwwtiXnPUTSnSykJGK8NkyvxYUeOJBBT1WwOPDIK1o7KUyrTlWnSQXm4AudLYCN3iUG4kjgQeHiPx5xFZk1dFmWkJZQ0Scb69lQLci5K8B6iDWHxnQ9tQMsJhYtkFigT--V6bq59M5KNSjz_RADHRYi-t_hGzPoRyeWuUSHC-j6_iMObeVotEQkMjLxkSx8ArWTPJk5iAGxEVgnuhJh5PqWYxGP2yEipUQyNo9S_-t_9g9BFLcVjXh7ArnJbOaHyDs2OdVFwvLpp5K7odXol1IGYdl59JJUuan8_0Or1e_fgSHnZS9C8YEBBDMlmWKAi5g-NBvz5W779siGod0li1dBO4f0XDkMXAdDcnV9Vv4L7bFHO6KtJwev-_l5Zx_fiB6Ew_y4fSuL1mF4tjBRlxgpyvFJSiDX37qEiZmnUPi8Bl1ddLw6FmX6OSGOiMwHUkUaVZR8g5TeYoak1TTbIbRaNzSa2Rrveuu3irrgGWDkOKNA8Ww5oCSVsaHDHjqh8j6u_Jw6Vgk8u5XV57lPVGO1G9IqHVQtOD843k4QstNXNVvPZc0aWK4qEPNsCislwi0n0Mks-2KvtTiNGfm_gRRgIS9AtCLwULe9vtBpuJxVoDnrhn1gA5A-z3KyvWs7_nAvH",
         "x-cos-storage-class": "INTELLIGENT_TIERING"}},
]

for j in JOBS:
    data = open(j["file"], "rb").read()
    req = urllib.request.Request("https://" + j["domain"] + j["path"], data=data, method="PUT")
    for k, v in j["headers"].items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            print("PUT %-46s -> HTTP %s (%d bytes)" % (os.path.basename(j["file"]), r.status, len(data)))
    except Exception as e:
        print("PUT %-46s -> FAIL %r" % (os.path.basename(j["file"]), e))
        sys.exit(1)
