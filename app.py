import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_FILE = "Directorio SIGED 2026 Secretarios, Enlaces y Operadores.xlsx"
if not os.path.exists(EXCEL_FILE):
    for f in os.listdir("."):
        if "SIGED" in f.upper() and f.endswith(".xlsx"):
            EXCEL_FILE = f
            break

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(columns=["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRÓNICO","TELÉFONO","DIRECCIÓN","FECHA DE ACTUALIZACIÓN"])
    df = pd.read_excel(EXCEL_FILE, sheet_name=0, dtype=str)
    df = df.fillna("")
    return df

TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Directorio SIGED 2026 - Guinda Editable</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--guinda:#621132;--oro:#b38e5d;--bg:#f6f2ee}
*{font-family:Montserrat,sans-serif;box-sizing:border-box}
body{margin:0;background:var(--bg)}
header{background:var(--guinda);color:white;padding:16px 24px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:20}
.controls{background:white;padding:14px 24px;display:flex;flex-wrap:wrap;gap:10px;border-bottom:3px solid var(--guinda);position:sticky;top:72px;z-index:10}
input,select{padding:10px 12px;border:1px solid #ccc;border-radius:8px;min-width:160px}
.btn{background:var(--guinda);color:white;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:700}
.btn-oro{background:var(--oro)}
.btn-green{background:#0f5132}
table{width:100%;background:white;border-collapse:collapse}
th{background:var(--guinda);color:white;padding:10px 8px;font-size:11px;text-transform:uppercase;position:sticky;top:0}
td{padding:8px;border-bottom:1px solid #eee;font-size:12px}
td.editable{background:#fffbe6;cursor:text}
td.editable:focus{background:#fff3cd;outline:2px solid var(--oro)}
.badge{padding:3px 8px;border-radius:12px;font-size:10px;font-weight:700;display:inline-block}
.badge-SEC{background:var(--guinda);color:white}
.badge-ENL{background:#e8d5b7;color:var(--guinda)}
.badge-OPE{background:#d1e7dd;color:#0f5132}
#toast{position:fixed;bottom:20px;right:20px;background:var(--guinda);color:white;padding:12px 18px;border-radius:8px;display:none;z-index:99}
</style>
</head>
<body>
<header>
<div style="width:40px;height:40px;background:white;border-radius:50%;display:grid;place-items:center;color:var(--guinda);font-weight:900">SEP</div>
<div><b>Directorio SIGED 2026</b> - Edicion REAL a Excel<br><small id="infoFile">{{file}} | {{count}} contactos | Guarda directo al.xlsx del servidor</small></div>
<div style="margin-left:auto;text-align:right"><span id="status" style="background:rgba(255,255,255,0.2);padding:6px 10px;border-radius:6px;font-size:11px">Sin cambios</span></div>
</header>
<div class="controls">
<input id="q" placeholder="Buscar nombre, entidad, correo..." style="flex:1;min-width:240px">
<select id="fEnt"><option value="">Todas Entidades</option></select>
<select id="fRol"><option value="">Todos Roles</option></select>
<button class="btn btn-green" onclick="guardarExcel()">Guardar Cambios a Excel REAL</button>
<button class="btn" onclick="copiarCorreos()">Copiar Correos</button>
<button class="btn btn-oro" onclick="descargar()">Descargar Excel</button>
<span id="cont" style="font-weight:800;color:var(--guinda);padding:10px"></span>
</div>
<div style="overflow:auto;padding:16px">
<table id="tabla"><thead><tr>
<th>Entidad</th><th>Rol SIGED</th><th>Nombre</th><th>Puesto</th><th>Correo</th><th>Tel</th><th>Direccion</th><th>Fecha</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>
<div id="toast"></div>
<script>
let DATA = {{data_json|safe}};
let filtrados = [];
let cambios = {};
const tbody=document.getElementById('tbody'), q=document.getElementById('q'), fEnt=document.getElementById('fEnt'), fRol=document.getElementById('fRol'), cont=document.getElementById('cont'), statusEl=document.getElementById('status');

[...new Set(DATA.map(d=>d.ENTIDAD))].sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fEnt.appendChild(o)});
[...new Set(DATA.map(d=>d['ROL SIGED']))].sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fRol.appendChild(o)});

function render(){
 let filtro=q.value.toLowerCase(), ent=fEnt.value, rol=fRol.value;
 filtrados=DATA.filter(r=>{
  let txt=(r.ENTIDAD+' '+r['ROL SIGED']+' '+r.NOMBRE+' '+r['CORREO ELECTRÓNICO']).toLowerCase();
  return (!filtro||txt.includes(filtro)) && (!ent||r.ENTIDAD===ent) && (!rol||r['ROL SIGED']===rol);
 });
 cont.textContent=filtrados.length+' contactos';
 tbody.innerHTML='';
 filtrados.forEach(r=>{
  let idx=DATA.indexOf(r);
  let badgeClass=r['ROL SIGED'].includes('SECRETARIO')?'SEC':r['ROL SIGED'].includes('ENLACE')?'ENL':'OPE';
  let tr=document.createElement('tr');
  tr.innerHTML=`<td>${r.ENTIDAD}</td><td><span class="badge badge-${badgeClass}">${r['ROL SIGED']}</span></td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="NOMBRE">${r.NOMBRE}</td>
  <td>${r.PUESTO}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="CORREO ELECTRÓNICO">${r['CORREO ELECTRÓNICO']}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="TELÉFONO">${r['TELÉFONO']}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="DIRECCIÓN" style="font-size:10px;max-width:220px">${r['DIRECCIÓN']}</td>
  <td style="font-size:10px">${r['FECHA DE ACTUALIZACIÓN']||''}</td>`;
  tbody.appendChild(tr);
 });
}

document.addEventListener('input', e=>{
 if(e.target.classList.contains('editable')){
  let idx=e.target.dataset.idx, field=e.target.dataset.field;
  if(!cambios[idx]) cambios[idx]={};
  cambios[idx][field]=e.target.innerText;
  DATA[idx][field]=e.target.innerText;
  statusEl.textContent='Cambios sin guardar * ('+Object.keys(cambios).length+')';
  statusEl.style.background='#dc3545';
 }
});

function guardarExcel(){
 if(Object.keys(cambios).length===0){ toast('No hay cambios'); return; }
 statusEl.textContent='Guardando...';
 fetch('/guardar', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({cambios: DATA})})
.then(r=>r.json()).then(res=>{
  if(res.ok){
   toast('Guardado en '+res.file+' - '+res.count+' contactos');
   statusEl.textContent='Guardado en Excel REAL';
   statusEl.style.background='#198754';
   cambios={};
  } else { toast('Error: '+res.error); }
 });
}

function descargar(){ window.location='/descargar'; }
function copiarCorreos(){
 let correos=[...new Set(filtrados.map(r=>r['CORREO ELECTRÓNICO']).filter(c=>c.includes('@')))];
 navigator.clipboard.writeText(correos.join('; '));
 toast('Copiados '+correos.length+' correos');
}
function toast(msg){ let t=document.getElementById('toast'); t.textContent=msg; t.style.display='block'; setTimeout(()=>t.style.display='none',3000); }

q.addEventListener('input', render);
fEnt.addEventListener('change', render);
fRol.addEventListener('change', render);
render();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    df = load_data()
    data_json = df.to_json(orient="records", force_ascii=False)
    return render_template_string(TEMPLATE, data_json=data_json, count=len(df), file=EXCEL_FILE)

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        data_list = payload.get("cambios", [])
        if not data_list:
            return jsonify({"ok": False, "error": "Sin datos"})
        df_new = pd.DataFrame(data_list)
        cols = ["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRÓNICO","TELÉFONO","DIRECCIÓN","FECHA DE ACTUALIZACIÓN"]
        for c in cols:
            if c not in df_new.columns:
                df_new[c] = ""
        df_new = df_new[cols]
        df_new.to_excel(EXCEL_FILE, index=False, sheet_name="Hoja1")
        backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{EXCEL_FILE}"
        df_new.to_excel(backup, index=False)
        return jsonify({"ok": True, "file": EXCEL_FILE, "count": len(df_new), "backup": backup})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/descargar")
def descargar():
    df = load_data()
    tmp = "/tmp/directorio_descarga.xlsx"
    df.to_excel(tmp, index=False)
    return send_file(tmp, as_attachment=True, download_name=f"Directorio_SIGED_2026_EDITADO_{datetime.now().strftime('%Y-%m-%d')}.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))