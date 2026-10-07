from flask import Flask, render_template_string, request, redirect
import pandas as pd
import os, re, unicodedata
from datetime import datetime

app = Flask(__name__)
EXCEL_FILE = "Directorio SIGED 2026 Secretarios, Enlaces y Operadores.csv"
HISTORIAL = "historial.txt"
PASSWORD_EDITOR = "SIGED2026"

def fix_mojibake(text):
    try:
        if 'Ã' in str(text) or 'Â' in str(text):
            return str(text).encode('latin1').decode('utf-8')
    except: pass
    return text

def normaliza(s):
    s = str(s).lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c)!= 'Mn')
    s = re.sub(r'[.,;:]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def load_df():
    if not os.path.exists(EXCEL_FILE):
        pd.DataFrame(columns=["ENTIDAD","ROL","NOMBRE","TELEFONO","CORREO"]).to_csv(EXCEL_FILE, index=False, sep=';', encoding='utf-8-sig')
    try:
        df = pd.read_csv(EXCEL_FILE, encoding='utf-8-sig', sep=';', engine='python', quotechar='"')
    except:
        df = pd.read_csv(EXCEL_FILE, encoding='utf-8-sig', sep=',', engine='python')
    df.columns = [c.strip().upper() for c in df.columns]
    df = df.map(fix_mojibake)
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df.replace("nan","").replace("None","")

def save_df(df):
    df.to_csv(EXCEL_FILE, index=False, sep=';', encoding='utf-8-sig')
    with open(HISTORIAL, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Actualizado - {len(df)} registros\n")

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Directorio SIGED</title>
<style>
body{font-family:Arial;background:#f2f2f2;margin:0}
.header{background:#004a8f;color:white;padding:12px 20px;display:flex;justify-content:space-between}
.filters{background:white;padding:15px;display:flex;gap:8px;flex-wrap:wrap}
table{width:100%;background:white;border-collapse:collapse;font-size:13px}
th{background:#222;color:white;padding:8px;position:sticky;top:0}
td{padding:7px;border-bottom:1px solid #ddd}
.btn{padding:7px 12px;border:0;border-radius:4px;cursor:pointer}
.btn-blue{background:#004a8f;color:white}.btn-red{background:#c00;color:white}.btn-gray{background:#eee}
input,select{padding:8px;border:1px solid #ccc;border-radius:4px}
.admin-bar{background:#ffeb3b;padding:10px 20px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
</style></head><body>
<div class="header"><b>Directorio SIGED - {{total}} registros</b><div><a href="/?edit={{edit_mode}}"><button class="btn btn-gray">{{'Salir Editor' if edit_mode else 'Soy Editora'}}</button></a></div></div>
{% if edit_mode %}<div class="admin-bar"><b>Modo Editora</b><form action="/upload" method="post" enctype="multipart/form-data" style="display:flex;gap:8px"><input type="file" name="archivo" accept=".csv" required><input type="hidden" name="pwd" value="{{pwd}}"><button class="btn btn-blue">Subir CSV</button></form></div>{% endif %}
<div class="filters"><form method="get" style="display:flex;gap:8px;flex-wrap:wrap;width:100%"><input name="q" placeholder="Buscar..." value="{{q}}" style="width:340px"><select name="entidad"><option value="">-- Entidad --</option>{% for e in entidades %}<option {% if normaliza(e)==normaliza(entidad) %}selected{% endif %}>{{e}}</option>{% endfor %}</select><select name="rol"><option value="">-- Rol --</option>{% for r in roles %}<option {% if normaliza(r)==normaliza(rol) %}selected{% endif %}>{{r}}</option>{% endfor %}</select><input type="hidden" name="pwd" value="{{pwd}}"><label><input type="checkbox" name="edit" value="1" {% if edit_mode %}checked{% endif %} onchange="this.form.submit()"> Edicion</label><button class="btn btn-blue">Filtrar</button><a href="/"><button type="button" class="btn btn-gray">Limpiar</button></a></form></div>
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}{% if edit_mode %}<th>ACCION</th>{% endif %}</tr>{% for idx, r in rows %}<tr>{% for c in cols %}<td>{{r[c]}}</td>{% endfor %}{% if edit_mode %}<td><a href="/editar/{{idx}}?pwd={{pwd}}"><button class="btn btn-blue">Editar</button></a> <a href="/eliminar/{{idx}}?pwd={{pwd}}" onclick="return confirm('Borrar?')"><button class="btn btn-red">X</button></a></td>{% endif %}</tr>{% endfor %}</table></body></html>
"""
EDIT_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Editar</title><style>body{font-family:Arial;padding:20px;background:#f2f2f2}.box{background:white;padding:20px;max-width:600px;margin:auto}input{width:100%;padding:8px;margin:6px 0;border:1px solid #ccc;border-radius:4px}button{padding:10px;background:#004a8f;color:white;border:0;border-radius:4px}</style></head><body><div class="box"><h3>Editar {{idx}}</h3><form method="post">{% for c in cols %}<label>{{c}}</label><input name="{{c}}" value="{{data[c]}}">{% endfor %}<input type="hidden" name="pwd" value="{{pwd}}"><button>Guardar</button> <a href="/?pwd={{pwd}}&edit=1">Cancelar</a></form></div></body></html>"""

def is_editor():
    pwd = request.args.get("pwd") or request.form.get("pwd") or ""
    return pwd == PASSWORD_EDITOR, pwd

@app.route("/")
def index():
    q = request.args.get("q","").strip(); entidad = request.args.get("entidad","").strip(); rol = request.args.get("rol","").strip()
    df = load_df(); cols = list(df.columns); col_ent = next((c for c in cols if "ENTIDAD" in c), cols[0]); col_rol = next((c for c in cols if "ROL" in c), cols[0])
    total = len(df); edit_mode, pwd = is_editor()
    if request.args.get("edit") == "1" and not edit_mode:
        return "<script>var p=prompt('Contraseña:'); if(p) location.href='/?pwd='+p+'&edit=1'; else location.href='/';</script>"
    entidades = sorted([x for x in df[col_ent].dropna().astype(str).unique() if x and x!='']); roles = sorted([x for x in df[col_rol].dropna().astype(str).unique() if x and x!=''])
    df_f = df.copy()
    if q:
        q_norm = normaliza(q); palabras = q_norm.split()
        df_f = df_f[df_f.apply(lambda row: all(p in normaliza(" ".join(row.astype(str).values)) for p in palabras), axis=1)]
    if entidad: df_f = df_f[df_f[col_ent].apply(normaliza) == normaliza(entidad)]
    if rol: df_f = df_f[df_f[col_rol].apply(normaliza) == normaliza(rol)]
    rows = list(df_f.iterrows())
    return render_template_string(HTML, rows=rows, cols=cols, total=total, entidades=entidades, roles=roles, q=q, entidad=entidad, rol=rol, edit_mode=edit_mode, pwd=pwd, normaliza=normaliza)

@app.route("/editar/<int:idx>", methods=["GET","POST"])
def editar(idx):
    edit_mode, pwd = is_editor()
    if not edit_mode: return redirect("/")
    df = load_df(); cols = list(df.columns)
    if request.method == "POST":
        for c in cols: df.at[idx, c] = request.form.get(c,"").strip()
        save_df(df); return redirect(f"/?pwd={pwd}&edit=1")
    data = df.loc[idx].to_dict()
    return render_template_string(EDIT_HTML, cols=cols, data=data, idx=idx, pwd=pwd)

@app.route("/eliminar/<int:idx>")
def eliminar(idx):
    edit_mode, pwd = is_editor()
    if not edit_mode: return redirect("/")
    df = load_df(); df = df.drop(index=idx).reset_index(drop=True); save_df(df)
    return redirect(f"/?pwd={pwd}&edit=1")

@app.route("/upload", methods=["POST"])
def upload():
    edit_mode, pwd = is_editor()
    if not edit_mode: return redirect("/")
    f = request.files.get("archivo")
    if f: f.save(EXCEL_FILE)
    return redirect(f"/?pwd={pwd}&edit=1")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
