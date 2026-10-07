import glob, os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = "siged2026sep"
PASSWORD = "SIGED2026EDIT" # Tu contraseña única
CSV = glob.glob("*.csv")[0] if glob.glob("*.csv") else "directorio.csv"

def cargar():
    try: df = pd.read_csv(CSV, dtype=str, encoding='utf-8').fillna("")
    except: df = pd.read_csv(CSV, dtype=str, encoding='latin1').fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

def fecha():
    try: return datetime.fromtimestamp(os.path.getmtime(CSV)).strftime("%d/%m/%Y")
    except: return datetime.now().strftime("%d/%m/%Y")

HTML = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Directorio SIGED</title>
<style>
body{margin:0;font-family:Arial;background:#f9f6f0}
.header{background:#65142C;color:white;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #BC955C}
.header b{font-size:16px}
.fecha{background:#E8DCC5;color:#3B0D1A;padding:8px 18px;display:flex;justify-content:space-between;font-size:13px}
.fecha a{color:#65142C;font-weight:bold}
.bar-editora{background:#10312B;color:white;padding:10px 18px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;border-bottom:3px solid #BC955C}
.bar-editora button{background:#BC955C;color:#10312B;font-weight:bold;border:none;padding:8px 14px;border-radius:5px;cursor:pointer}
.filtros{padding:14px 18px;background:white;display:flex;gap:10px;flex-wrap:wrap}
select{padding:10px;min-width:230px;border:1px solid #ccc;border-radius:6px}
.btn{background:#65142C;color:white;border:none;padding:10px 18px;border-radius:6px;cursor:pointer;font-weight:bold}
.btn-sec{background:#eee;color:#333;border:none;padding:10px 18px;border-radius:6px}
table{width:100%;border-collapse:collapse;background:white}
th{background:#10312B;color:white;padding:10px 6px;font-size:12px;position:sticky;top:0}
td{border:1px solid #ddd;padding:8px;font-size:12px;vertical-align:top}
input.edit{width:96%;padding:6px;border:1px solid #BC955C;border-radius:4px}
</style></head><body>

<div class="header"><b>Directorio SIGED - {{total}} registros {% if rol_sel %} | {{rol_sel}}{% endif %}</b>
<span style="font-size:12px;opacity:.9">SEP</span></div>

<div class="fecha">
<span>📅 Fecha de actualización: {{fecha}} |
{% if es_editora %} ✅ Editando como <b>Carina</b> - <a href="/logout">Salir Editora</a>
{% else %} Edita: <a href="/login">Carina (clic aquí para editar con contraseña)</a>
{% endif %}
</span>
<span>{% if not es_editora %}Solo lectura para los 10 usuarios{% else %}Modo edición activo{% endif %}</span>
</div>

{% if es_editora %}
<div class="bar-editora">
<span>🔓 Editora Autorizada:</span>
<form action="/subir" method="post" enctype="multipart/form-data" style="display:flex;gap:6px">
<input type="file" name="csv" accept=".csv"><button type="submit">📤 Subir CSV</button>
</form>
<a href="/descargar"><button>⬇️ Descargar CSV Actualizado</button></a>
</div>
{% endif %}

<div class="filtros">
<form method="get" style="display:flex;gap:10px;flex-wrap:wrap">
<select name="entidad"><option value="">-- Entidad -- Todas</option>
{% for e in entidades %}<option value="{{e}}" {% if e==entidad_sel %}selected{% endif %}>{{e}}</option>{% endfor %}
</select>
<select name="rol"><option value="">-- Rol -- OPERADOR / ENLACE</option>
{% for r in roles %}<option value="{{r}}" {% if r==rol_sel %}selected{% endif %}>{{r}}</option>{% endfor %}
</select>
<button class="btn" type="submit">Filtrar</button>
<a href="/"><button type="button" class="btn-sec">Limpiar</button></a>
</form>
</div>

{% if es_editora %}
<form method="post" action="/guardar">
<div style="overflow:auto;max-height:68vh"><table>
<tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for i,row in data.iterrows() %}
<tr>{% for c in cols %}<td><input class="edit" name="{{i}}__{{c}}" value="{{row[c]}}"></td>{% endfor %}</tr>
{% endfor %}
</table></div>
<div style="text-align:center;padding:16px"><button type="submit" style="background:#65142C;color:white;padding:12px 32px;border:none;border-radius:8px;font-size:15px;font-weight:bold">💾 GUARDAR CAMBIOS</button></div>
</form>
{% else %}
<div style="overflow:auto;max-height:70vh"><table>
<tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in data.iterrows() %}
<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>
{% endfor %}
</table></div>
{% endif %}
</body></html>
"""

LOGIN = """
<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width">
<style>body{font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:#f3efe6}
.box{background:white;padding:32px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.15);border-top:7px solid #65142C;width:320px;text-align:center}
input{padding:12px;width:90%;margin:12px 0;border:1px solid #ccc;border-radius:6px}button{padding:12px;width:100%;background:#65142C;color:white;border:none;border-radius:6px;font-weight:bold}</style>
</head><body><div class="box">
<h3 style="color:#65142C">🔒 Acceso Editora<br><small>Directorio SIGED</small></h3>
<p>Solo <b>Carina</b> puede editar</p>
<form method="post"><input type="password" name="pwd" placeholder="Contraseña"><button>Entrar</button></form>
{% if error %}<p style="color:red;font-size:13px">{{error}}</p>{% endif %}
<a href="/" style="font-size:12px">Regresar a directorio</a>
</div></body></html>
"""

@app.route("/")
def index():
    df=cargar(); cols=list(df.columns)
    cr=[c for c in cols if 'rol' in c.lower()][0]; ce=[c for c in cols if 'entidad' in c.lower()][0]
    roles=sorted(df[cr].dropna().astype(str).unique()); ents=sorted(df[ce].dropna().astype(str).unique())
    ent_sel=request.args.get("entidad",""); rol_sel=request.args.get("rol","")
    df_f=df.copy()
    if rol_sel: df_f=df_f[df_f[cr].str.contains(rol_sel,case=False,na=False)]
    if ent_sel: df_f=df_f[df_f[ce].str.contains(ent_sel,case=False,na=False)]
    return render_template_string(HTML,data=df_f.head(800),cols=cols,total=len(df_f),entidades=ents,roles=roles,entidad_sel=ent_sel,rol_sel=rol_sel,fecha=fecha(),es_editora=session.get("ed",False))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("pwd")==PASSWORD:
            session["ed"]=True; return redirect("/")
        return render_template_string(LOGIN,error="Contraseña incorrecta")
    return render_template_string(LOGIN,error="")

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/guardar",methods=["POST"])
def guardar():
    if not session.get("ed"): return redirect("/login")
    df=cargar()
    for k,v in request.form.items():
        if "__" in k:
            i,c=k.split("__",1)
            try: df.at[int(i),c]=v
            except: pass
    df.to_csv(CSV,index=False,encoding='utf-8-sig'); return redirect("/")

@app.route("/subir",methods=["POST"])
def subir():
    if not session.get("ed"): return redirect("/login")
    f=request.files.get("csv")
    if f: f.save(CSV)
    return redirect("/")

@app.route("/descargar")
def descargar():
    if not session.get("ed"): return redirect("/login")
    content=open(CSV,encoding='utf-8-sig').read()
    return Response(content,mimetype="text/csv",headers={"Content-disposition":"attachment; filename=Directorio_SIGED_Actualizado.csv"})
