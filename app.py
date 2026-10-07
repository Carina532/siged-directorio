import glob
from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)
PASSWORD = "SIGED2026"

def cargar_datos():
    archivos = glob.glob("*.csv")
    if not archivos:
        return None, "No hay CSV"
    for f in archivos:
        try:
            df = pd.read_csv(f, encoding='utf-8', dtype=str).fillna("")
            return df, None
        except:
            try:
                df = pd.read_csv(f, encoding='latin1', dtype=str).fillna("")
                return df, None
            except Exception as e:
                continue
    return None, "No se pudo leer el CSV"

HTML = """
<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>SIGED Directorio</title>
<style>body{font-family:Arial;padding:15px} input{padding:8px;margin:3px} table{border-collapse:collapse;width:100%;margin-top:10px} th,td{border:1px solid #ccc;padding:6px;font-size:12px} th{background:#6a1b2a;color:white}</style>
</head><body>
<h3>Directorio SIGED 2026 - Acceso Restringido</h3>
<form>
<input name=q placeholder="Nombre" value="{{q}}">
<input name=entidad placeholder="Entidad" value="{{entidad}}">
<input name=rol placeholder="Rol" value="{{rol}}">
<input type=password name=pwd placeholder="Contraseña" value="{{pwd}}">
<button>Buscar</button>
</form>
{% if error %}<p style='color:red'>{{error}}</p>{% endif %}
{% if df is not none %}
<p><b>{{total}} registros</b></p>
<div style='overflow:auto'><table><tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>
{% for _,row in df.iterrows() %}<tr>{% for c in cols %}<td>{{row[c]}}</td>{% endfor %}</tr>{% endfor %}
</table></div>
{% endif %}
</body></html>
"""

@app.route('/')
def index():
    q=request.args.get('q',''); entidad=request.args.get('entidad',''); rol=request.args.get('rol',''); pwd=request.args.get('pwd','')
    if pwd!=PASSWORD:
        return render_template_string(HTML, df=None, cols=[], error="Ingresa contraseña SIGED2026" if pwd else "Ingresa la contraseña para ver el directorio", q=q, entidad=entidad, rol=rol, pwd=pwd, total=0)
    df, err = cargar_datos()
    if err:
        return render_template_string(HTML, df=None, cols=[], error=err, q=q, entidad=entidad, rol=rol, pwd=pwd, total=0)
    df_f=df.copy()
    if q:
        df_f=df_f[df_f.apply(lambda r: r.astype(str).str.contains(q,case=False).any(),axis=1)]
    if entidad:
        c=[x for x in df_f.columns if 'entid' in x.lower() or 'estado' in x.lower()]
        if c: df_f=df_f[df_f[c[0]].str.contains(entidad,case=False,na=False)]
    if rol:
        c=[x for x in df_f.columns if 'rol' in x.lower() or 'cargo' in x.lower() or 'tipo' in x.lower()]
        if c: df_f=df_f[df_f[c[0]].str.contains(rol,case=False,na=False)]
    return render_template_string(HTML, df=df_f.head(200), cols=list(df_f.columns), error="", q=q, entidad=entidad, rol=rol, pwd=pwd, total=len(df_f))

if __name__=='__main__':
    app.run()
