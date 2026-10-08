import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os, traceback
from datetime import datetime, timedelta

app = Flask(__name__)
EDIT_PASSWORD = os.environ.get("EDIT_PASSWORD", "SIGED2026")
EDITOR_LOCK = {"user": None, "time": None}

EXCEL_FILE = None
for f in os.listdir("."):
    if f.lower().endswith(".xlsx"):
        if "siged" in f.lower() or "directorio" in f.lower():
            EXCEL_FILE = f; break
if not EXCEL_FILE:
    for f in os.listdir("."):
        if f.lower().endswith(".xlsx"):
            EXCEL_FILE = f; break

def load_data():
    if not EXCEL_FILE or not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(columns=["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRONICO","TELEFONO","DIRECCION","FECHA DE ACTUALIZACION"])
    df = pd.read_excel(EXCEL_FILE, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

TEMPLATE = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Directorio SIGED 2026</title>
<style>
:root{--guinda:#621132;--bg:#f6f2ee}*{font-family:Arial,sans-serif;box-sizing:border-box}
body{margin:0;background:var(--bg)}header{background:var(--guinda);color:white;padding:16px 24px;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:20}
.controls{background:white;padding:12px 20px;display:flex;flex-wrap:wrap;gap:8px;border-bottom:3px solid var(--guinda);position:sticky;top:68px;z-index:10}
select, input[type=text]{padding:10px;border:1px solid #ccc;border-radius:8px;min-width:180px}
.btn{background:var(--guinda);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:700}
.btn-green{background:#0f5132}.btn-blue{background:#0d3b66}.btn:disabled{opacity:.4}
table{width:100%;background:white;border-collapse:collapse}th{background:var(--guinda);color:white;padding:10px 6px;font-size:11px;position:sticky;top:0}
td{padding:8px;border-bottom:1px solid #eee;font-size:12px}td.editable{background:#fffbe6;border:1px dashed #b38e5d}td.locked{pointer-events:none;background:#f5f5f5}
#toast{position:fixed;bottom:20px;right:20px;background:var(--guinda);color:white;padding:10px 16px;border-radius:8px;display:none;z-index:99}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);display:none;place-items:center;z-index:100}
.box{background:white;padding:24px;border-radius:12px;width:95%;max-width:500px}
.box input{width:100%;margin-bottom:10px}
</style></head><body>
<header><div style="width:36px;height:36px;background:white;color:var(--guinda);border-radius:50%;display:grid;place-items:center;font-weight:900">SEP</div>
<div><b>Directorio SIGED 2026 Secretarios, Enlaces y Operadores</b></div>
<div style="margin-left:auto;display:flex;gap:8px"><span id="lockStatus" style="background:rgba(255,255,255,.2);padding:6px 10px;border-radius:6px;font-size:11px">Solo lectura</span><button class="btn" style="background:white;color:var(--guinda)" onclick="solicitarEdicion()">🔒 Editar</button></div></header>

<div class="controls">
<select id="fEnt"><option value="">Todas Entidades</option></select>
<select id="fRol"><option value="">Todos Roles</option></select>
<button class="btn btn-blue" id="btnNuevo" onclick="abrirNuevo()" disabled>+ Nueva Entidad</button>
<button class="btn btn-green" id="btnGuardar" onclick="guardarExcel()" disabled>Guardar</button>
<button class="btn" onclick="descargar()">Descargar</button>
<span id="cont" style="font-weight:800;color:var(--guinda);margin-left:auto"></span></div>

<div style="overflow:auto;padding:12px"><table><thead><tr><th>ENTIDAD</th><th>ROL</th><th>NOMBRE</th><th>PUESTO</th><th>CORREO</th><th>TEL</th><th>DIRECCION</th><th>FECHA</th></tr></thead><tbody id="tbody"></tbody></table></div>

<div id="toast"></div>

<div id="lockModal" class="modal"><div class="box"><h3 style="color:var(--guinda);margin-top:0">Modo Edición - Solo 1 persona</h3><input id="passInput" type="password" placeholder="Contraseña"><div style="display:flex;gap:8px"><button class="btn btn-green" style="flex:1" onclick="confirmarEdicion()">Entrar</button><button class="btn" style="flex:1;background:#ccc;color:#333" onclick="cerrarModal('lockModal')">Cancelar</button></div><small>Por defecto: SIGED2026</small></div></div>

<div id="nuevoModal" class="modal"><div class="box"><h3 style="color:var(--guinda);margin-top:0">Agregar Nueva Entidad / Responsable</h3>
<input id="nEnt" type="text" placeholder="ENTIDAD (ej. NUEVA ENTIDAD)">
<input id="nRol" type="text" placeholder="ROL SIGED (ej. ENLACE SIGED, RESPONSABLE)">
<input id="nNom" type="text" placeholder="NOMBRE">
<input id="nPue" type="text" placeholder="PUESTO">
<input id="nCor" type="text" placeholder="CORREO ELECTRONICO">
<input id="nTel" type="text" placeholder="TELEFONO">
<input id="nDir" type="text" placeholder="DIRECCION">
<div style="display:flex;gap:8px"><button class="btn btn-green" style="flex:1" onclick="agregarFila()">Agregar</button><button class="btn" style="flex:1;background:#ccc;color:#333" onclick="cerrarModal('nuevoModal')">Cancelar</button></div>
</div></div>

<script>
let DATA={{data_json|safe}}; let cambios={}; let puedeEditar=false; let token=null;
const tbody=document.getElementById('tbody'), fEnt=document.getElementById('fEnt'), fRol=document.getElementById('fRol'), cont=document.getElementById('cont'), btnGuardar=document.getElementById('btnGuardar'), btnNuevo=document.getElementById('btnNuevo'), lockStatus=document.getElementById('lockStatus');
const cols=Object.keys(DATA[0]||{}); function col(n){return cols.find(c=>c.toUpperCase().includes(n))||n}
function colEnt(){return col('ENTIDAD')} function colRol(){return col('ROL')} function colNom(){return col('NOMBRE')} function colCor(){return col('CORREO')} function colTel(){return col('TEL')} function colDir(){return col('DIRECC')} function colPue(){return col('PUESTO')} function colFec(){return col('FECHA')}

function poblarFiltros(){
 fEnt.innerHTML='<option value="">Todas Entidades</option>'; fRol.innerHTML='<option value="">Todos Roles</option>';
 [...new Set(DATA.map(d=>d[colEnt()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fEnt.appendChild(o)});
 [...new Set(DATA.map(d=>d[colRol()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fRol.appendChild(o)});
}
function render(){
 let ent=fEnt.value, rol=fRol.value;
 let filtrados=DATA.filter(r=>(!ent||r[colEnt()]===ent)&&(!rol||r[colRol()]===rol));
 cont.textContent=filtrados.length+' contactos'; tbody.innerHTML='';
 filtrados.forEach(r=>{
  let idx=DATA.indexOf(r); let cls=puedeEditar?'editable':'locked'; let ce=puedeEditar;
  let tr=document.createElement('tr');
  tr.innerHTML=`<td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colEnt()}">${r[colEnt()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colRol()}">${r[colRol()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colNom()}">${r[colNom()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colPue()}">${r[colPue()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colCor()}">${r[colCor()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colTel()}">${r[colTel()]||''}</td>
  <td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colDir()}">${r[colDir()]||''}</td>
  <td>${r[colFec()]||''}</td>`;
  tbody.appendChild(tr);
 });
}
document.addEventListener('input',e=>{if(!puedeEditar)return;if(e.target.dataset.idx){let idx=e.target.dataset.idx,field=e.target.dataset.field;DATA[idx][field]=e.target.innerText;cambios[idx]=true;lockStatus.textContent='Editando *';lockStatus.style.background='#dc3545';}});
function solicitarEdicion(){document.getElementById('lockModal').style.display='grid';}
function cerrarModal(id){document.getElementById(id).style.display='none';}
function abrirNuevo(){document.getElementById('nuevoModal').style.display='grid';}
function agregarFila(){
 let nueva={}; nueva[colEnt()]=document.getElementById('nEnt').value; nueva[colRol()]=document.getElementById('nRol').value;
 nueva[colNom()]=document.getElementById('nNom').value; nueva[colPue()]=document.getElementById('nPue').value;
 nueva[colCor()]=document.getElementById('nCor').value; nueva[colTel()]=document.getElementById('nTel').value;
 nueva[colDir()]=document.getElementById('nDir').value; nueva[colFec()]=new Date().toLocaleDateString();
 if(!nueva[colEnt()]||!nueva[colNom()]){toast('Minimo Entidad y Nombre');return;}
 DATA.push(nueva); cambios[DATA.length-1]=true; cerrarModal('nuevoModal');
 document.getElementById('nEnt').value=''; document.getElementById('nNom').value=''; document.getElementById('nCor').value='';
 poblarFiltros(); render(); toast('Nueva entidad agregada. Dale a Guardar');
}
function confirmarEdicion(){let p=document.getElementById('passInput').value;fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p})}).then(r=>r.json()).then(res=>{if(res.ok){puedeEditar=true;token=res.token;cerrarModal('lockModal');lockStatus.textContent='🔓 Tu estas editando';lockStatus.style.background='#198754';btnGuardar.disabled=false;btnNuevo.disabled=false;render();toast('Modo edición. Ya puedes editar ENTIDAD y agregar nuevas');}else{toast(res.error);}});}
function guardarExcel(){fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cambios:DATA,token:token})}).then(r=>r.json()).then(res=>{if(res.ok){toast('Guardado en Excel');cambios={};}else toast(res.error);});}
function descargar(){window.location='/descargar';}
function toast(m){let t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3500);}
poblarFiltros(); render();
setInterval(()=>{if(puedeEditar)fetch('/heartbeat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});},30000);
</script></body></html>
"""

@app.route("/")
def index():
    df = load_data()
    return render_template_string(TEMPLATE, data_json=df.to_json(orient="records", force_ascii=False))

@app.route("/login", methods=["POST"])
def login():
    global EDITOR_LOCK
    data = request.get_json()
    if data.get("password")!= EDIT_PASSWORD:
        return jsonify({"ok": False, "error": "Contraseña incorrecta"})
    if EDITOR_LOCK["user"] and EDITOR_LOCK["time"]:
        if datetime.now() - EDITOR_LOCK["time"] < timedelta(minutes=15):
            if EDITOR_LOCK["user"]!= data.get("token") and EDITOR_LOCK.get("ip")!= request.remote_addr:
                 return jsonify({"ok": False, "error": f"Alguien más está editando. Espera."})
    token = os.urandom(8).hex()
    EDITOR_LOCK = {"user": token, "time": datetime.now(), "ip": request.remote_addr}
    return jsonify({"ok": True, "token": token})

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    if data.get("token") == EDITOR_LOCK.get("user"):
        EDITOR_LOCK["time"] = datetime.now()
    return jsonify({"ok": True})

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        if payload.get("token")!= EDITOR_LOCK.get("user"):
            return jsonify({"ok": False, "error": "No tienes el bloqueo"})
        df_new = pd.DataFrame(payload.get("cambios", []))
        df_new.to_excel(EXCEL_FILE, index=False)
        return jsonify({"ok": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

@app.route("/descargar")
def descargar_route():
    df = load_data()
    tmp = "/tmp/descarga.xlsx"
    df.to_excel(tmp, index=False)
    return send_file(tmp, as_attachment=True, download_name="Directorio_SIGED_2026.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))