import os, io, csv
import oracledb
from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)
oracledb.init_oracle_client = lambda: None

def get_conn():
    return oracledb.connect(
        user=os.getenv("CLOPEZ_TORAL"),
        password=os.getenv("CL0P3ZZZ_20*26"),
        dsn=os.getenv("172.31.36.20:1530/PRODSEP") # Ej: (description= (address=...)(connect_data=...))
    )

# ---- PLANTILLA IGUAL A TU FOTO ----
TEMPLATE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Directorio SIGED 2026</title>
<style>
body{margin:0;font-family:Arial;background:#f4f4f4}
.header{background:#5a0a1e;color:white;padding:12px 20px;display:flex;justify-content:space-between;align-items:center}
.header h1{margin:0;font-size:22px}
.badge{border:1px solid white;padding:6px 14px;border-radius:20px;font-size:13px}
.filters{background:white;padding:15px 20px;display:flex;gap:10px;align-items:center;border-bottom:4px solid #ddd}
select,button{padding:10px 14px;border-radius:8px;border:1px solid #ccc}
.btn-buscar{background:#a67c52;color:white;border:none;font-weight:bold}
.btn-desc{background:#2d0a12;color:white;border:none;font-weight:bold}
.table-wrap{background:white;margin:15px;padding:10px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#5a0a1e;color:white;padding:10px;text-align:left}
td{padding:8px;border-bottom:1px solid #eee;vertical-align:top}
.count{margin-left:auto;font-weight:bold;color:#5a0a1e}
.edit{display:none}
.admin.edit{display:inline-block}
</style></head><body>
<div class="header">
  <h1>SEP | Directorio SIGED 2026</h1>
  <div class="badge">{{ 'Admin - Edición' if is_admin else 'Solo lectura' }}</div>
</div>
<div class="filters">
  <select id="ent"><option value="">Todas Entidades</option>{% for e in entidades %}<option>{{e}}</option>{% endfor %}</select>
  <select id="rol"><option value="">Todos Roles</option>{% for r in roles %}<option>{{r}}</option>{% endfor %}</select>
  <button class="btn-buscar" onclick="cargar()">🔍 Buscar</button>
  <button class="btn-desc" onclick="window.location='/descargar?ent='+ent.value+'&rol='+rol.value">Descargar</button>
  <div class="count" id="count">{{total}} contactos</div>
</div>
<div class="table-wrap {{ 'admin' if is_admin else ''}}">
<table><thead><tr><th>ENTIDAD</th><th>ROL</th><th>NOMBRE</th><th>PUESTO</th><th>CORREO</th><th>TEL</th><th>DIRECCION</th><th>FECHA</th><th class="edit">HIST</th></tr></thead><tbody id="tbody"></tbody></table>
</div>
<script>
async function cargar(){
  let url=`/api/directorio?ent=${document.getElementById('ent').value}&rol=${document.getElementById('rol').value}`;
  let r=await fetch(url); let data=await r.json();
  document.getElementById('count').innerText=data.length+' contactos';
  let h=''; data.forEach(x=>{
    h+=`<tr><td>${x.ENTIDAD||''}</td><td>${x.ROL_SIGED||''}</td><td>${x.NOMBRE||''}</td><td>${x.PUESTO||''}</td><td>${x.CORREO||''}</td><td>${x.TEL||''}</td><td>${x.DIRECCION||''}</td><td>${x.FECHA_ALTA||''}</td>
    <td class="edit"><button onclick="verHist(${x.ID_DIRECTORIO})">Ver</button> <button onclick="editar(${x.ID_DIRECTORIO})">Editar</button></td></tr>`;
  }); document.getElementById('tbody').innerHTML=h;
}
async function verHist(id){ let r=await fetch('/api/historico/'+id); alert(JSON.stringify(await r.json(),null,2)); }
async function editar(id){
  let motivo=prompt('Motivo del cambio:'); if(!motivo)return;
  let nuevoPuesto=prompt('Nuevo puesto:'); if(!nuevoPuesto)return;
  await fetch('/api/editar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ID_DIRECTORIO:id,PUESTO:nuevoPuesto,MOTIVO_CAMBIO:motivo})});
  cargar();
}
cargar();
</script></body></html>
"""

@app.route("/")
def index():
    is_admin = request.args.get("admin") == "siged2026"
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT DISTINCT ENTIDAD FROM DIRECTORIO_SIGED WHERE ACTIVO=1 ORDER BY 1")
    entidades=[r[0] for r in cur.fetchall() if r[0]]
    cur.execute("SELECT DISTINCT ROL_SIGED FROM DIRECTORIO_SIGED WHERE ACTIVO=1 ORDER BY 1")
    roles=[r[0] for r in cur.fetchall() if r[0]]
    cur.execute("SELECT COUNT(*) FROM DIRECTORIO_SIGED WHERE ACTIVO=1")
    total=cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template_string(TEMPLATE, entidades=entidades, roles=roles, total=total, is_admin=is_admin)

@app.route("/api/directorio")
def api_dir():
    ent=request.args.get("ent",""); rol=request.args.get("rol","")
    conn=get_conn(); cur=conn.cursor()
    sql="""SELECT ID_DIRECTORIO, ENTIDAD, ROL_SIGED, NOMBRE, PUESTO, CORREO,
                  TELEFONO_1 || ' ' || EXTENSION AS TEL, DIRECCION, FECHA_ALTA
           FROM DIRECTORIO_SIGED WHERE ACTIVO=1"""
    params={}
    if ent: sql+=" AND ENTIDAD=:ent"; params["ent"]=ent
    if rol: sql+=" AND ROL_SIGED=:rol"; params["rol"]=rol
    sql+=" ORDER BY ENTIDAD, NOMBRE"
    cur.execute(sql, params)
    cols=[c[0] for c in cur.description]
    data=[dict(zip(cols,r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(data)

@app.route("/api/historico/<int:id_dir>")
def hist(id_dir):
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT ID_REGISTRO, VERSION, NOMBRE, PUESTO, ACTIVO, FECHA_INICIO, FECHA_FIN, MOTIVO_CAMBIO FROM DIRECTORIO_SIGED WHERE ID_DIRECTORIO=:id ORDER BY VERSION DESC", id=id_dir)
    cols=[c[0] for c in cur.description]
    data=[dict(zip(cols,r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(data)

@app.route("/api/editar", methods=["POST"])
def editar_api():
    d=request.json
    conn=get_conn(); cur=conn.cursor()
    cur.execute("UPDATE DIRECTORIO_SIGED SET ACTIVO=0, FECHA_FIN=SYSDATE WHERE ID_DIRECTORIO=:id AND ACTIVO=1", id=d['ID_DIRECTORIO'])
    cur.execute("""INSERT INTO DIRECTORIO_SIGED (ID_DIRECTORIO, ENTIDAD, ROL_SIGED, NOMBRE, PUESTO, CORREO, DIRECCION, TELEFONO_1, EXTENSION, CELULAR, FECHA_ALTA, ACTIVO, VERSION, FECHA_INICIO, MOTIVO_CAMBIO)
                   SELECT ID_DIRECTORIO, ENTIDAD, ROL_SIGED, NOMBRE, :pue, CORREO, DIRECCION, TELEFONO_1, EXTENSION, CELULAR, FECHA_ALTA, 1, VERSION+1, SYSDATE, :mot
                   FROM DIRECTORIO_SIGED WHERE ID_DIRECTORIO=:id ORDER BY VERSION DESC FETCH FIRST 1 ROWS ONLY""",
                pue=d.get('PUESTO'), mot=d.get('MOTIVO_CAMBIO'), id=d['ID_DIRECTORIO'])
    conn.commit(); cur.close(); conn.close()
    return jsonify({"ok":True})

@app.route("/descargar")
def descargar():
    # Mismo filtro que la vista
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT ENTIDAD, ROL_SIGED, NOMBRE, PUESTO, CORREO, TELEFONO_1, EXTENSION, DIRECCION FROM DIRECTORIO_SIGED WHERE ACTIVO=1 ORDER BY ENTIDAD")
    rows=cur.fetchall()
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(["ENTIDAD","ROL","NOMBRE","PUESTO","CORREO","TELEFONO","EXT","DIRECCION"])
    writer.writerows(rows)
    cur.close(); conn.close()
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=directorio_siged_2026.csv"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)