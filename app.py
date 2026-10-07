import glob, csv, os
import pandas as pd
from flask import Flask, request, render_template_string, redirect, Response

app = Flask(__name__)
CSV_FILE = glob.glob("*.csv")[0] if glob.glob("*.csv") else "directorio.csv"

def cargar():
    try:
        df = pd.read_csv(CSV_FILE, dtype=str, encoding='utf-8').fillna("")
    except:
        df = pd.read_csv(CSV_FILE, dtype=str, encoding='latin1').fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

HTML = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Directorio SIGED 2026</title>
<style>
body{font-family:Arial;padding:15px;background:#f9f9f9}
select{padding:10px;margin:4px;border-radius:6px;min-width:180px}
button{padding:10px 18px;background:#0d47a1;color:white;border:none;border-radius:6px;cursor:pointer;margin:2px}
table{width:100%;border-collapse:collapse;margin-top:15px;background:white}
th,td{border:1px solid #ddd;padding:6px;font-size:12px} th{background:#6a1b2a;color:white}
input.edit{width:95%;padding:5px;border:1px solid #0d47a1}
</style>
</head><body>
<h2>Directorio SIGED 2026</h2>
<form method="get">
<select name="entidad"><option value="">-- Entidad -- Todas</option>
{% for e in entidades %}<option value="{{e}}" {% if e==entidad_sel %}selected{% endif %}>{{e}}</option>{% endfor %}
</select>
<select name="rol"><option value="">-- Rol -- Todos</option>
{% for r in roles %}<option value="{{r}}" {% if r==rol_sel %}selected{% endif %}>{{r}}</option>{% endfor %}
</select>
<button type="submit">Filtrar</button>
<a href="/"><button type="button" style="background:#eee;color:#333">Limpiar</button></a>
{% if not modo_edicion %}
<a href="/?edicion=1&rol={{rol_sel}}&entidad={{entidad_sel}}"><button type="button" style="background:#2e7d32">🔓 Modo Edición (Solo tú)</button></a>
{% else %}
<a href="/descargar"><button type="button" style="background:#ff6f00">⬇️ Descargar CSV Actualizado</button></a>
<a href="/"><button type="button" style="background:#666">Salir de Edición</button></a>
{% endif %}
</form>
<div style="margin:10px 0"><b>{{total}} registros</b> {% if rol_sel %}- {{rol_sel}} de {{entidad_sel if entidad_sel else "todo el país"}}{% endif %} {% if modo_edicion %}<span style="color:green">| EDITANDO - Los cambios se guardan aquí mismo</span>{% endif %}</div>

{% if modo_edicion %}
<form method="post" action="/guardar">
<div style="overflow:auto;max-height:70vh">
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for i,row in data.iterrows() %}
<tr>{% for c in cols %}<td><input class="edit" name="{{i}}__{{c}}" value="{{row[c]}}"></td>{% endfor %}</tr>
{% endfor %}
</table></div>
<br><button type="submit" style="background:#2e7d32;padding:12px 30px;font-size:16px">💾 GUARDAR CAMBIOS</button>
</form>
{% else %}
<div style="overflow:auto;max-height:70vh">
<table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in data.iterrows() %}<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>{% endfor %}
</table></div>
{% endif %}
</body></html>
"""

@app.route("/", methods=["GET"])
def index():
    df = cargar()
    cols = list(df.columns)
    col_rol = [c for c in cols if 'rol' in c.lower()][0] if [c for c in cols if 'rol' in c.lower()] else cols[0]
    col_ent = [c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()][0] if [c for c in cols if 'entidad' in c.lower() or 'estado' in c.lower()] else cols[0]

    roles = sorted(df[col_rol].dropna().astype(str).unique())
    entidades = sorted(df[col_ent].dropna().astype(str).unique())

    entidad_sel = request.args.get("entidad","")
    rol_sel = request.args.get("rol","")
    modo_edicion = request.args.get("edicion")=="1"

    df_f = df.copy()
    if rol_sel:
        df_f = df_f[df_f[col_rol].str.contains(rol_sel, case=False, na=False)]
    if entidad_sel:
        df_f = df_f[df_f[col_ent].str.contains(entidad_sel, case=False, na=False)]

    return render_template_string(HTML, data=df_f.head(500), cols=cols, total=len(df_f),
                                  entidades=entidades, roles=roles,
                                  entidad_sel=entidad_sel, rol_sel=rol_sel, modo_edicion=modo_edicion)

@app.route("/guardar", methods=["POST"])
def guardar():
    df = cargar()
    for key, val in request.form.items():
        if "__" in key:
            idx, col = key.split("__",1)
            try:
                idx=int(idx)
                df.at[idx, col] = val
            except: pass
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    return redirect("/?edicion=1")

@app.route("/descargar")
def descargar():
    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        content = f.read()
    return Response(content, mimetype="text/csv", headers={"Content-disposition": f"attachment; filename=DirectorioActualizado.csv"})

if __name__ == "__main__":
    app.run()
