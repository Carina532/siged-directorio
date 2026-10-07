import glob, os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd
app = Flask(__name__)
app.secret_key = "sep"
PWD = "SIGED2026EDIT"
CSV = glob.glob("*.csv")[0]

def cargar():
    try: return pd.read_csv(CSV,dtype=str,encoding='utf-8').fillna("")
    except: return pd.read_csv(CSV,dtype=str,encoding='latin1').fillna("")

HTML = """
<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width">
<style>
body{margin:0;font-family:Arial;background:#fdf8f0}
.header{background:#65142C;color:white;padding:14px 16px;border-bottom:4px solid #BC955C}
.fecha{background:#E8DCC5;padding:8px 16px;display:flex;justify-content:space-between;font-size:13px}
.fecha a{color:#65142C;font-weight:bold}
.bar{background:#10312B;color:white;padding:10px 16px;display:flex;gap:10px}
.bar button{background:#BC955C;color:#10312B;font-weight:bold;border:none;padding:8px 12px;border-radius:5px}
select{padding:10px;min-width:200px} th{background:#10312B;color:white;padding:8px} td{border:1px solid #ddd;padding:6px;font-size:12px}
</style>
<div class=header><b>Directorio SIGED - {{total}} registros</b> SEP</div>
<div class=fecha><span>📅 {{fecha}} | {% if ed %}Editando: Carina <a href=/logout>Salir</a>{% else %}Edita: <a href=/login>Carina (clic contraseña)</a>{% endif %}</span><span>{% if not ed %}Solo lectura - 10 usuarios{% else %}Modo Editora{% endif %}</span></div>
{% if ed %}<div class=bar><form action=/subir method=post enctype=multipart/form-data><input type=file name=csv><button>📤 Subir CSV</button></form><a href=/descargar><button>⬇️ Descargar CSV</button></a></div>{% endif %}
<form method=get style=padding:12px;background:white;display:flex;gap:8px><select name=entidad><option value="">-- Entidad --</option>{% for e in ents %}<option {% if e==ent_sel %}selected{% endif %}>{{e}}</option>{% endfor %}</select><select name=rol><option value="">-- Rol --</option>{% for r in roles %}<option {% if r==rol_sel %}selected{% endif %}>{{r}}</option>{% endfor %}</select><button style=background:#65142C;color:white;padding:10px;border:none;border-radius:6px>Filtrar</button></form>
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>{% for _,r in data.iterrows() %}<tr>{% for c in cols %}<td>{{r[c]}}</td>{% endfor %}</tr>{% endfor %}</table>
"""
LOGIN = """<body style=display:flex;justify-content:center;align-items:center;height:100vh;background:#f3efe6;font-family:Arial><div style=background:white;padding:30px;border-radius:12px;border-top:6px solid #65142C;text-align:center><h3>Contraseña Editora</h3><form method=post><input type=password name=pwd placeholder=SIGED2026EDIT style=padding:10px;width:90%><br><br><button style=padding:10px;width:100%;background:#65142C;color:white;border:none>Entrar</button></form><p style=color:red>{{err}}</p></div></body>"""

@app.route("/")
def i():
    df=cargar(); c=list(df.columns); ce=[x for x in c if 'entidad' in x.lower()][0]; cr=[x for x in c if 'rol' in x.lower()][0]
    es=request.args.get("entidad",""); rs=request.args.get("rol","")
    dff=df.copy()
    if es: dff=dff[dff[ce].str.contains(es,case=False,na=False)]
    if rs: dff=dff[dff[cr].str.contains(rs,case=False,na=False)]
    fec=datetime.fromtimestamp(os.path.getmtime(CSV)).strftime("%d/%m/%Y")
    return render_template_string(HTML,data=dff.head(500),cols=c,total=len(dff),ents=sorted(df[ce].unique()),roles=sorted(df[cr].unique()),ent_sel=es,rol_sel=rs,fecha=fec,ed=session.get("ed"))

@app.route("/login",methods=["GET","POST"])
def l():
    if request.method=="POST" and request.form.get("pwd")==PWD:
        session["ed"]=True; return redirect("/")
    return render_template_string(LOGIN,err="Mal" if request.method=="POST" else "")

@app.route("/logout")
def out(): session.clear(); return redirect("/")
@app.route("/subir",methods=["POST"])
def su(): f=request.files.get("csv");
    if f and session.get("ed"): f.save(CSV)
    return redirect("/")
@app.route("/descargar")
def de():
    if not session.get("ed"): return redirect("/login")
    return Response(open(CSV,encoding='utf-8-sig').read(),mimetype="text/csv",headers={"Content-disposition":"attachment; filename=Directorio.csv"})
