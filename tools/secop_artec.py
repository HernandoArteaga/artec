"""Consulta SECOP II (datos.gov.co, p6dx-8zbt) y filtra procesos abiertos afines a ARTEC HIDRO."""
import json, urllib.request, urllib.parse, datetime, re, sys, os
API = "https://www.datos.gov.co/resource/p6dx-8zbt.json"
def q(params):
    url = API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=120) as r:
        return json.load(r)
out = {"generado": datetime.datetime.utcnow().isoformat()+"Z"}
sample = q({"$limit": 1, "$order": ":id"})
out["campos"] = sorted(sample[0].keys()) if sample else []
now = (datetime.datetime.utcnow() - datetime.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S")
KW = ["HIDROL", "HIDRAUL", "HIDRÁUL", "PRESA", "EMBALSE", "REPRESA", "INUNDAC", "SOCAVAC", "TORRENCIAL",
      "CUENCA", "POMCA", "ACUEDUCTO", "ALCANTARILL", "DRENAJE", "PLUVIAL", "PTAR", "PTAP", "BOCATOMA",
      "GESTION DEL RIESGO", "GESTIÓN DEL RIESGO", "EROSION", "EROSIÓN", "JARILL", "DIQUE", "HIDROELECTR",
      "PCH", "HIDROMETEOR", "CAUCE", "RONDA HIDRICA", "RONDA HÍDRICA", "QUEBRADA", " RIO ", " RÍO ", "MURO DE CONTENCION",
      "MURO DE CONTENCIÓN", "ESTABILIZACI", "GEOTECN", "BATIMETR", "SEDIMENT", "CANAL", "DISTRITO DE RIEGO", "RIEGO", "AGUA POTABLE",
      "SANEAMIENTO", "PLAN MAESTRO", "MITIGACI", "AMENAZA", "VULNERABILIDAD", "PUENTE", "FOTOVOLTA", "SOLAR"]
where = f"fecha_de_recepcion_de >= '{now}'"
rows, off = [], 0
try:
    while True:
        b = q({"$where": where, "$limit": 5000, "$offset": off, "$order": "fecha_de_recepcion_de ASC"})
        rows += b; off += 5000
        if len(b) < 5000 or off > 60000: break
    out["modo"] = "abiertos por fecha_de_recepcion_de"
except Exception as e:
    out["error_abiertos"] = str(e)
    rows = q({"$limit": 20000, "$order": "fecha_de_publicacion_del DESC"})
    out["modo"] = "ultimos 20000 publicados"
out["total_consultados"] = len(rows)
def txt(r): return " " + " ".join(str(r.get(k, "")) for k in ("nombre_del_procedimiento", "descripci_n_del_procedimiento")).upper() + " "
hits = []
for r in rows:
    t = txt(r)
    m = sorted({k.strip() for k in KW if k in t})
    if m:
        u = r.get("urlproceso"); u = u.get("url") if isinstance(u, dict) else u
        hits.append({"kw": m, "entidad": r.get("entidad"), "depto": r.get("departamento_entidad"), "ciudad": r.get("ciudad_entidad"),
            "ref": r.get("referencia_del_proceso"), "id": r.get("id_del_proceso"), "nombre": r.get("nombre_del_procedimiento"),
            "desc": (r.get("descripci_n_del_procedimiento") or "")[:700], "precio": r.get("precio_base"),
            "modalidad": r.get("modalidad_de_contratacion"), "tipo": r.get("tipo_de_contrato"), "fase": r.get("fase"),
            "estado": r.get("estado_del_procedimiento"), "estado_resumen": r.get("estado_resumen"),
            "publicado": r.get("fecha_de_publicacion_del"), "cierre": r.get("fecha_de_recepcion_de"),
            "unspsc": r.get("codigo_principal_de_categoria"), "duracion": f"{r.get('duracion','')} {r.get('unidad_de_duracion','')}", "url": u})
out["coincidencias"] = len(hits)
out["procesos"] = hits
os.makedirs("secop/data", exist_ok=True)
json.dump(out, open("secop/data/consulta-artec.json", "w"), ensure_ascii=False, indent=1)
print(out["modo"], out["total_consultados"], out["coincidencias"])
