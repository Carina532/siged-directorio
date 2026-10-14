import os
import oracledb
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Conexión Oracle - Modo Thin (no necesita Oracle Client)
def get_conn():
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASS")
    dsn = os.getenv("DB_DSN")
    if not user or not pw or not dsn:
        raise Exception("Faltan variables DB_USER / DB_PASS / DB_DSN en Render")
    return oracledb.connect(user=user, password=pw, dsn=dsn)

TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Directorio SIGED 2026</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background:#f6f6; }
.header { background:#611232; color:white; padding:20px; }
.card { border-radius:12px; }
</style>
</head>
<body>
<div class="header">
  <h3 class="m-0">SEP | Directorio SIGED 2026</h3>
  <small>siged-directorio.onrender.com - Live</small>
</div>
<div class="container mt-4">
  <div class="card shadow-sm p-3">
    <div class="row g-2">
      <div class="col-md-4"><input id="q" class="form-control" placeholder="Buscar por nombre, área, correo..."></div>
      <div class="col-md-2"><button class="btn btn-primary w-100" onclick="buscar()">Buscar</button></div>
      <div class="col-md-3"><button class="btn btn-success w-100" onclick="exportar()">Exportar CSV</button></div>
      <div class="col-md-3"><a class="btn btn-outline-secondary w-100" href="/test-db">Probar Oracle</a></div>
    </div>
  </div>

  <div class="card shadow-sm mt-3 p-3">
    <div id="total" class="fw-bold mb-2">Cargando...</div>
    <div class="table-responsive">
      <table class="table table-sm table-striped" id="tabla">
        <thead><tr><th>Nombre</th><th>Cargo</th><th>Área</th><th>Tel</th><th>Correo</th><th>Estado</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<script>
async function buscar(){
  let q = document.getElementById('q').value;
  let res = await fetch('/api/buscar?q='+encodeURIComponent(q));
  let data = await res.json();
  if(data.error){ alert(data.error); return; }
  let tbody = document.querySelector('#tabla tbody');
  tbody.innerHTML = '';
  data.forEach(r=>{
    tbody.innerHTML += `<tr><td>${r.NOMBRE||''}</td><td>${r.CARGO||''}</td><td>${r.AREA||''}</td><td>${r.TELEFONO||''}</td><td>${r.CORREO||''}</td><td>${r.ENTIDAD||''}</td></tr>`;
  });
  document.getElementById('total').innerText = data.length + ' contactos encontrados';
}
function exportar(){ window.location = '/api/exportar?q='+encodeURIComponent(document.getElementById('q').value); }
buscar();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/test-db")
def test_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM DIRECTORIO_SIGED WHERE ACTIVO=1")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        return f"<h2>CONEXION OK</h2><p>{total} contactos activos</p><a href='/'>Volver</a>"
    except Exception as e:
        return f"<h2>ERROR ORACLE</h2><pre>{str(e)}</pre><p>Revisa DB_USER, DB_PASS, DB_DSN en Render > Environment</p><a href='/'>Volver</a>", 500

@app.route("/api/buscar")
def api_buscar():
    q = request.args.get("q","").strip()
    try:
        conn = get_conn()
        cur = conn.cursor()
        sql = "SELECT NOMBRE, CARGO, AREA, TELEFONO, CORREO, ENTIDAD FROM DIRECTORIO_SIGED WHERE ACTIVO=1"
        params = {}
        if q:
            sql += " AND (UPPER(NOMBRE) LIKE UPPER(:q) OR UPPER(AREA) LIKE UPPER(:q) OR UPPER(CORREO) LIKE UPPER(:q) OR UPPER(ENTIDAD) LIKE UPPER(:q))"
            params["q"] = f"%{q}%"
        sql += " ORDER BY NOMBRE FETCH FIRST 500 ROWS ONLY"
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        data = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/exportar")
def api_exportar():
    import io, csv
    from flask import Response
    q = request.args.get("q","").strip()
    try:
        conn = get_conn()
        cur = conn.cursor()
        sql = "SELECT NOMBRE, CARGO, AREA, TELEFONO, CORREO, ENTIDAD FROM DIRECTORIO_SIGED WHERE ACTIVO=1"
        params = {}
        if q:
            sql += " AND (UPPER(NOMBRE) LIKE UPPER(:q) OR UPPER(AREA) LIKE UPPER(:q) OR UPPER(CORREO) LIKE UPPER(:q))"
            params["q"] = f"%{q}%"
        cur.execute(sql, params)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([d[0] for d in cur.description])
        for row in cur.fetchall():
            writer.writerow(row)
        cur.close()
        conn.close()
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=directorio_siged.csv"})
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))