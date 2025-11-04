from flask import Flask, request, jsonify, send_file
import io
import os
import tempfile
import pandas as pd
import pdfplumber
from dateutil import parser as dateparser

app = Flask(__name__)

def normalize_amount(s):
    if s is None:
        return None
    txt = str(s).replace(",", "").replace("$", "").strip()
    neg = False
    if txt.startswith("(") and txt.endswith(")"):
        neg = True
        txt = txt[1:-1]
    try:
        val = float(txt)
        return -val if neg else val
    except Exception:
        return None

def guess_headers(cells):
    lowered = [c.lower() for c in cells]
    headers = []
    for i, c in enumerate(lowered):
        orig = cells[i] or ""
        if "date" in c:
            headers.append("Date")
        elif "descr" in c or "memo" in c or "detail" in c or "name" in c:
            headers.append("Description")
        elif "amount" in c and "balance" not in c:
            headers.append("Amount")
        elif "debit" in c:
            headers.append("Debit")
        elif "credit" in c:
            headers.append("Credit")
        elif "balance" in c:
            headers.append("Balance")
        else:
            headers.append(orig or "Col")
    # make unique
    seen = {}
    out = []
    for h in headers:
        seen[h] = seen.get(h, 0) + 1
        out.append(h if seen[h] == 1 else f"{h}_{seen[h]}")
    return out

def extract_tables(path):
    frames = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception:
                tables = None
            if not tables:
                continue
            for tbl in tables:
                if not tbl:
                    continue
                max_len = max(len(r) for r in tbl)
                norm = [r + [""] * (max_len - len(r)) for r in tbl]
                headers = guess_headers(norm[0])
                data = norm[1:] if len(norm) > 1 else []
                df = pd.DataFrame(data, columns=headers)
                frames.append(df)
    return frames

def consolidate(frames):
    if not frames:
        return pd.DataFrame()
    all_cols = []
    for f in frames:
        for c in f.columns:
            if c not in all_cols:
                all_cols.append(c)
    out = pd.DataFrame(columns=all_cols)
    for f in frames:
        out = pd.concat([out, f.reindex(columns=all_cols)], ignore_index=True)
    return out

def normalize_bank(df):
    colmap = {}
    for c in df.columns:
        cl = c.lower()
        if cl.startswith("date") and "Date" not in colmap:
            colmap["Date"] = c
        elif cl.startswith("descr") or "memo" in cl or "detail" in cl or cl == "name":
            colmap.setdefault("Description", c)
        elif cl == "amount" or ("amount" in cl and "balance" not in cl):
            colmap.setdefault("Amount", c)
        elif "debit" in cl:
            colmap.setdefault("Debit", c)
        elif "credit" in cl:
            colmap.setdefault("Credit", c)
        elif "balance" in cl:
            colmap.setdefault("Balance", c)

    out = pd.DataFrame()
    for k, v in colmap.items():
        out[k] = df[v]

    if "Amount" not in out.columns and {"Debit", "Credit"}.issubset(out.columns):
        def _amt(row):
            d = normalize_amount(row.get("Debit"))
            c = normalize_amount(row.get("Credit"))
            d = d if d is not None else 0.0
            c = c if c is not None else 0.0
            return c - d
        out["Amount"] = out.apply(_amt, axis=1)

    if "Date" in out.columns:
        def _d(x):
            try:
                return dateparser.parse(str(x), dayfirst=False, fuzzy=True).date().isoformat()
            except Exception:
                return str(x)
        out["Date"] = out["Date"].apply(_d)
    if "Amount" in out.columns:
        out["Amount"] = out["Amount"].apply(normalize_amount)
    if "Balance" in out.columns:
        out["Balance"] = out["Balance"].apply(normalize_amount)
    return out

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/extract", methods=["POST"])
def extract():
    """
    POST /extract
      - file: PDF
      - normalize: bank | none   (default: bank)
      - output: csv | json       (default: csv)
    """
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    f = request.files["file"]
    normalize = request.form.get("normalize", "bank")
    output = request.form.get("output", "csv")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        f.save(tmp.name)
        pdf_path = tmp.name

    try:
        frames = extract_tables(pdf_path)
    finally:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass

    df = consolidate(frames)
    if df.empty:
        return jsonify({"rows": 0, "columns": [], "data": []})

    if normalize == "bank":
        df = normalize_bank(df)

    if output == "json":
        return jsonify({
            "rows": int(df.shape[0]),
            "columns": list(df.columns),
            "data": df.fillna("").to_dict(orient="records")
        })
    else:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        mem = io.BytesIO(csv_buf.getvalue().encode("utf-8"))
        return send_file(mem,
                         as_attachment=True,
                         download_name="extracted.csv",
                         mimetype="text/csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
