import glob, os, csv
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = "siged2026secret"
PASSWORD_EDITORA = "SIGED2026EDIT" # <--- Esta es tu contraseña para editar, solo tú
CSV_FILE = glob.glob("*.csv")[0] if glob.glob("*.csv") else "directorio.csv"

def cargar():
    try:
        df = pd.read_csv(CSV_FILE, dtype=str, encoding='utf-8').fillna("")
    except:
        df = pd.read_csv(CSV_FILE, dtype=str, encoding='latin1').fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

# LOGIN PARA EDITORA
LOGIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>body{font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:#f3f0eb}.box{background:white;padding:30px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.15);border-top:6px solid #65142C} input{padding:12px;width:100%;margin:10px 0} button{padding:12px;width:100%;background:#65142C;color:white;border:none;border-radius:6px;cursor:pointer}</style>
</head><body>
<div class="box"><h3 style="color:#65142C">Modo Editora - Contraseña</h3><p>Solo acceso autorizado SIGED</p>
<form method="post"><input type="password" name="pwd" placeholder="Contraseña de Editora"><button>Entrar</button></form>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<a href="/">← Regresar a directorio</a>
</div></body></html>
"""

HTML = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Directorio SIGED 2026</title>
<style>
body{font-family:Arial;margin:0;background:#f5f3ef}
.header{background:#10312B;color:white;padding:12px 15px;display:flex;justify-content:space-between;align-items:center}
.header span{font-weight:bold}
.bar-edicion{background:linear-gradient(90deg,#65142C 0%,#9D2449 100%);color:white;padding:10px 15px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;border-bottom:3px solid #BC955C}
.bar-edicion button{background:#BC955C;color:#3C0E1E;border:none;padding:8px 14px;border-radius:5px;font-weight:bold;cursor:pointer}
.filters{padding:12px 15px;background:white;border-bottom:1px solid #ddd;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select{padding:9px;border:1px solid #ccc;border-radius:6px;min-width:200px}
.btn-filtrar{background:#10312B;color:white;border:none;padding:9px 16px;border-radius:6px;cursor:pointer}
.btn-limpiar{background:#eee;color:#333;border:none;padding:9px 16px;border-radius:6px}
table{width:100%;border-collapse:collapse;background:white} th,td{border:1px solid #ddd;padding:7px;font-size:12px} th{background:#10312B;color:white}
input.edit{width:95%;padding:5px;border:1px solid #BC955C;border-radius:4px}
.count{padding:8px 15px;font-weight:bold;color:#65142C;background:#E8DCC5}
</style>
</head><body>
<div class="header"><span>Directorio SIGED - {{total}} registros {% if rol_sel %} | {{rol_sel}}{% endif %}</span>
{% if es_editora %}<a href="/logout"><button style="background:white;color:#10312B;border:none;padding:6px 12px;border-radius:5px">Salir Editora</button></a>{% endif %}
</div>

{% if es_editora %}
<div class="bar-edicion">
<strong style="color:#DDC9A3">🔒 Modo Editora Activo</strong>
<form action="/subir_csv" method="post" enctype="multipart/form-data" style="display:inline-flex;gap:6px">
<input type="file" name="csv" accept=".csv" style="color:white"><button type="submit">Subir CSV</button>
</form>
<a href="/descargar"><button>⬇️ Descargar Actualizado</button></a>
<span style="font-size:12px;opacity:.9">Solo tú puedes editar</span>
</div>
{% endif %}

<div class="filters">
<form method="get" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
<select name="entidad"><option value="">-- Entidad -- Todas</option>
{% for e in entidades %}<option value="{{e}}" {% if e==entidad_sel %}selected{% endif %}>{{e}}</option>{% endfor %}
</select>
<select name="rol"><option value="">-- Rol -- Todos</option>
{% for r in roles %}<option value="{{r}}" {% if r==rol_sel %}selected{% endif %}>{{r}}</option>{% endfor %}
</select>
<button class="btn-filtrar" type="submit">Filtrar</button>
<a href="/"><button class="btn-limpiar" type="button">Limpiar</button></a>
{% if not es_editora %}
<a href="/login"><button type="button" style="background:#65142C;color:white;border:none;padding:9px 16px;border-radius:6px">🔑 Entrar como Editora</button></a>
{% endif %}
</form>
</div>

<div class="count">{{total}} registros {% if rol_sel %}mostrando: {{rol_sel}} de {{entidad_sel if entidad_sel else "todo el país"}}{% endif %}</div>

{% if es_editora %}
<form method="post" action="/guardar">
<div style="overflow:auto;max-height:65vh"><table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}<th>ACCION</th></tr>
{% for i,row in data.iterrows() %}
<tr>{% for c in cols %}<td><input class="edit" name="{{i}}__{{c}}" value="{{row[c]}}"></td>{% endfor %}<td><small>{{i}}</small></td></tr>
{% endfor %}
</table></div>
<div style="padding:15px;text-align:center"><button type="submit" style="background:#65142C;padding:12px 30px;font-size:16px;border:none;color:white;border-radius:8px">💾 GUARDAR CAMBIOS</button></div>
</form>
{% else %}
<div style="overflow:auto;max-height:70vh"><table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in data.iterrows() %}<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>{% endfor %}
</table></div>
{% endif %}
</body></html>
"""

@app.route("/")
def index():
    df = cargar()
    cols = list(df.columns)
    col_rol = [c for c in cols if 'rol' in c.lower()][0] if [c for c in cols if 'rol' in c.lower()] else cols[0]
    col_ent = [c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()][0] if [c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()] else cols[0]
    roles = sorted(df[col_rol].dropna().astype(str).unique())
    entidades = sorted(df[col_ent].dropna().astype(str).unique())
    entidad_sel = request.args.get("entidad","")
    rol_sel = request.args.get("rol","")
    df_f = df.copy()
    if rol_sel:
        df_f = df_f[df_f[col_rol].str.contains(rol_sel, case=False, na=False)]
    if entidad_sel:
        df_f = df_f[df_f[col_ent].str.contains(entidad_sel, case=False, na=False)]
    es_editora = session.get("editora", False)
    return render_template_string(HTML, data=df_f.head(500), cols=cols, total=len(df_f),
                                  entidades=entidades, roles=roles,
                                  entidad_sel=entidad_sel, rol_sel=rol_sel, es_editora=es_editora)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("pwd")==PASSWORD_EDITORA:
            session["editora"]=True
            return redirect("/")
        else:
            return render_template_string(LOGIN_HTML, error="Contraseña incorrecta")
    return render_template_string(LOGIN_HTML, error="")

@app.route("/logout")
def logout():
    session.pop("editora", None)
    return redirect("/")

@app.route("/guardar", methods=["POST"])
def guardar():
    if not session.get("editora"): return redirect("/login")
    df = cargar()
    for key,val in request.form.items():
        if "__" in key:
            idx,col = key.split("__",1)
            try: df.at[int(idx), col]=val
            except: pass
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    return redirect("/?rol=&entidad=")

@app.route("/subir_csv", methods=["POST"])
def subir_csv():
    if not session.get("editora"): return redirect("/login")
    f = request.files.get("csv")
    if f: f.save(CSV_FILE)
    return redirect("/")

@app.route("/descargar")
def descargar():
    if not session.get("editora"): return redirect("/login")
    with open(CSV_FILE, "r", encoding="utf-8-sig") as fp:
        content=fp.read()
    return Response(content, mimetype="text/csv", headers={"Content-disposition":"attachment; filename=Directorio_SIGED_Actualizado.csv"})

if __name__=="__main__":
    app.run()
