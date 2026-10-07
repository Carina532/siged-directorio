import glob, os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = "siged2026"
PWD = "SIGED2026EDIT"
CSV = glob.glob("*.csv")[0] if glob.glob("*.csv") else "directorio.csv"

def cargar():
    try: df=pd.read_csv(CSV,dtype=str,encoding='utf-8').fillna("")
    except: df=pd.read_csv(CSV,dtype=str,encoding='latin1').fillna("")
    df.columns=[c.strip() for c in df.columns]
    return df

def fecha_actualizacion():
    try:
        ts = os.path.getmtime(CSV)
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
    except:
        return "07/10/2026"

HTML = """
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>Directorio SIGED 2026</title>
<style>
body{margin:0;font-family:Arial;background:#f5f3ef}
.header{background:#10312B;color:white;padding:10px 15px;display:flex;justify-content:space-between;flex-wrap:wrap}
.fecha{font-size:13px;background:#E8DCC5;color:#65142C;padding:8px 15px;display:flex;justify-content:space-between;flex-wrap:wrap}
.fecha a{color:#65142C;font-weight:bold;text-decoration:underline;cursor:pointer}
.bar{background:#65142C;color:white;padding:10px 15px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;border-bottom:4px solid #BC955C}
.bar button{background:#BC955C;color:#3C0E1E;font-weight:bold;border:none;padding:8px 14px;border-radius:5px;cursor:pointer}
.filters{padding:12px;background:white;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #ddd}
select{padding:10px;min-width:200px;border-radius:6px}
.btn{background:#10312B;color:white;border:none;padding:10px 16px;border-radius:6px;cursor:pointer}
table{width:100%;border-collapse:collapse;background:white}th,td{border:1px solid #ddd;padding:6px;font-size:12px}th{background:#10312B;color:white}
input.edit{width:95%;padding:5px;border:1px solid #BC955C;border-radius:4px}
</style></head><body>

<div class="header"><b>Directorio SIGED - {{total}} registros {% if rol_sel %}| {{rol_sel}}{% endif %}</b></div>

<div class="fecha">
<span>📅 Fecha de actualización: {{fecha}} |
{% if es_editora %}
✅ Editando como: <b>Carina</b> - <a href="/logout">Cerrar sesión</a>
{% else %}
Edita: <a href="/login">Carina (clic aquí para editar)</a>
{% endif %}
</span>
<span>🔒 Solo Editora puede modificar</span>
</div>

{% if es_editora %}
<div class="bar">
<strong>🔓 Modo Editora Activo</strong>
<form action="/subir" method="post" enctype="multipart/form-data" style="display:flex;gap:6px;align-items:center">
<input type="file" name="csv" accept=".csv"><button type="submit">📤 Subir CSV</button>
</form>
<a href="/descargar"><button>⬇️ Descargar CSV</button></a>
</div>
{% endif %}

<div class="filters">
<form method="get" style="display:flex;gap:8px;flex-wrap:wrap">
<select name="entidad"><option value="">-- Entidad -- Todas</option>
{% for e in entidades %}<option value="{{e}}" {% if e==entidad_sel %}selected{% endif %}>{{e}}</option>{% endfor %}
</select>
<select name="rol"><option value="">-- Rol -- Todos</option>
{% for r in roles %}<option value="{{r}}" {% if r==rol_sel %}selected{% endif %}>{{r}}</option>{% endfor %}
</select>
<button class="btn" type="submit">Filtrar</button>
<a href="/"><button type="button" class="btn" style="background:#eee;color:#333">Limpiar</button></a>
</form>
</div>

{% if es_editora %}
<form method="post" action="/guardar">
<div style="overflow:auto;max-height:60vh">
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for i,row in data.iterrows() %}
<tr>{% for c in cols %}<td><input class="edit" name="{{i}}__{{c}}" value="{{row[c]}}"></td>{% endfor %}</tr>
{% endfor %}
</table></div>
<div style="text-align:center;padding:15px"><button type="submit" style="background:#65142C;color:white;padding:12px 30px;border:none;border-radius:8px;font-size:16px">💾 GUARDAR CAMBIOS</button></div>
</form>
{% else %}
<div style="overflow:auto;max-height:70vh">
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in data.iterrows() %}<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>{% endfor %}
</table></div>
{% endif %}

</body></html>
"""

LOGIN_HTML = """
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width">
<style>body{font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:#f3f0eb}
.box{background:white;padding:30px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.2);border-top:6px solid #65142C;text-align:center}
input{padding:12px;width:90%;margin:10px 0;border:1px solid #ccc;border-radius:6px}
button{padding:12px;width:100%;background:#65142C;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:bold}</style>
</head><body><div class="box">
<h3 style="color:#65142C">🔒 Acceso Editora</h3>
<p>Fecha: {{fecha}}<br>Edita: <b>Carina</b></p>
<form method="post"><input type="password" name="pwd" placeholder="Contraseña"><button>Entrar</button></form>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<a href="/">← Regresar</a>
</div></body></html>
"""

@app.route("/")
def index():
    df=cargar()
    cols=list(df.columns)
    col_rol=[c for c in cols if 'rol' in c.lower()][0] if [c for c in cols if 'rol' in c.lower()] else cols[0]
    col_ent=[c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()][0] if [c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()] else cols[0]
    roles=sorted(df[col_rol].dropna().astype(str).unique())
    entidades=sorted(df[col_ent].dropna().astype(str).unique())
    ent_sel=request.args.get("entidad","")
    rol_sel=request.args.get("rol","")
    df_f=df.copy()
    if rol_sel: df_f=df_f[df_f[col_rol].str.contains(rol_sel,case=False,na=False)]
    if ent_sel: df_f=df_f[df_f[col_ent].str.contains(ent_sel,case=False,na=False)]
    return render_template_string(HTML, data=df_f.head(500), cols=cols, total=len(df_f),
                                  entidades=entidades, roles=roles,
                                  entidad_sel=ent_sel, rol_sel=rol_sel,
                                  fecha=fecha_actualizacion(),
                                  es_editora=session.get("editora",False))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("pwd")==PWD:
            session["editora"]=True
            return redirect("/")
        return render_template_string(LOGIN_HTML, error="Contraseña incorrecta: SIGED2026EDIT", fecha=fecha_actualizacion())
    return render_template_string(LOGIN_HTML, error="", fecha=fecha_actualizacion())

@app.route("/logout")
def logout():
    session.pop("editora",None)
    return redirect("/")

@app.route("/guardar", methods=["POST"])
def guardar():
    if not session.get("editora"): return redirect("/login")
    df=cargar()
    for k,v in request.form.items():
        if "__" in k:
            i,c=k.split("__",1)
            try: df.at[int(i),c]=v
            except: pass
    df.to_csv(CSV,index=False,encoding='utf-8-sig')
    return redirect("/")

@app.route("/subir", methods=["POST"])
def subir():
    if not session.get("editora"): return redirect("/login")
    f=request.files.get("csv")
    if f: f.save(CSV)
    return redirect("/")

@app.route("/descargar")
def descargar():
    if not session.get("editora"): return redirect("/login")
    content=open(CSV,encoding='utf-8-sig').read()
    return Response(content,mimetype="text/csv",headers={"Content-disposition":"attachment; filename=Directorio_SIGED_Actualizado.csv"})

if __name__=="__main__":
    app.run()
