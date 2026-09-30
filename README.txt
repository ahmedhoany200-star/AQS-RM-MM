AQS Rolling Mill ERP - FAST version (test)

build_fast.bat  -> builds "deploy" here from the MASTER (uses ..\tools\build_secure.py and its key; the key is NOT copied here)
deploy\         -> upload this WHOLE folder to Cloudflare Pages (same as the normal deploy folder)

What is different from the normal build
- index.html is 0.8 MB instead of 9.6 MB (only the app + login page)
- data-<code>.bin   = the encrypted data (5.2 MB, binary instead of text)
- assets-<code>.bin = the encrypted Performance dashboard + drawings (0.65 MB) - before they were readable inside index.html
- the download starts while the user is signing in
- the .bin files are kept by the browser / phone app; downloaded again ONLY when the data changes (new file name)
- Every update: run build_fast.bat, upload deploy\ (old .bin files are removed automatically)
