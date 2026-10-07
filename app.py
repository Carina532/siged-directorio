import glob, os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = "sep2026final"
PWD = "SIGED2026EDIT"

def get_csv():
    files = glob.glob("*.csv")
    return files[0] if files else None

def cargar():
    csv_file = get_csv()
    if not csv_file:
        return pd.DataFrame(), "Sin archivo"
    for enc in ['utf-8', 'utf-8-sig', 'latin1']:
        for sep in [',', ';', '|']:
            try:
                df = pd.read_csv(csv_file, dtype=str, sep=sep, engine='python', encoding=enc, on_bad_lines='skip').fillna("")
                if len(df.columns) >= 1 and len(df) > 0:
                    return df, csv_file
            except:
                continue
    try:
        df = pd.read_csv(csv_file, dtype=str, engine='python', encoding='utf-8', on_bad_lines='skip', sep=None).fillna("")
        return df, csv_file
    except Exception as e:
        return pd.DataFrame({"Aviso":[f"CSV con filas malas omitidas. Error: {e}"]}), csv_file

def fecha():
    f = get_csv()
    if not f: return "07/10/2026"
    try: return datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d/%m/%Y")
    except: return "07/10/2026"

HTML = """
<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#fdf6ef}
.h{background:#65142C;color:#fff;padding:14px 16px;border-bottom:4px solid #BC955C;display:flex;justify-content:space-between}
.f{background:#E8DCC5;padding:8px 16px;display:flex;justify-content:space-between;font-size:13px;flex-wrap:wrap}
.f a{color:#65142C;font-weight:bold;text-decoration:underline}
.b{background:#10312B;color:#fff;padding:10px 16px;display:flex;gap:10px;border-bottom:3px solid #BC955C;flex-wrap:wrap}
.b button{background:#BC955C;color:#10312B;font-weight:bold;border:none;padding:8px 14px;border-radius:5px;cursor:pointer}
th{background:#10312B;color:#fff;padding:10px 6px;font-size:11px} td{border:1px solid #ddd;padding:7px;font-size:11px}
table{border-collapse:collapse;background:#fff;width:100%}
</style>
<div class=h><b>Directorio SIGED - {{t}} registros</b><span>SEP</span></div>
<div class=f><span>📅 Fecha: {{fe}} | {% if ed %}✅ Carina editando - <a href=/logout>Salir</a>{% else %}Edita: <a href=/login>Carina (clic contraseña)</a>{% endif %}</span><span>{% if ed %}Modo Editora{% else %}Solo lectura{% endif %}</span></div>
{% if ed %}<div class=b><form action=/subir method=post enctype=multipart/form-data style=display:flex;gap:8px><input type=file name=csv accept=.csv><button>📤 Subir CSV</button></form><a href=/descargar><button>⬇️ Descargar CSV</button></a></div>{% endif %}
<div style=padding:12px;background:#fff>
<form method=get style=display:flex;gap:8px;flex-wrap:wrap>
<select name=entidad><option value="">-- Entidad -- Todas</option>{% for e in ents %}<option {% if e==esel %}selected{% endif %}>{{e}}</option>{% endfor %}</select>
<select name=rol><option value="">-- Rol --</option>{% for r in rols %}<option {% if r==rsel %}selected{% endif %}>{{r}}</option>{% endfor %}</select>
<button style=background:#65142C;color:#fff;padding:10px 18px;border:none;border-radius:6px>Filtrar</button>
<a href="/"><button type=button>Limpiar</button></a>
</form></div>
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>{% for _,r in data.iterrows() %}<tr>{% for c in cols %}<td>{{r[c]}}</td>{% endfor %}</tr>{% endfor %}</table>
<p style=padding:10px;font-size:11px;color:#666>Archivo: {{csvname}}</p>
"""
LOGIN = """<body style=font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:#f3efe6><div style=background:#fff;padding:32px;border-radius:12px;border-top:7px solid #65142C;width:300px;text-align:center><h3 style=color:#65142C>Acceso Editora Carina</h3><form method=post><input type=password name=pwd placeholder="SIGED2026EDIT" style=padding:12px;width:90%><br><br><button style=padding:12px;width:100%;background:#65142C;color:#fff;border:none;border-radius:6px>Entrar</button></form><p style=color:red>{{e}}</p></div></body>"""

@app.route("/")
def idx():
    df, csvname = cargar()
    if df.empty and csvname=="Sin archivo":
        return f"<h3>No hay CSV. Archivos: {glob.glob('*')}</h3>"
    cols = list(df.columns) if not df.empty else []
    ce = next((c for c in cols if 'entidad' in c.lower()), cols[0] if cols else None)
    cr = next((c for c in cols if 'rol' in c.lower()), cols[1] if len(cols)>1 else ce)
    esel = request.args.get("entidad","")
    rsel = request.args.get("rol","")
    dff = df.copy()
    try:
        if esel and ce and ce in dff.columns: dff = dff[dff[ce].astype(str).str.contains(esel,case=False,na=False)]
        if rsel and cr and cr in dff.columns: dff = dff[dff[cr].astype(str).str.contains(rsel,case=False,na=False)]
    except: pass
    ents = sorted(df[ce].dropna().astype(str).unique()) if ce and ce in df.columns else []
    rols = sorted(df[cr].dropna().astype(str).unique()) if cr and cr in df.columns else []
    return render_template_string(HTML,data=dff.head(900),cols=cols,t=len(dff),ents=ents,rols=rols,esel=esel,rsel=rsel,fe=fecha(),ed=session.get("ed"),csvname=csvname)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST" and request.form.get("pwd")==PWD:
        session["ed"]=True
        return redirect("/")
    return render_template_string(LOGIN,e="Incorrecta" if request.method=="POST" else "")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/subir",methods=["POST"])
def subir():
    if not session.get("ed"): return redirect("/login")
    f = request.files.get("csv")
    csv_actual = get_csv() or "Directorio.csv"
    if f and f.filename:
        f.save(csv_actual)
    return redirect("/")

@app.route("/descargar")
def descargar():
    if not session.get("ed"): return redirect("/login")
    csv_file = get_csv()
    if not csv_file: return "No hay archivo"
    data = open(csv_file,encoding='utf-8-sig',errors='ignore').read()
    return Response(data,mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=Directorio.csv"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)