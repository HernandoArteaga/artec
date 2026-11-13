"""Descarga los documentos públicos de un proceso SECOP II y extrae su texto."""
import json, urllib.request, urllib.parse, sys, os, subprocess, re
PROC = os.environ.get("PROCESO", "CO1.REQ.11319405")
NTC = os.environ.get("NOTICE", "CO1.NTC.11173956")
out_dir = f"secop/data/docs/{PROC}"; os.makedirs(out_dir, exist_ok=True)
log = []
def get(url, t=120):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=t) as r: return r.read(), r.headers.get("Content-Type", ""), r.geturl()
# 1) buscar datasets de archivos del SECOP II
cat = json.loads(get("https://www.datos.gov.co/api/catalog/v1?q=" + urllib.parse.quote("SECOP II archivos descarga") + "&limit=20")[0])
ids = [(r["resource"]["id"], r["resource"]["name"], r["resource"].get("columns_field_name")) for r in cat["results"]]
log.append({"datasets": ids})
docs = []
for did, name, cols in ids:
    if not cols or not any("proceso" in c for c in cols): continue
    pcol = [c for c in cols if "proceso" in c]
    for c in pcol:
        for val in (PROC, NTC):
            try:
                d = json.loads(get(f"https://www.datos.gov.co/resource/{did}.json?" + urllib.parse.urlencode({c: val, "$limit": 200}))[0])
            except Exception as e:
                continue
            if d:
                log.append({"dataset": did, "name": name, "col": c, "val": val, "n": len(d), "sample": d[0]})
                docs += d
    if docs: break
json.dump(docs, open(f"{out_dir}/documentos.json", "w"), ensure_ascii=False, indent=1)
# 2) descargar y extraer texto
for i, d in enumerate(docs):
    url = None
    for k, v in d.items():
        if isinstance(v, dict) and "url" in v: v = v["url"]
        if isinstance(v, str) and v.startswith("http") and ("Retrieve" in v or "Download" in v or "Archive" in v or "documento" in k):
            url = v; break
    nm = str(d.get("nombre_archivo") or d.get("nombre_del_documento") or d.get("titulo") or f"doc{i}")
    if not url: log.append({"sin_url": nm}); continue
    try:
        b, ct, final = get(url, 180)
    except Exception as e:
        log.append({"error": nm, "url": url, "e": str(e)}); continue
    safe = re.sub(r"[^\w.-]+", "_", nm)[:80]
    p = f"{out_dir}/{i:02d}_{safe}"
    open(p, "wb").write(b)
    if b[:4] == b"%PDF":
        subprocess.run(["pdftotext", "-layout", p, p + ".txt"])
        os.remove(p)
    elif b[:2] == b"PK":
        os.rename(p, p + ".zip")
    log.append({"ok": nm, "bytes": len(b), "ct": ct})
json.dump(log, open(f"{out_dir}/log.json", "w"), ensure_ascii=False, indent=1, default=str)
print(len(docs))
