import json,sys,subprocess,urllib.parse
# uso: ov.py "consulta" prefijo N [fuente]
q,pre,n=sys.argv[1],sys.argv[2],int(sys.argv[3]); src=sys.argv[4] if len(sys.argv)>4 else None
p={"q":q,"license":"cc0,pdm,by,by-sa","page_size":n}
if src: p["source"]=src
d=json.loads(subprocess.run(["curl","-s","https://api.openverse.org/v1/images/?"+urllib.parse.urlencode(p)],capture_output=True,text=True).stdout)
cred=json.load(open("creditos.json")) if __import__("os").path.exists("creditos.json") else {}
for i,r in enumerate(d["results"]):
    f=f"{pre}{i}.jpg"
    subprocess.run(["curl","-s","-o",f,f"https://api.openverse.org/v1/images/{r['id']}/thumb/?full_size=true&compressed=false"])
    cred[f]=f"{r.get('creator')} ({r.get('source')}, {r.get('license').upper()} {r.get('license_version')})"
    print(f,r.get('width'),"x",r.get('height'),"|",cred[f],"|",r["title"][:50])
json.dump(cred,open("creditos.json","w"),ensure_ascii=False,indent=1)
