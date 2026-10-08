import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_FILE = "Directorio SIGED 2026 Secretarios, Enlaces y Operadores.xlsx"
if not os.path.exists(EXCEL_FILE):
    for f in os.listdir("."):
        if "SIGED" in f.upper() and f.endswith(".xlsx"):
            EXCEL_FILE = f
            break

def load_data():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(columns=["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRÓNICO","TELÉFONO","DIRECCIÓN","FECHA DE ACTUALIZACIÓN"])
    df = pd.read_excel(EXCEL_FILE, sheet_name=0, dtype=str)
    df = df.fillna("")
    return df

TEMPLATE = """
<!DOCTYPE html>
... [usa el archivo completo que te generé en /mnt/data/app.py]...
"""

@app.route("/")
def index():
    df = load_data()
    data_json = df.to_json(orient="records", force_ascii=False)
    return render_template_string(TEMPLATE, data_json=data_json, count=len(df), file=EXCEL_FILE)

@app.route("/guardar", methods=["POST"])
def guardar():
    try:
        payload = request.get_json()
        data_list = payload.get("cambios", [])
        df_new = pd.DataFrame(data_list)
        cols = ["ENTIDAD","ROL SIGED","NOMBRE","PUESTO","CORREO ELECTRÓNICO","TELÉFONO","DIRECCIÓN","FECHA DE ACTUALIZACIÓN"]
        for c in cols:
            if c not in df_new.columns:
                df_new[c] = ""
        df_new = df_new[cols]
        df_new.to_excel(EXCEL_FILE, index=False, sheet_name="Hoja1")
        backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{EXCEL_FILE}"
        df_new.to_excel(backup, index=False)
        return jsonify({"ok": True, "file": EXCEL_FILE, "count": len(df_new), "backup": backup})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/descargar")
def descargar():
    df = load_data()
    tmp = "/tmp/directorio_descarga.xlsx"
    df.to_excel(tmp, index=False)
    return send_file(tmp, as_attachment=True, download_name=f"Directorio_SIGED_2026_EDITADO_{datetime.now().strftime('%Y-%m-%d')}.xlsx")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
