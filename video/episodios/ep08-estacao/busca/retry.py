import json, time, urllib.parse, urllib.request, re
UA={"User-Agent":"VideoResearchTool/1.0 (image search for a video project) python-urllib"}
out=json.load(open("arte2.json"))
falta={"oyuki":"Oyuki Maruyama Okyo","yoshitoshi_okiku":"Yoshitoshi Sarayashiki Okiku","yoshitoshi_36":"Shinkei sanjurokkaisen Yoshitoshi","botan":"Botan doro lantern ghost print","yurei_zu":"Yurei-zu ghost scroll painting","kunisada_oiwa":"Kunisada Oiwa ghost","kuchisake":"Kuchisake-onna","hanako":"school toilet Japan old","kisaragi":"Kisaragi Station"}
for k,s in falta.items():
    if out.get(k): continue
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":s+" filetype:bitmap","gsrnamespace":6,"gsrlimit":6,"prop":"imageinfo","iiprop":"url|size|extmetadata","iiurlwidth":500,"format":"json"})
    for t in range(6):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=40).read()); break
        except Exception as e: time.sleep(60)
    else: d={}
    out[k]=[]
    for p in sorted(d.get("query",{}).get("pages",{}).values(),key=lambda p:p.get("index",0)):
        ii=p["imageinfo"][0]; m=ii.get("extmetadata",{})
        out[k].append({"titulo":p["title"],"w":ii["width"],"h":ii["height"],"prev":ii["thumburl"],"original":ii["url"],"licenca":m.get("LicenseShortName",{}).get("value","?"),"autor":re.sub("<[^>]+>","",m.get("Artist",{}).get("value","?")).strip()[:80],"pagina":ii.get("descriptionurl")})
        print(k,ii["width"],ii["height"],out[k][-1]["licenca"],"|",p["title"][:90],flush=True)
    json.dump(out,open("arte2.json","w"),ensure_ascii=False,indent=1)
    time.sleep(20)
print("fim")
