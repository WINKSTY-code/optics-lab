# -*- coding: utf-8 -*-
"""V5.1.2 资产上传：Python urllib 直传（本机 Git Bash 无 curl）"""
import json, os, urllib.request, sys

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"

JOBS = [
    {
        "file": os.path.join(BASE, "光学交互实验室_AI_v5.1.2.html"),
        "domain": "smhwb-gz-002.data-tencentsmh.com",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl5ebdf5832e3b540500065b804b04cf37.html",
        "headers": {
            "Authorization": "q-ak=AKID9FwGF8LzY364H_sdkCtKODz2ucc2y_NQFj5JqAI3D_6XQmlIK8IQalFKrVHc-rgn&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789456432;1789463632&q-sign-algorithm=sha1&q-sign-time=1789456432;1789463632&q-signature=93fb8d44522b7a6155a16e3b80f127995cf073e6&q-url-param-list=",
            "Cache-Control": "max-age=31104000",
            "Content-Type": "text/html",
            "x-cos-acl": "default",
            "x-cos-crc32c-flag": "cosn",
            "x-cos-security-token": "sRG13TneIPWp4GHkHL3uYpB4tFVjkM7a066d6fca87cb149062ec4ec6d0831b65fTxEVDcK_rpD5laAJp6KBA0C1k_eUvPzlcWf06itGHkwPfrwZhOTRRAH4yLA536KUN5DFW4MJLVoyALJtpe88TyeR0MJ2eEQFDziuUwKQMMKAvJcmtRCSM3lurhq_6xbW7G5ugn7Vjhw6HvpUM5FEgIMtiJR7VSCsufkW3lW-eqC22Ir5MxyJU2oZ5fIpGz-rp1vg74Rn1THGtAwAkcA9YToLd6IzkbA4GP4enQiPs40TD-PFhM8KFoT27Ncdn7l8lIff4ThImjbNyr1nm7lcotiVSptkauHlTPOkKn1drfNJRNq3c_zBpSD7DSI5EuKKqYiTi5b3d1ygfXKz4GgMSH_rRBFSz1g18aXIw1hOQSLFZWAnZCa2AlQj3P5UeI4x_qOlPWir04Nvs_Z0dlG5mU5E2YFsoIVnaO_er-1P8tibvTWYruq22oiDU_v6qQZEUuQ_zeyRywr3zmOyswwSSov4E11GE6xsOocf5zfEpMjIDfzrmcxQdd1OdM7tNczZZ9y6KnAg0QJRZmssuONBMxwJkHsBL8t8ANtr1rQbOEvJk3w0o_fHMnKOmDSwIz6MAnhK0beXEo-Eb4xA9BUHwOh7aNN4aWzUeCOI4N8VyGJHtS69-X_2VMAd8A0Uak-HjJRW8jK_eg9pnDkQcMJCMM4srDY8O385AJysfby2nZAVO1-t7tq015MoHRKBfrXhets-aMou_Y255qPu3lPhGdyq5yMNYIsjKbDoCLmvabToT8r_Bsu9wwsASE0neGJquiOewzKlVba5wnd2Ezc3exXEa6GN-XIap--j_ubUUDl9XXjXFpotJuIhHo0A66wN1cxduNFigo3KMX2GihwUZJ6878ch1Gi9Tf8DAxvl2RTIiMBtkdzhWaVhyXbEQh7_x_OLjWoOM55ImXTysGQiBg1Yw6kFtvfk5i2o-dNqoCLm9tKBYGisuEjUU-5vLnA",
            "x-cos-storage-class": "INTELLIGENT_TIERING",
        },
    },
    {
        "file": os.path.join(BASE, "工作记录V5.1.2.md"),
        "domain": "smhwb-gz-002.data-tencentsmh.com",
        "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYlef77548aa2efd37f00065b804b03f858.md",
        "headers": {
            "Authorization": "q-ak=AKIDW_HKYnaeLKIslxomH5P5SRqojjnE7v-FZw5H22SDDyFpOMjGC_0IdD6K3PBur7Hn&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789456432;1789463632&q-sign-algorithm=sha1&q-sign-time=1789456432;1789463632&q-signature=5187892189ad392de13832f1e086924b70c95168&q-url-param-list=",
            "Cache-Control": "max-age=31104000",
            "Content-Type": "text/markdown",
            "x-cos-acl": "default",
            "x-cos-crc32c-flag": "cosn",
            "x-cos-security-token": "sRG13TneIPWp4GHkHL3uYpB4tFVjkM7aa4474f835132f898e842c8ec220c8e0efTxEVDcK_rpD5laAJp6KBC8o1XVy8ZUXKTqCS9eZ7XOLwOiT83_BB-aMKp9OZMFmaU-ZZaXCtmyhaqTdNGTZts09Uqn4Ww69WqA2fAjSxXa-NYp1H9nXTd91ZqHR8RzSTvAKtojoGjaZ2fNm84KbQ2OEkjRnDyigTM3-kOASBaL6Z_n4KCDEWIIuEeh7AFbvGYc9ujNtN2DwH5mTTKdDZC1CwkXrA45nhQJPK4fKEEQfPNU3gPZtPhIk55f8Q9oyGX163dEACOkndKtkVM-BxphxsKddq7vbMqHhX8ad3VzcZcjIn7OBPQtHI3zjXNUJeaIICyFvFvDGho417ZCWhPmKpbpQLoj4IVven3Xf_P3ouG4Cf6aiHrsqRrAJmqj0dpDNYenmZrvWZwMHCsIaqL0rTNLQwtoqoVJBsJSIvyTIo2K5WmCCKemp82xEPachS_vUfKtmTk5EYwHHOmogOepN--hZoRcc9pHY1qqt54cL2vF46gPfFf3onQygYODvGET3vYS_7s8ZKY0VN4fIK6RSseMBOph1_AdITJPcngJnBhYHbm-J1KxBaSCZ5uA00JMjM6Yr2lPUWdZaMIcSSisN2G-A8N623zlRv5zPZdphdkoQmcmEkifcMUNv1ZmeqPmOP9X3X5rubZBnE3KHPs_WxcQzheiovtNrcC5-iYWD4x036HkG7kQ-IWeqspndBn0ALLRPnOF16iuPbxz6YlaXwhg9nkyU6E62-bou118cyTw-9TyZZjK9R5IsrnGd1U3bRC3cttzOpntQodsQ9fJ_nP4LeM5bJrk664V_qvDS5ZBnQWMkhRqMiKqyQ2Jx0HrC468Ys0XG48QpNe20oTaZ_XFRxVWcOQ7sZULsM746fA2qC5p63hm-9JRSetSVxNJtEFFpLsGfCB7VenvPUuIvySNAJSqLUCrfHs5tVFUTnx3AKEMe9--ZtaP--fOi",
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
        with urllib.request.urlopen(req, timeout=180) as r:
            print("PUT %-46s -> HTTP %s (%d bytes)" % (os.path.basename(fp), r.status, len(data)))
    except Exception as e:
        print("PUT %-46s -> FAIL %r" % (os.path.basename(fp), e))
        sys.exit(1)
