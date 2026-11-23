import json,sys,urllib.request,urllib.parse,os,re,io
from PIL import Image,ImageDraw
UA={"User-Agent":"ShockMentalBot/1.0 (educational video research)"}
import subprocess,time
def get(u):
    for k in range(5):
        r=subprocess.run(["curl","-sf","-A",UA["User-Agent"],u],capture_output=True)
        if r.returncode==0: return r.stdout
        time.sleep(35)
    raise Exception("fail "+u)
q=sys.argv[1]; tag=sys.argv[2]; n=int(sys.argv[3]) if len(sys.argv)>3 else 12
D=os.path.dirname(__file__)
api="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(dict(action="query",generator="search",gsrsearch=q,gsrnamespace=6,gsrlimit=n,prop="imageinfo",iiprop="url|size|extmetadata|mime",iiurlwidth=400,format="json"))
d=json.loads(get(api)); out=[]
for p in sorted(d.get("query",{}).get("pages",{}).values(),key=lambda p:p.get("index",0)):
    ii=p["imageinfo"][0]; m=ii.get("extmetadata",{})
    lic=m.get("LicenseShortName",{}).get("value","?"); art=re.sub("<[^>]+>","",m.get("Artist",{}).get("value","?"))[:40]
    out.append(dict(t=p["title"],w=ii["width"],h=ii["height"],mime=ii["mime"],lic=lic,art=art.strip(),thumb=ii.get("thumburl"),url=ii["url"]))
json.dump(out,open(f"{D}/{tag}.json","w"),ensure_ascii=False,indent=1)
ims=[]
for i,o in enumerate(out):
    print(i,o["w"],"x",o["h"],o["mime"],"|",o["lic"],"|",o["art"],"|",o["t"][5:70])
    try: im=Image.open(io.BytesIO(get(o["thumb"]))).convert("RGB"); im.thumbnail((300,200))
    except Exception as e: im=Image.new("RGB",(300,200),"gray")
    ims.append(im)
cols=4; s=Image.new("RGB",(cols*305,((len(ims)+cols-1)//cols)*225),"white"); dr=ImageDraw.Draw(s)
for i,im in enumerate(ims):
    x,y=(i%cols)*305,(i//cols)*225; s.paste(im,(x,y)); dr.text((x+3,y+203),str(i),fill="red")
s.save(f"{D}/{tag}.jpg")
