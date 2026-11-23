import sys,json,subprocess,urllib.parse,re,time
UA="ShockMentalBot/1.0 (educational video research)"
def texto(titulo,lang="en"):
    u=f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1&titles={urllib.parse.quote(titulo)}&format=json"
    for k in range(4):
        r=subprocess.run(["curl","-s","-m","40","-A",UA,u],capture_output=True,text=True)
        try: return list(json.loads(r.stdout)["query"]["pages"].values())[0].get("extract","")
        except Exception: time.sleep(8)
    return ""
titulo=sys.argv[1]; pats=sys.argv[2:]
t=texto(titulo); print(f"### {titulo} ({len(t)} car.)")
for p in pats:
    for m in list(re.finditer(p,t,re.I))[:2]:
        a=max(0,m.start()-170); print("  ·",t[a:m.end()+230].replace("\n"," "))
