import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os, traceback
from datetime import datetime, timedelta

app = Flask(__name__)
EDIT_PASSWORD = os.environ.get("EDIT_PASSWORD", "siged2027")
ADMIN_KEY = EDIT_PASSWORD
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

def get_col_name(df, keyword):
    for c in df.columns:
        if keyword.upper() in str(c).upper():
            return c
    return None

def clean_df(df):
    if df.empty:
        return df
    df = df.astype(str)
    for col in df.columns:
        df[col] = df[col].replace(['nan','None','0','0.0'], '')
        df[col] = df[col].str.strip()
    col_ent = get_col_name(df, 'ENTIDAD')
    col_nom = get_col_name(df, 'NOMBRE')
    if col_ent and col_nom:
        df = df[~((df[col_ent] == '') & (df[col_nom] == ''))]
        df = df[df[col_nom]!= '']
        df = df[df[col_ent]!= '']
    df = df[~(df == '').all(axis=1)]
    return df.reset_index(drop=True)

def load_data():
    if not EXCEL_FILE or not os.path.exists(EXCEL_FILE): return pd.DataFrame()
    df = pd.read_excel(EXCEL_FILE, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    df = clean_df(df)
    return df

TEMPLATE = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Directorio SIGED {{year}}</title>
<style>:root{--guinda:#621132}*{font-family:Arial,sans-serif;box-sizing:border-box}body{margin:0;background:#f6f2ee}header{background:var(--guinda);color:white;padding:16px 24px;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:20}
.controls{background:white;padding:12px 20px;display:flex;flex-wrap:wrap;gap:8px;border-bottom:3px solid var(--guinda);position:sticky;top:68px;z-index:10}select{padding:10px;border:1px solid #ccc;border-radius:8px;min-width:180px}.btn{background:var(--guinda);color:white;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;font-weight:700}.btn-green{background:#0f5132}.btn-blue{background:#0d3b66}.btn-search{background:#b38e5d}.btn-gray{background:#6c757d}.btn:disabled{opacity:.4}table{width:100%;background:white;border-collapse:collapse}th{background:var(--guinda);color:white;padding:10px 6px;font-size:11px}td{padding:8px;border-bottom:1px solid #eee;font-size:12px}td.editable{background:#fffbe6;border:1px dashed #b38e5d}#toast{position:fixed;bottom:20px;right:20px;background:var(--guinda);color:white;padding:10px 16px;border-radius:8px;display:none;z-index:99}.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);display:none;place-items:center;z-index:100}.box{background:white;padding:24px;border-radius:12px;width:95%;max-width:480px}.box input{width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:8px}</style></head><body>
<header><div style="width:36px;height:36px;background:white;color:var(--guinda);border-radius:50%;display:grid;place-items:center;font-weight:900">SEP</div><div><b>Directorio SIGED {{year}}</b></div><div style="margin-left:auto;display:flex;gap:8px;align-items:center"><span id="lockStatus" style="background:rgba(255,255,255,.2);padding:6px 10px;border-radius:6px;font-size:11px">{% if is_admin %}Modo Admin{% else %}Solo lectura{% endif %}</span>{% if is_admin %}<button class="btn" style="background:white;color:var(--guinda)" onclick="solicitarEdicion()">🔒 Editar</button><button class="btn btn-gray" onclick="salirEdicion()">🚪 Salir</button>{% endif %}</div></header>
<div class="controls"><select id="fEnt"><option value="">Todas Entidades</option></select><select id="fRol"><option value="">Todos Roles</option></select><button class="btn btn-search" onclick="buscar()">🔍 Buscar</button>{% if is_admin %}<button class="btn btn-blue" id="btnNuevo" onclick="abrirNuevo()" disabled>+ Nueva Entidad</button><button class="btn btn-green" id="btnGuardar" onclick="guardarExcel()" disabled>Guardar</button>{% endif %}<button class="btn" onclick="descargar()">Descargar</button><span id="cont" style="font-weight:800;color:var(--guinda);margin-left:auto"></span></div>
<div style="overflow:auto;padding:12px"><table><thead><tr><th>ENTIDAD</th><th>ROL</th><th>NOMBRE</th><th>PUESTO</th><th>CORREO</th><th>TEL</th><th>DIRECCION</th><th>FECHA</th></tr></thead><tbody id="tbody"></tbody></table></div><div id="toast"></div>
<div id="lockModal" class="modal"><div class="box"><h3 style="color:var(--guinda);margin-top:0">Contraseña</h3><input id="passInput" type="password" placeholder="siged2027"><div style="display:flex;gap:8px"><button class="btn btn-green" style="flex:1" onclick="confirmarEdicion()">Entrar</button><button class="btn" style="flex:1;background:#ccc;color:#333" onclick="cerrarModal('lockModal')">Cancelar</button></div></div></div>
<div id="nuevoModal" class="modal"><div class="box"><h3 style="color:var(--guinda);margin-top:0">Agregar Nueva Entidad</h3><input id="nEnt" placeholder="ENTIDAD"><input id="nRol" placeholder="ROL SIGED"><input id="nNom" placeholder="NOMBRE"><input id="nPue" placeholder="PUESTO"><input id="nCor" placeholder="CORREO"><input id="nTel" placeholder="TELEFONO"><input id="nDir" placeholder="DIRECCION"><div style="display:flex;gap:8px"><button class="btn btn-green" style="flex:1" onclick="agregarFila()">Agregar</button><button class="btn" style="flex:1;background:#ccc;color:#333" onclick="cerrarModal('nuevoModal')">Cancelar</button></div></div></div>
<script>
let DATA={{data_json|safe}}; let cambios={}; let puedeEditar=false; let token=null; let IS_ADMIN={{'true' if is_admin else 'false'}};
const tbody=document.getElementById('tbody'), fEnt=document.getElementById('fEnt'), fRol=document.getElementById('fRol'), cont=document.getElementById('cont');
const cols=Object.keys(DATA[0]||{}); function col(n){return cols.find(c=>c.toUpperCase().includes(n))||n}
function colEnt(){return col('ENTIDAD')} function colRol(){return col('ROL')} function colNom(){return col('NOMBRE')} function colCor(){return col('CORREO')} function colTel(){return col('TEL')} function colDir(){return col('DIRECC')} function colPue(){return col('PUESTO')} function colFec(){return col('FECHA')}
function poblarFiltros(){ fEnt.innerHTML='<option value="">Todas Entidades</option>'; fRol.innerHTML='<option value="">Todos Roles</option>'; [...new Set(DATA.map(d=>d[colEnt()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fEnt.appendChild(o)}); [...new Set(DATA.map(d=>d[colRol()]))].filter(Boolean).sort().forEach(e=>{let o=document.createElement('option');o.value=e;o.textContent=e;fRol.appendChild(o)});}
function render(){ let ent=fEnt.value, rol=fRol.value; let filtrados=DATA.filter(r=>(!ent||r[colEnt()]===ent)&&(!rol||r[colRol()]===rol)); cont.textContent=filtrados.length+' contactos'; tbody.innerHTML=''; filtrados.forEach(r=>{ let idx=DATA.indexOf(r); let cls=(IS_ADMIN&&puedeEditar)?'editable':''; let ce=(IS_ADMIN&&puedeEditar); let tr=document.createElement('tr'); tr.innerHTML=`<td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colEnt()}">${r[colEnt()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colRol()}">${r[colRol()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colNom()}">${r[colNom()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colPue()}">${r[colPue()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colCor()}">${r[colCor()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colTel()}">${r[colTel()]||''}</td><td class="${cls}" contenteditable="${ce}" data-idx="${idx}" data-field="${colDir()}">${r[colDir()]||''}</td><td>${r[colFec()]||''}</td>`; tbody.appendChild(tr);});}
function buscar(){ render(); toast('Filtro: '+(fEnt.value||'Todas')+' - '+(fRol.value||'Todos'));}
document.addEventListener('input',e=>{if(!puedeEditar||!IS_ADMIN)return;if(e.target.dataset.idx){DATA[e.target.dataset.idx][e.target.dataset.field]=e.target.innerText;cambios[e.target.dataset.idx]=true;}});
function solicitarEdicion(){document.getElementById('lockModal').style.display='grid';}function cerrarModal(id){document.getElementById(id).style.display='none';}function abrirNuevo(){document.getElementById('nuevoModal').style.display='grid';}
function agregarFila(){ let nueva={}; nueva[colEnt()]=document.getElementById('nEnt').value.trim(); nueva[colRol()]=document.getElementById('nRol').value.trim(); nueva[colNom()]=document.getElementById('nNom').value.trim(); nueva[colPue()]=document.getElementById('nPue').value.trim(); nueva[colCor()]=document.getElementById('nCor').value.trim(); nueva[colTel()]=document.getElementById('nTel').value.trim(); nueva[colDir()]=document.getElementById('nDir').value.trim(); nueva[colFec()]=new Date().toLocaleDateString(); if(!nueva[colEnt()]||!nueva[colNom()]){toast('Minimo Entidad y Nombre');return;} DATA.push(nueva); cambios[DATA.length-1]=true; document.getElementById('nEnt').value='';document.getElementById('nRol').value='';document.getElementById('nNom').value='';document.getElementById('nPue').value='';document.getElementById('nCor').value='';document.getElementById('nTel').value='';document.getElementById('nDir').value=''; cerrarModal('nuevoModal'); poblarFiltros(); fEnt.value=nueva[colEnt()]; render(); toast('Agregada. Ahora dale Guardar');}
function confirmarEdicion(){let p=document.getElementById('passInput').value;fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p, admin_key:'{{admin_key}}'})}).then(r=>r.json()).then(res=>{if(res.ok){puedeEditar=true;token=res.token;cerrarModal('lockModal');document.getElementById('lockStatus').textContent='🔓 Editando';document.getElementById('btnGuardar').disabled=false;document.getElementById('btnNuevo').disabled=false;render();toast('Modo edición')}else{toast(res.error);}});}
function guardarExcel(){fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cambios:DATA,token:token})}).then(r=>r.json()).then(res=>{if(res.ok){toast('Guardado sin huecos ✅');}else toast(res.error);});}
function salirEdicion(){ fetch('/logout',{method:'POST'}).then(()=>{ window.location.href = window.location.origin + window.location.pathname; }); }
function descargar(){window.location='/descargar';}function toast(m){let t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3500);}poblarFiltros(); render();
</script></body></html>
"""

@app.route("/")
def index():
    df = load_data()
    admin_param = request.args.get("admin", "")
    is_admin = admin_param == ADMIN_KEY
    year = datetime.now().year
    return render_template_string(TEMPLATE, data_json=df.to_json(orient="records", force_ascii=False), is_admin=is_admin, admin_key=admin_param, year=year)

@app.route("/login", methods=["POST"])
def login():
    global EDITOR_LOCK
    data = request.get_json()
    if data.get("password")!= EDIT_PASSWORD or data.get("admin_key")!= ADMIN_KEY:
        return jsonify({"ok": False, "error": "No autorizado"})
    token = os.urandom(8).hex()
    EDITOR_LOCK = {"user": token, "time": datetime.now()}
    return jsonify({"ok": True, "token": token})

@app.route("/logout", methods=["POST"])
def logout():
    global EDITOR_LOCK
    EDITOR_LOCK = {"user": None, "time": None}
    return jsonify({"ok": True})

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        if payload.get("token")!= EDITOR_LOCK.get("user"):
            return jsonify({"ok": False, "error": "No permiso o sesión expirada"})
        df_new = pd.DataFrame(payload.get("cambios", []))
        df_new = clean_df(df_new)
        df_new.to_excel(EXCEL_FILE, index=False)
        return jsonify({"ok": True})
    except Exception as e:
        traceback.print_exc(); return jsonify({"ok": False, "error": str(e)})

@app.route("/descargar")
def descargar_route():
    df = load_data()
    tmp = "/tmp/descarga.xlsx"
    df.to_excel(tmp, index=False)
    return send_file(tmp, as_attachment=True, download_name=f"Directorio_SIGED_{datetime.now().year}.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))