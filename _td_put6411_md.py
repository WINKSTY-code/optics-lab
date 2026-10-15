# -*- coding: utf-8 -*-
"""V6.4.11 工作记录 md 单独重传（上一组临时凭证报 InvalidAccessKeyId，已换新）"""
import os, urllib.request, urllib.error

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
DOMAIN = "smhwb-gz-002.data-tencentsmh.com"
PATH = "/smh2mf8nq7i9cemv/AAAAAAAAAAAAAAquGxmsFgjIGlOQUWYl68ee333dc368351c00065bbca6520e18.md"
AUTH = ("q-ak=AKIDD4a2__QPq7440TKBTlTHsNjxR5H5kBER8lnvr_GrohmlsJe_WjZklLi1QNhFQSke"
        "&q-header-list=host;x-cos-acl;x-cos-storage-class"
        "&q-key-time=1789715662;1789722862"
        "&q-sign-algorithm=sha1&q-sign-time=1789715662;1789722862"
        "&q-signature=e516292c5ade95f0421962738acd3cdfb359e279"
        "&q-url-param-list=")
TOKEN = ("9N2AvNna2G7yF4vA8er503yOSRJrLMbab9a1ce5bd8887589511ed98ee3294b25"
         "JvbMZSM63Mx76BxDcCnEVAhiGEzD7fIJvSqYHI6Q_3LTLGjIKeWa8Wr4WCurMP8cP2yeIFFUf2ESxxoJEpCP06QyIGC9tRZ8tnWqlQyr-iBGO3w7xgJsmglAxXI1xJkSq1KDP5QCA1U_q86LOafY5V9wpRCK-Iy773ML1_xABySbA_PYS-CJ4Trk2CziE0oP4aExBiNGPMKkEeiiUsWCTdK_KFU3xkz2HkkcQUh58kgXj3a4fE3PUtBxjHRBXJA-YxZebtzJCzX89aFst5vlpTMnNWWY3coxadXv9o4syJUpgBFKdIx4-e825wdt_MXWXEhgq6YTWh78zRMYmOsVMYZYloMXJC_Olj9gJRXYtdHwM1CgzFgzYEk4MPe-1ebU9OCuO0_B1xdJocmyn7-JeYarW9uJTNog3CgqE-tdSB64-tqh5FyfOA0jf_DFSqjg-mxKIv6Dyl3Oxu4MRAT3I4lmcMgpPZCfkZ4OSjmHQqop_J3Z-ymr_15LsmTafR5klxrzzlVWnpKAbwQlYDpb-tWNPbSrjvYxzhHfZW0zfsPDXdcjgCBjEIgH9oOxtA9rHFJXraFWsZ1Cg5mY5GziZTleIN9cfwSBvrtPnu_cOEGoVywquPPd7CpB5isucn-B1WdHulIn452-b3OqYMaIw9FDyGcELWjImYs7TqXqa0iXRUH-qVgtCXd7dT1o5Yszsrm3DcFi6SzpqQbIEu20mmjqqB03bf-s5kvtwNh8gSQudBXz2rU6I13xEsySzCokr0DCwvCxkHEaMtaqrY7HRRKMSiDPM5RUtHjFLazKJAbN2ToZKc0sNGszlabkgKPMzlXMPyce84P9FBJfpb1oRmAMGQpB3ZA-YIb0LD2wnVRUmQ7QrR9FPbu9EILEa5zR3_XVuo6SKWDPRt3HGdr1nnQt7EsT-vk7bARVza1KpjgW-UFLsUQkURzQ29DZEm7l")

data = open(os.path.join(BASE, "工作记录V6.4.11.md"), "rb").read()
req = urllib.request.Request("https://" + DOMAIN + PATH, data=data, method="PUT")
req.add_header("Authorization", AUTH)
req.add_header("Content-Type", "text/markdown")
req.add_header("x-cos-acl", "default")
req.add_header("x-cos-storage-class", "INTELLIGENT_TIERING")
req.add_header("x-cos-security-token", TOKEN)
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        print("PUT 工作记录V6.4.11.md -> HTTP %s (%d B)" % (r.status, len(data)))
except urllib.error.HTTPError as e:
    print("HTTP %s" % e.code)
    print(e.read()[:500].decode("utf-8", "replace"))
