# AQS Rolling Mill ERP — FAST build (test)
# MASTER -> test folder/deploy : small index.html + encrypted data file + encrypted assets file (cached by the browser)
import os, re, sys, json, gzip, base64, hashlib, shutil, subprocess
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.environ.get("AQS_BASE") or os.path.dirname(HERE)
TOOLS=os.path.join(BASE,"tools"); SRC=os.path.join(BASE,"AQS Rolling mill.html")
OUT=os.path.join(HERE,"deploy"); ITER=250000
KEY=re.search(r'^KEY\s*=\s*["\'](.+?)["\']',open(os.path.join(TOOLS,"build_secure.py"),encoding="utf-8").read(),re.M).group(1)

def enc(plain,tag):
    # deterministic salt/iv from the content: same data -> same file name -> users keep their cached copy
    h=hashlib.sha256(tag+plain).digest(); salt=h[:16]; iv=hashlib.sha256(b"iv"+h).digest()[:12]
    k=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=ITER).derive(KEY.encode())
    blob=salt+iv+AESGCM(k).encrypt(iv,plain,None)
    return blob,hashlib.sha256(blob).hexdigest()[:10]

# 1) normal secure build (login page + Firebase module) into a temp file
tmp=os.path.join(HERE,"_tmp_index.html")
env=dict(os.environ,AQS_BASE=BASE,AQS_OUT=tmp)
r=subprocess.run([sys.executable,os.path.join(TOOLS,"build_secure.py")],env=env,capture_output=True,text=True)
if r.returncode: print(r.stdout,r.stderr); sys.exit("build_secure failed")
html=open(tmp,encoding="utf-8").read(); os.remove(tmp)
master=open(SRC,encoding="utf-8").read()

# 2) data payload (already gzip in the master) -> data-<hash>.bin
gz=base64.b64decode(re.search(r'<script id="gzdata"[^>]*>(.*?)</script>',master,re.S).group(1).strip())
dblob,dh=enc(gz,b"data")
g=re.search(r'<script id="gzdata"[^>]*>(.*?)</script>',html,re.S)
html=html[:g.start()]+'<script id="gzdata" type="text/plain"></script>'+html[g.end():]

# 3) performance dashboard + drawings -> assets-<hash>.bin (encrypted too — before they were public in index.html)
m=re.search(r'<script type="text/plain" id="perfdata">(.*?)</script>',html,re.S)
perf=base64.b64decode(m.group(1).strip()).decode("utf-8") if m else ""   # plain HTML compresses ~6x better than base64
if m: html=html[:m.start()]+'<script type="text/plain" id="perfdata"></script>'+html[m.end():]
dwg={}
for d in list(re.finditer(r'<script type="text/plain" class="aqs-dwg" data-code="([^"]+)">(.*?)</script>',html,re.S))[::-1]:
    dwg[d.group(1)]=d.group(2).strip(); html=html[:d.start()]+html[d.end():]
ablob,ah=enc(gzip.compress(json.dumps({"perf":perf,"dwg":dwg}).encode(),9,mtime=0),b"assets")

# 4) new loader: download starts as soon as the page opens (while the user signs in), decrypt, fill, boot
DATA=f"data-{dh}.bin"; ASSETS=f"assets-{ah}.bin"
loader=r'''<script>
document.getElementById('app').style.visibility='hidden';
window.__dashboardLoaded=false;
(function(){const get=u=>fetch(u).then(r=>{if(!r.ok)throw new Error('download '+u+' '+r.status);return r.arrayBuffer();});
  window.__binP=Promise.all([get('/__DATA__'),get('/__ASSETS__')]);window.__binP.catch(()=>{});})();
async function __dec(buf,key){const raw=new Uint8Array(buf);const salt=raw.slice(0,16),iv=raw.slice(16,28),ct=raw.slice(28);
  const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(key),{name:'PBKDF2'},false,['deriveKey']);
  const k=await crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:250000,hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['decrypt']);
  const gz=await crypto.subtle.decrypt({name:'AES-GCM',iv},k,ct);
  return JSON.parse(await new Response(new Blob([gz]).stream().pipeThrough(new DecompressionStream('gzip'))).text());}
window.__loadDashboard=async function(passphrase){
  if(window.__dashboardLoaded)return;
  const [db,ab]=await window.__binP;
  const [RAW,AS]=await Promise.all([__dec(db,passphrase),__dec(ab,passphrase)]);
  const pe=document.getElementById('perfdata');if(pe)pe.textContent=AS.perf?btoa(unescape(encodeURIComponent(AS.perf))):'';
  for(const c in (AS.dwg||{})){const s=document.createElement('script');s.type='text/plain';s.className='aqs-dwg';s.dataset.code=c;s.textContent=AS.dwg[c];document.body.appendChild(s);}
  boot(RAW);window.__dashboardLoaded=true;
};
</script>'''.replace('__DATA__',DATA).replace('__ASSETS__',ASSETS)
n0=len(html)
html=re.sub(r'<script>\s*document\.getElementById\(\'app\'\)\.style\.visibility=\'hidden\';\s*window\.__dashboardLoaded=false;.*?</script>',lambda _:loader,html,count=1,flags=re.S)
assert len(html)!=n0 and '__binP' in html, "loader not replaced"

# 5) write the deploy folder
if os.path.isdir(OUT):
    for f in os.listdir(OUT):
        if f.endswith(".bin"): os.remove(os.path.join(OUT,f))
os.makedirs(OUT,exist_ok=True)
for f in ["manifest.webmanifest","icon-192.png","icon-512.png","icon-maskable-512.png","apple-touch-icon.png","favicon-32.png","login-bg.jpg","og.png","robots.txt"]:
    p=os.path.join(BASE,"deploy",f)
    if os.path.exists(p): shutil.copy2(p,os.path.join(OUT,f))
open(os.path.join(OUT,"index.html"),"w",encoding="utf-8").write(html)
open(os.path.join(OUT,DATA),"wb").write(dblob); open(os.path.join(OUT,ASSETS),"wb").write(ablob)
hdr=open(os.path.join(BASE,"deploy","_headers"),encoding="utf-8").read().rstrip()+'''

/index.html
  Cache-Control: no-cache

/data-*
  Cache-Control: public, max-age=31536000, immutable
  Content-Type: application/octet-stream

/assets-*
  Cache-Control: public, max-age=31536000, immutable
  Content-Type: application/octet-stream
'''
open(os.path.join(OUT,"_headers"),"w",encoding="utf-8").write(hdr)
shutil.copy2(os.path.join(HERE,"sw.js"),os.path.join(OUT,"sw.js"))

# 6) self-test
def dec(b):
    s,i,c=b[:16],b[16:28],b[28:]
    k=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=s,iterations=ITER).derive(KEY.encode())
    return json.loads(gzip.decompress(AESGCM(k).decrypt(i,c,None)))
p=dec(dblob); a=dec(ablob)
kb=lambda f:round(os.path.getsize(os.path.join(OUT,f))/1048576,2)
print(f"index.html {kb('index.html')} MB | {DATA} {kb(DATA)} MB | {ASSETS} {kb(ASSETS)} MB")
print("self-test OK — bom rows:",len(p['brows']),"| drawings:",len(a['dwg']),"| perf:",len(a['perf'])>0)
print("Upload the whole 'test folder\\deploy' folder.")
