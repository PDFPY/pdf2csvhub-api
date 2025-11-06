from flask import Flask, request, jsonify, send_file
import io
import os
import tempfile
import pdfplumber
import csv

app = Flask(__name__)

def extract_tables(path):
    """
    Extract all tables from all pages as a single list of rows.
    Each row is a list of cell values (strings).
    """
    rows = []
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
                for r in tbl:
                    rows.append([(cell if cell is not None else "") for cell in r])
    return rows

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})
@app.route("/", methods=["GET"])
def home():
    @app.route("/demo", methods=["GET"])
def demo():
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>pdf2csvhub Demo</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; line-height: 1.6; }
          h1 { font-size: 24px; margin-bottom: 10px; }
          label { display: block; margin-top: 12px; }
          button { margin-top: 16px; padding: 8px 16px; }
        </style>
      </head>
      <body>
        <h1>pdf2csvhub Demo</h1>
        <p>Upload a PDF with tables and get CSV or JSON back from the API.</p>

        <form action="/extract" method="post" enctype="multipart/form-data">
          <label>
            PDF file:
            <input type="file" name="file" required>
          </label>

          <label>
            Output format:
            <select name="output">
              <option value="json">JSON (view in browser)</option>
              <option value="csv">CSV (download file)</option>
            </select>
          </label>

          <button type="submit">Convert</button>
        </form>

        <p style="font-size: 13px; color: #555; margin-top: 24px;">
          This form calls <code>POST /extract</code> on this same server.
        </p>
      </body>
    </html>
    """

    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>pdf2csvhub – PDF to CSV/JSON API</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; }
          h1 { font-size: 28px; margin-bottom: 10px; }
          code { background: #f3f3f3; padding: 2px 4px; border-radius: 3px; }
          .box { border: 1px solid #ddd; padding: 16px; border-radius: 8px; margin-top: 16px; }
          .small { font-size: 13px; color: #555; }
        </style>
      </head>
      <body>
        <h1>pdf2csvhub</h1>
        <p>Turn PDF tables (bank statements, invoices, reports) into CSV or JSON with a simple API.</p>

        <div class="box">
          <h2>Health check</h2>
          <p>Check if the API is up:</p>
          <pre><code>GET https://api.pdf2csvhub.com/health</code></pre>
        </div>

        <div class="box">
          <h2>Extract tables from a PDF</h2>
          <p>Endpoint:</p>
          <pre><code>POST https://api.pdf2csvhub.com/extract</code></pre>
          <p>Send as <code>multipart/form-data</code> with:</p>
          <ul>
            <li><code>file</code> – the PDF file (required)</li>
            <li><code>output</code> – <code>json</code> or <code>csv</code> (optional, default <code>csv</code>)</li>
          </ul>
          <p>Example JSON response:</p>
<pre><code>{
  "rows": 4,
  "data": [
    ["Date","Description","Amount"],
    ["2025-01-01","Opening Bal","1000.00"],
    ["2025-01-03","Coffee Shop","-4.50"],
    ["2025-01-05","Grocery Store","-32.10"]
  ]
}</code></pre>
        </div>

        <p class="small">
          Support: <a href="mailto:support@pdf2csvhub.com">support@pdf2csvhub.com</a>
        </p>
      </body>
    </html>
    """

@app.route("/extract", methods=["POST"])
def extract():
    """
    POST /extract
      - file: PDF (required)
      - output: csv | json (default: csv)

    This version:
      - extracts all tables it can find
      - returns them as CSV or JSON (flat list of rows).
    """
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    f = request.files["file"]
    output = request.form.get("output", "csv")

    # save the uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        f.save(tmp.name)
        pdf_path = tmp.name

    try:
        rows = extract_tables(pdf_path)
    finally:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass

    if not rows:
        # no tables found
        if output == "json":
            return jsonify({"rows": 0, "data": []})
        else:
            return jsonify({"rows": 0, "message": "no tables found"})

    if output == "json":
        return jsonify({"rows": len(rows), "data": rows})
    else:
        # CSV: write to an in-memory file
        max_cols = max(len(r) for r in rows)
        normalized = [r + [""] * (max_cols - len(r)) for r in rows]

        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerows(normalized)

        mem = io.BytesIO(csv_buf.getvalue().encode("utf-8"))
        return send_file(
            mem,
            as_attachment=True,
            download_name="extracted.csv",
            mimetype="text/csv"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)


