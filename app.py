import os, glob
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = "sep2026final"
PWD = "SIGED2026EDIT"

def get_csv():
    c = glob.glob("*.csv")
    return c[0] if c else None

def cargar():
    csv = get_csv()
    if not csv: return pd.DataFrame([{"Aviso":"Sube tu CSV en modo edición"}])
    try:
        return pd.read_csv(csv, dtype=str, encoding='utf-8').fillna("")
    except:
        try:
            return pd.read_csv(csv, dtype=str, encoding='latin1').fillna("")
        except Exception as e:
            return pd.DataFrame([{"Error":str(e)}])

def fecha():
    csv = get_csv()
    try:
        return datetime.fromtimestamp(os.path.getmtime(csv)).strftime("%d/%m/%Y")
    except:
        return "07/10/2026"

HTML = """
<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#fdf6ef}
.h{background:#65142C;color:#fff;padding:14px 16px;border-bottom:4px solid #BC955C;display:flex;justify-content:space-between}
.f{background:#E8DCC5;padding:8px 16px;display:flex;justify-content:space-between;font-size:13px;flex-wrap:wrap}
.f a{color:#65142C;font-weight:bold;text-decoration:underline}
.b{background:#10312B;color:#fff;padding:10px 16px;display:flex;gap:10px;border-bottom:3px solid #BC955C;flex-wrap:wrap}
.b button{background:#BC955C;color:#10312B;font-weight:bold;border:none;padding:8px 14px;border-radius:5px;cursor:pointer}
select{padding:10px;min-width:230px}
th{background:#10312B;color:#fff;padding:10px 6px;font-size:11px;text-align:left}
td{border:1px solid #ddd;padding:7px;font-size:11px;word-break:break-word}
table{border-collapse:collapse;width:100%;background:#fff}
</style>
<div class=h><b>Directorio SIGED -
