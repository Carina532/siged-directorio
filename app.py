import glob
from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)
PASSWORD = "SIGED2026"

def cargar_datos():
    archivos = glob.glob("*.csv")
    if not archivos:
        return None, "No hay CSV subido"
    for f in archivos:
        try:
            return pd.read_csv(f, encoding='utf-8', dtype=str).fillna(""), None
        except:
            try:
                return pd.read_csv(f, encoding='latin1', dtype=str).fillna(""), None
            except:
                continue
    return None, "No se pudo leer el CSV"

HTML = """
<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>SIGED</title>
<style>body{font-family:Arial;padding:12px} input{padding:8px;margin:2px} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ccc;padding:6px;font-size:11px} th{background:#6a1b2a;color:white}</style>
</head><body>
<h3>Directorio SIGED 2026</h3>
<form method="get">
<input name="q" placeholder="Nombre" value="{{q}}">
<input name="entidad" placeholder="Entidad" value="{{entidad}}">
<input name="rol" placeholder="Rol" value="{{rol}}">
<input type="password" name="pwd" placeholder="Contraseña" value="{{pwd}}">
<button type="submit">Buscar</button>
</form>
{% if error %}<p style='color:red'><b>{{error}}</b></p>{% endif %}
{% if df is not none %}
<p>{{total}} registros</p>
<div style='overflow:auto'><table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in df.iterrows() %}<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>{% endfor %}
</table></div>
{% endif %}
</body></html>
"""

@app.route('/', methods=['GET'])
def index():
    try:
        q = request.args.get('q','').strip()
        entidad = request.args.get('entidad','').strip()
        rol = request.args.get('rol','').strip()
        pwd = request.args.get('pwd','').strip()

        if pwd!= PASSWORD:
            msg = "Ingresa contraseña SIGED2026" if pwd else "Escribe la contraseña SIGED2026 para ver el directorio"
            return render_template_string(HTML, df=None, cols=[], error=msg, q=q, entidad=entidad, rol=rol, pwd=pwd, total=0)

        df, err = cargar_datos()
        if err or df is None:
            return render_template_string(HTML, df=None, cols=[], error=err, q=q, entidad=entidad, rol=rol, pwd=pwd, total=0)

        df_f = df.copy()
        if q:
            df_f = df_f[df_f.apply(lambda r: r.astype(str).str.contains(q, case=False, na=False).any(), axis=1)]
        if entidad:
            col = [c for c in df_f.columns if 'entid' in c.lower() or 'estado' in c.lower()]
            if col:
                df_f = df_f[df_f[col[0]].str.contains(entidad, case=False, na=False)]
        if rol:
            col = [c for c in df_f.columns if 'rol' in c.lower() or 'cargo' in c.lower() or 'tipo' in c.lower()]
            if col:
                df_f = df_f[df_f[col[0]].str.contains(rol, case=False, na=False)]

        return render_template_string(HTML, df=df_f.head(200), cols=list(df_f.columns), error="", q=q, entidad=entidad, rol=rol, pwd=pwd, total=len(df_f))
    except Exception as e:
        return render_template_string(HTML, df=None, cols=[], error=f"Error temporal: {e}", q="", entidad="", rol="", pwd="", total=0)

if __name__ == '__main__':
    app.run()
