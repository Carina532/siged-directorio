import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os, traceback
from datetime import datetime

app = Flask(__name__)

EXCEL_FILE = None
for f in os.listdir("."):
    if f.lower().endswith(".xlsx"):
        if "siged" in f.lower() or "directorio" in f.lower():
            EXCEL_FILE = f
            break
if not EXCEL_FILE:
    for f in os.listdir("."):
        if f.lower().endswith(".xlsx"):
            EXCEL_FILE = f
            break

def load_data():
    try:
        if not EXCEL_FILE or not os.path.exists(EXCEL_FILE):
            return pd.DataFrame(columns=["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRONICO","TELEFONO","DIRECCION","FECHA DE ACTUALIZACION"])
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        df = df.fillna("")
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"ERROR {e}")
        traceback.print_exc()
        return pd.DataFrame(columns=["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRONICO","TELEFONO","DIRECCION","FECHA DE ACTUALIZACION"])

TEMPLATE = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Directorio SIGED 2026 Secretarios, Enlaces y Operadores</title>
<style>
:root{--guinda:#621132;--oro:#b38e5d;--bg:#f6f2ee}*{font-family:Arial,sans-serif;box-sizing:border-box}
body{margin:0;background:var(--bg)}header{background:var(--guinda);color:white;padding:16px 24px;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:20}
.controls{background:white;padding:12px 20px;display:flex;flex-wrap:wrap;gap:8px;border-bottom:3px solid var(--guinda);position:sticky;top:68px;z-index:10;align-items:center}
select{padding:10px;border:1px solid #ccc;border-radius:8px;min-width:200px}
.btn{background:var(--guinda);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:700}
.btn-green{background:#0f5132}
table{width:100%;background:white;border-collapse:collapse}th{background:var(--guinda);color:white;padding:10px 6px;font-size:11px;text-transform:uppercase;position:sticky;top:0}
td{padding:8px;border-bottom:1px solid #eee;font-size:12px}td.editable{background:#fffbe6}
#toast{position:fixed;bottom:20px;right:20px;background:var(--guinda);color:white;padding:10px 16px;border-radius:8px;display:none}
</style></head><body>
<header><div style="width:36px;height:36px;background:white;color:var(--guinda);border-radius:50%;display:grid;place-items:center;font-weight:900">SEP</div>
<div><b>Directorio SIGED 2026 Secretarios, Enlaces y Operadores</b><br><small>{{file}} | {{count}} contactos</small></div>
<div style="margin-left:auto"><span id="status" style="background:rgba(255,255,255,.2);padding:6px 10px;border-radius:6px;font-size:11px">Listo</span></div></header>

<div class="controls">
<select id="fEnt"><option value="">Todas Entidades</option></select>
<select id="fRol"><option value="">Todos Roles</option></select>
<button class="btn btn-green" onclick="guardarExcel()">Guardar a Excel REAL</button>
<button class="btn" onclick="descargar()">Descargar</button>
<span id="cont" style="font-weight:800;color:var(--guinda);margin-left:auto"></span></div>

<div style="overflow:auto;padding:12px"><table><thead><tr>
<th>ENTIDAD</th><th>ROL</th><th>NOMBRE</th><th>PUESTO</th><th>CORREO</th><th>TEL</th><th>DIRECCION</th><th>FECHA</th>
</tr></thead><tbody id="tbody"></tbody></table></div>
<div id="toast"></div>
<script>
let DATA = {{data_json|safe}}; let filtrados=[]; let cambios={};
const tbody=document.getElementById('tbody'), fEnt=document.getElementById('fEnt'), fRol=document.getElementById('fRol'), cont=document.getElementById('cont'), statusEl=document.getElementById('status');
const cols = Object.keys(DATA[0]||{});
function colNombre(){ return cols.find(c=>c.includes('NOMBRE'))||'NOMBRE' }
function colCorreo(){ return cols.find(c=>c.includes('CORREO'))||'CORREO ELECTRONICO' }
function colTel(){ return cols.find(c=>c.includes('TEL'))||'TELEFONO' }
function colEnt(){ return cols.find(c=>c.includes('ENTIDAD'))||'ENTIDAD' }
function colRol(){ return cols.find(c=>c.includes('ROL'))||'ROL SIGED' }
function colDir(){ return cols.find(c=>c.includes('DIRECC'))||'DIRECCION' }
[...new Set(DATA.map(d=>d[colEnt()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fEnt.appendChild(o)});
[...new Set(DATA.map(d=>d[colRol()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fRol.appendChild(o)});
function render(){
 let ent=fEnt.value, rol=fRol.value;
 filtrados=DATA.filter(r=>{ return (!ent||r[colEnt()]===ent) && (!rol||r[colRol()]===rol); });
 cont.textContent=filtrados.length+' contactos'; tbody.innerHTML='';
 filtrados.forEach(r=>{
  let idx=DATA.indexOf(r);
  let tr=document.createElement('tr');
  tr.innerHTML=`<td>${r[colEnt()]||''}</td><td>${r[colRol()]||''}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="${colNombre()}">${r[colNombre()]||''}</td>
  <td>${r[cols.find(c=>c.includes('PUESTO'))||'PUESTO']||''}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="${colCorreo()}">${r[colCorreo()]||''}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="${colTel()}">${r[colTel()]||''}</td>
  <td class="editable" contenteditable="true" data-idx="${idx}" data-field="${colDir()}">${(r[colDir()]||'').substring(0,80)}</td>
  <td>${r[cols.find(c=>c.includes('FECHA'))||'']||''}</td>`;
  tbody.appendChild(tr);
 });
}
document.addEventListener('input', e=>{
 if(e.target.classList.contains('editable')){
  let idx=e.target.dataset.idx, field=e.target.dataset.field;
  DATA[idx][field]=e.target.innerText;
  cambios[idx]=true;
  statusEl.textContent='Sin guardar * ('+Object.keys(cambios).length+')'; statusEl.style.background='#dc3545';
 }
});
function guardarExcel(){
 if(Object.keys(cambios).length===0){ toast('No hay cambios'); return; }
 statusEl.textContent='Guardando...';
 fetch('/guardar',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({cambios: DATA})})
.then(r=>r.json()).then(res=>{
  if(res.ok){ toast('Guardado: '+res.file); statusEl.textContent='Guardado'; statusEl.style.background='#198754'; cambios={}; }
  else toast('Error: '+res.error);
 });
}
function descargar(){ window.location='/descargar'; }
function toast(m){let t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3000);}
fEnt.addEventListener('change', render); fRol.addEventListener('change', render); render();
</script></body></html>
"""

@app.route("/")
def index():
    df = load_data()
    data_json = df.to_json(orient="records", force_ascii=False)
    return render_template_string(TEMPLATE, data_json=data_json, count=len(df), file=EXCEL_FILE or "SIN EXCEL")

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        data_list = payload.get("cambios", [])
        df_new = pd.DataFrame(data_list)
        df_new.to_excel(EXCEL_FILE, index=False)
        return jsonify({"ok": True, "file": EXCEL_FILE})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

@app.route("/descargar")
def descargar():
    df = load_data()
    tmp = "/tmp/descarga.xlsx"
    df.to_excel(tmp, index=False)
    return send_file(tmp, as_attachment=True, download_name="Directorio_SIGED_2026.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
