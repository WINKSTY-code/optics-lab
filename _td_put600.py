# -*- coding: utf-8 -*-
import os, sys, urllib.request
BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
JOBS = [
 {"file": os.path.join(BASE, "光学交互实验室_AI_v6.0.0.html"),
  "domain": "smhwb-gz-002.data-tencentsmh.com",
  "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYle21cc188d884d77b00065b95534f7c2e.html",
  "headers": {"Authorization": "q-ak=AKIDiZNiXtTQaEfmnQoGBjs5yAkY-YZvbsOk7ST2_QcLWKSrffqmG59Rh0ZAHYFgq2OP&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789546766;1789553966&q-sign-algorithm=sha1&q-sign-time=1789546766;1789553966&q-signature=caaf282c881bf84e6d1d32c3e06ec816ca66cf2e&q-url-param-list=",
   "Cache-Control": "max-age=31104000", "Content-Type": "text/html", "x-cos-acl": "default",
   "x-cos-crc32c-flag": "cosn",
   "x-cos-security-token": "eKxFEONx2qVMcdp20BHTObcRQBtEpqKaeee9227659b39c645f769d1080d89a24mEVSovgJSdGRXgh2quOe81W2v0bAJNK7gOOPCGu8ICdRr8xKjL5JxRv-dJGuLrvBLtI3ffyToez_Q7h9YGJ16RcAeB7aEAtBIw7_nMuzsux2KvnkBIOZ3ZVQoPrmvQ5TpwHlLBE5dpg1LB1wnG11Unqo4Z5m-89LeKljlxS-qL46odpOpx1klsS5djxcFIhdhcvWnCbw-XBNc8_eQia2c_fbA6kURARdromGSxJyt4x1r8As0488APllO4fNACVpDwE2mVfpCX5wcEcV7qUWbEIXqn1WRNE5Ow2XwTO3DUG-RBI59-1ppsojirL7oOtsjzWfYamXHkleb_wz8cBcTsn4MkBhAEaVKTqjMZYN24cu6NYFhZBFQ2C4VXnrGdEah1pqI7TijoO-M4xIHsZ33mSx_rQouvtiSrWddmhd92JYE8OJa5O17uvBL8HHMN_6yrqOoYMqVD_3IH14X2EeqL4luo6RTrYGw7_L-SHE_iIRVguGkTleDKTFNQAnSSkEA9xYzurzRaHkyMF7KwG9i92xcaE7e2Rou1g9rrE8OrBkQQv7ZgzFIJMRITapwTskEgoMJNgQY7lAEX95VbIsy-hDNR4ELBuRO2xZPImxIHjvdWrPkDGH25rZzXuP7lWaf9YHxvYpEhj_42KFlWED7-GnD_9i528IbFAO0r_owqtAiAnJ-6FSoiJEvkB54BTIYTimRSLwhGi84hF-MoLnorl8l_bUICQwXjYHEcW9N2enZP7o5wdUqh1obkJ6v3GK1zaNh6T4zSueQsJ5eDNL2DkGURFubD00shQq8pZlk9zYgcPPfGD8HsFwQsLyOAbo8bC6Pju_g-JS-vcvj4NG-Fy8Z1xuShWPHbjcSHBOGdlo7cUiKoZPQ2J0QdEHdf4SfDC8C1vyGc8__ZMmNrxkiqKsptvGI9P7dd3jKRkSgdZWgOdawy-8A59dqJ04WOLs",
   "x-cos-storage-class": "INTELLIGENT_TIERING"}},
 {"file": os.path.join(BASE, "工作记录V6.0.0.md"),
  "domain": "smhwb-gz-002.data-tencentsmh.com",
  "path": "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl98a76eea38a5ad3c00065b9553f0301b.md",
  "headers": {"Authorization": "q-ak=AKID6tShbiQ5IO0vRXE2LSP_P9DNets0uIp8f1xOy8AmI-zBMSUHHMqoe22BBdEFWNnE&q-header-list=host;x-cos-acl;x-cos-storage-class&q-key-time=1789546776;1789553976&q-sign-algorithm=sha1&q-sign-time=1789546776;1789553976&q-signature=0abd98200162462dd365165b6ddd7a1648d3923c&q-url-param-list=",
   "Cache-Control": "max-age=31104000", "Content-Type": "text/markdown", "x-cos-acl": "default",
   "x-cos-crc32c-flag": "cosn",
   "x-cos-security-token": "eKxFEONx2qVMcdp20BHTObcRQBtEpqKa91546b2437d01b5c43cd9582705f12femEVSovgJSdGRXgh2quOe86FDfm175a5Mkdu3urfwRSTo4I8EE2l2bCYNcQCxjF1GxBe4LSKRgPIW6YDXD1ChTLc32R6UzU3Omt5xOWl9rpvlhxGIYmxmwVDMF54CL6zpJqaQD76H5cmtFXz3dF63MoQlcn0KWq9ykC3xOMHQeyK7IwmOLBObItCuRJMs0MW3Kz_p5ubxWcFwluVfCJSoGy5UBAToVUi0pQQlFATdSRZdU45iXS1kgUYvsQFf8Bxsagh8rOS5feS_zMkC-ZufagOt5l1yfol6S5XW40OimJelfSYWhGmJo08w50Sl0i-DePWTUhqXIkUnCrZuWAxBX6sXfJhZZB_-Re-RGQayrppCCiemfIxZK1F4OiXcv3hYjldZQCkMsgVvCAww8TACtrwubvP1bEzjNnUelSuyS2_GBZziZbHRDjYQdGSpsQsBOl4ad12bZ5cTXL5Pk38ED_2GjBK1jxrq-RYd-fIWH5qHWtdqXlisvJ8KWE3F6fqzYRZTrsgwIuDdOVxMPYZWfmUWF-EbcP1ijryq95CA7Xwo63w7NPESVfi8TLKai5ki6WgX88Yxt2WZPbwQoK38wJGoGDMOT1QZkYIG4t1N0TVeTXO7t3KQQFWu0lTCmc1SQvbtxC5PZDPQwk-SlzQ_l1lscrpxhLJptvuOFssRdtGqmOW6VixcU3Co2tR4_hikiXNRPWvcvoyMhuYdcgUkYAP9ZZBefTo-o_bwt1kiY8WAd_zzA5bJepM_EzYcnE0X9wFWwyB9Jj9jeWiMn07Yc6Q-MDKB6aTeCxyLtaRzytx1y70-k0XugnBN1n2iBlIUu1VN2YfJBcitSKooqgLkf7Mz1AQyxhUkq5GZ3J5GG2MvJRRfr1zGu8oxfbx7QJujQi3gqJPyMX3pMFxni5S7HRW_WykFMBD72thHBacFeVgM6u_0GJNAYUhjt2e-iMbB",
   "x-cos-storage-class": "INTELLIGENT_TIERING"}},
]
for j in JOBS:
    data = open(j["file"], "rb").read()
    req = urllib.request.Request("https://" + j["domain"] + j["path"], data=data, method="PUT")
    for k, v in j["headers"].items(): req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            print("PUT %-46s -> HTTP %s (%d bytes)" % (os.path.basename(j["file"]), r.status, len(data)))
    except Exception as e:
        print("PUT %-46s -> FAIL %r" % (os.path.basename(j["file"]), e)); sys.exit(1)
