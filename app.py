import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os, traceback
from datetime import datetime, timedelta

app = Flask(__name__)

# CONFIGURACION DE SEGURIDAD
EDIT_PASSWORD = os.environ.get("EDIT_PASSWORD", "SIGED2026") # <-- CAMBIA AQUI TU CONTRASEÑA
EDITOR_LOCK = {"user": None, "time": None}

EXCEL_FILE = None
for f in os.listdir("."):
    if f.lower().endswith(".xlsx") and ("siged" in f.lower() or "directorio" in f.lower()):
        EXCEL_FILE = f; break
if not EXCEL_FILE:
    for f in os.listdir("."):
        if f.lower().endswith(".xlsx"):
            EXCEL_FILE = f; break

def load_data():
    if not EXCEL_FILE or not os.path.exists(EXCEL_FILE): return pd.DataFrame()
    df = pd.read_excel(EXCEL_FILE, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

TEMPLATE = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Directorio SIGED 2026 Secretarios, Enlaces y Operadores</title>
<style>
:root{--guinda:#621132;--oro:#b38e5d;--bg:#f6f2ee}*{font-family:Arial,sans-serif;box-sizing:border-box}
body{margin:0;background:var(--bg)}header{background:var(--guinda);color:white;padding:16px 24px;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:20}
.controls{background:white;padding:12px 20px;display:flex;flex-wrap:wrap;gap:8px;border-bottom:3px solid var(--guinda);position:sticky;top:68px;z-index:10;align-items:center}
select{padding:10px;border:1px solid #ccc;border-radius:8px;min-width:200px}
.btn{background:var(--guinda);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:700}
.btn-green{background:#0f5132}.btn:disabled{opacity:0.4;cursor:not-allowed}
table{width:100%;background:white;border-collapse:collapse}th{background:var(--guinda);color:white;padding:10px 6px;font-size:11px;text-transform:uppercase}
td{padding:8px;border-bottom:1px solid #eee;font-size:12px}td.editable{background:#fffbe6}td.locked{background:#eee;pointer-events:none}
#toast{position:fixed;bottom:20px;right:20px;background:var(--guinda);color:white;padding:10px 16px;border-radius:8px;display:none;z-index:99}
#lockModal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);display:none;place-items:center;z-index:100}
#lockBox{background:white;padding:24px;border-radius:12px;width:90%;max-width:380px}
</style></head><body>
<header><div style="width:36px;height:36px;background:white;color:var(--guinda);border-radius:50%;display:grid;place-items:center;font-weight:900">SEP</div>
<div><b>Directorio SIGED 2026 Secretarios, Enlaces y Operadores</b></div>
<div style="margin-left:auto;display:flex;gap:8px"><span id="lockStatus" style="background:rgba(255,255,255,.2);padding:6px 10px;border-radius:6px;font-size:11px">Solo lectura</span><button class="btn" style="background:white;color:var(--guinda)" onclick="solicitarEdicion()">🔒 Editar</button></div></header>
<div class="controls">
<select id="fEnt"><option value="">Todas Entidades</option></select>
<select id="fRol"><option value="">Todos Roles</option></select>
<button class="btn btn-green" id="btnGuardar" onclick="guardarExcel()" disabled>Guardar</button>
<button class="btn" onclick="descargar()">Descargar</button>
<span id="cont" style="font-weight:800;color:var(--guinda);margin-left:auto"></span></div>
<div style="overflow:auto;padding:12px"><table><thead><tr><th>ENTIDAD</th><th>ROL</th><th>NOMBRE</th><th>PUESTO</th><th>CORREO</th><th>TEL</th><th>DIRECCION</th><th>FECHA</th></tr></thead><tbody id="tbody"></tbody></table></div>
<div id="toast"></div>
<div id="lockModal"><div id="lockBox"><h3 style="margin-top:0;color:var(--guinda)">Modo Edición - Solo 1 persona</h3><p style="font-size:13px">Ingresa la contraseña para editar. Solo una persona puede editar a la vez.</p><input id="passInput" type="password" placeholder="Contraseña" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px"><div style="display:flex;gap:8px;margin-top:12px"><button class="btn btn-green" style="flex:1" onclick="confirmarEdicion()">Entrar</button><button class="btn" style="flex:1;background:#ccc;color:#333" onclick="cerrarModal()">Cancelar</button></div><small style="color:#666">Contraseña por defecto: SIGED2026 (la puedes cambiar en Render)</small></div></div>
<script>
let DATA={{data_json|safe}}; let filtrados=[]; let cambios={}; let puedeEditar=false; let token=null;
const tbody=document.getElementById('tbody'), fEnt=document.getElementById('fEnt'), fRol=document.getElementById('fRol'), cont=document.getElementById('cont'), btnGuardar=document.getElementById('btnGuardar'), lockStatus=document.getElementById('lockStatus');
const cols=Object.keys(DATA[0]||{}); function col(n){return cols.find(c=>c.toUpperCase().includes(n))||n}
function colEnt(){return col('ENTIDAD')} function colRol(){return col('ROL')} function colNom(){return col('NOMBRE')} function colCor(){return col('CORREO')} function colTel(){return col('TEL')} function colDir(){return col('DIRECC')}
[...new Set(DATA.map(d=>d[colEnt()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fEnt.appendChild(o)});
[...new Set(DATA.map(d=>d[colRol()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fRol.appendChild(o)});
function render(){let ent=fEnt.value,rol=fRol.value;filtrados=DATA.filter(r=>(!ent||r[colEnt()]===ent)&&(!rol||r[colRol()]===rol));cont.textContent=filtrados.length+' contactos';tbody.innerHTML='';filtrados.forEach(r=>{let idx=DATA.indexOf(r);let tr=document.createElement('tr');let editableClass=puedeEditar?'editable':'locked';tr.innerHTML=`<td>${r[colEnt()]||''}</td><td>${r[colRol()]||''}</td><td class="${editableClass}" contenteditable="${puedeEditar}" data-idx="${idx}" data-field="${colNom()}">${r[colNom()]||''}</td><td>${r[col('PUESTO')]||''}</td><td class="${editableClass}" contenteditable="${puedeEditar}" data-idx="${idx}" data-field="${colCor()}">${r[colCor()]||''}</td><td class="${editableClass}" contenteditable="${puedeEditar}" data-idx="${idx}" data-field="${colTel()}">${r[colTel()]||''}</td><td class="${editableClass}" contenteditable="${puedeEditar}" data-idx="${idx}" data-field="${colDir()}">${(r[colDir()]||'').substring(0,80)}</td><td>${r[col('FECHA')]||''}</td>`;tbody.appendChild(tr);});}
document.addEventListener('input',e=>{if(!puedeEditar)return;if(e.target.classList.contains('editable')){let idx=e.target.dataset.idx,field=e.target.dataset.field;DATA[idx][field]=e.target.innerText;cambios[idx]=true;lockStatus.textContent='Editando * ('+Object.keys(cambios).length+')';lockStatus.style.background='#dc3545';btnGuardar.disabled=false;}});
function solicitarEdicion(){document.getElementById('lockModal').style.display='grid';}
function cerrarModal(){document.getElementById('lockModal').style.display='none';}
function confirmarEdicion(){let p=document.getElementById('passInput').value;fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p})}).then(r=>r.json()).then(res=>{if(res.ok){puedeEditar=true;token=res.token;cerrarModal();lockStatus.textContent='🔓 Tú estás editando';lockStatus.style.background='#198754';btnGuardar.disabled=false;render();toast('Modo edición activado. Solo tú puedes guardar.');}else{toast('Contraseña incorrecta o alguien más está editando: '+res.error);}});}
function guardarExcel(){if(!puedeEditar){toast('Debes entrar en modo edición');return;}if(Object.keys(cambios).length===0){toast('No hay cambios');return;}btnGuardar.textContent='Guardando...';fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cambios:DATA,token:token})}).then(r=>r.json()).then(res=>{btnGuardar.textContent='Guardar';if(res.ok){toast('Guardado correctamente');cambios={};}else toast('Error: '+res.error);});}
function descargar(){window.location='/descargar';}
function toast(m){let t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3500);}
fEnt.addEventListener('change',render);fRol.addEventListener('change',render);render();
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
    # Si hay alguien editando y no han pasado 15 min
    if EDITOR_LOCK["user"] and EDITOR_LOCK["time"]:
        if datetime.now() - EDITOR_LOCK["time"] < timedelta(minutes=15):
            if EDITOR_LOCK["user"]!= request.remote_addr:
                 return jsonify({"ok": False, "error": f"Ya está editando alguien desde hace {(datetime.now() - EDITOR_LOCK['time']).seconds//60} min. Espera 15 min."})
    token = os.urandom(8).hex()
    EDITOR_LOCK = {"user": token, "time": datetime.now(), "ip": request.remote_addr}
    return jsonify({"ok": True, "token": token})

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    global EDITOR_LOCK
    data = request.get_json()
    if data.get("token") == EDITOR_LOCK.get("user"):
        EDITOR_LOCK["time"] = datetime.now()
    return jsonify({"ok": True})

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        if payload.get("token")!= EDITOR_LOCK.get("user"):
            return jsonify({"ok": False, "error": "No tienes el bloqueo de edición. Dale a Editar de nuevo."})
        if payload.get("token"):
            EDITOR_LOCK["time"] = datetime.now()
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