// AQS Rolling Mill — service worker (makes the site installable as an app; always loads the newest version when online)
const CACHE='aqs-rm-v1';
const SHELL=['/','/manifest.webmanifest','/icon-192.png','/icon-512.png','/icon-maskable-512.png','/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).catch(()=>{}));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;   // Firebase / Google calls go straight to the network
  if(r.mode==='navigate'){   // the page: network first (newest data), cached copy only when offline
    e.respondWith(fetch(r).then(res=>{const c=res.clone();caches.open(CACHE).then(x=>x.put('/',c));return res;}).catch(()=>caches.match('/').then(m=>m||new Response('<h2 style="font-family:sans-serif">AQS Rolling Mill — you are offline</h2><p style="font-family:sans-serif">Connect to the network and open the app again.</p>',{headers:{'Content-Type':'text/html'}}))));return;}
  e.respondWith(caches.match(r).then(m=>m||fetch(r)));});
