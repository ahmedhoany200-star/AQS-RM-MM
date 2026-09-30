// AQS Rolling Mill — service worker v2 (fast build)
// page: network first (always newest) · data-*.bin / assets-*.bin: kept on the device, downloaded again only when their name changes
const CACHE='aqs-rm-v2';
const SHELL=['/manifest.webmanifest','/icon-192.png','/icon-512.png','/icon-maskable-512.png','/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).catch(()=>{}));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;
  if(/^\/(data|assets)-[0-9a-f]+\.bin$/.test(u.pathname)){
    e.respondWith(caches.open(CACHE).then(c=>c.match(r).then(m=>m||fetch(r).then(res=>{if(res.ok){const kind=u.pathname.split('-')[0];
      c.keys().then(ks=>ks.forEach(k=>{const p=new URL(k.url).pathname;if(p!==u.pathname&&p.startsWith(kind+'-')&&p.endsWith('.bin'))c.delete(k);}));
      c.put(r,res.clone());}return res;}))));return;}
  if(r.mode==='navigate'){
    e.respondWith(fetch(r).then(res=>{const c=res.clone();caches.open(CACHE).then(x=>x.put('/',c));return res;}).catch(()=>caches.match('/').then(m=>m||new Response('<h2 style="font-family:sans-serif">AQS Rolling Mill — you are offline</h2>',{headers:{'Content-Type':'text/html'}}))));return;}
  e.respondWith(caches.match(r).then(m=>m||fetch(r)));});
