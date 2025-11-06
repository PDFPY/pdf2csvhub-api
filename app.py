from flask import Flask, request, jsonify, send_file
import io
import os
import tempfile
import csv
import pdfplumber

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
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>pdf2csvhub – PDF to CSV/JSON API</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.6; }
          h1 { font-size: 30px; margin-bottom: 4px; }
          h2 { font-size: 22px; margin-top: 24px; }
          code { background: #f3f3f3; padding: 2px 4px; border-radius: 3px; }
          .tagline { color: #444; margin-bottom: 20px; }
          .box { border: 1px solid #ddd; padding: 16px; border-radius: 8px; margin-top: 16px; }
          .small { font-size: 13px; color: #555; }
          a.button {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 6px;
            border: 1px solid #333;
            text-decoration: none;
            color: #fff;
            background: #333;
            margin-top: 8px;
          }
          a.button:hover { background: #000; }
        </style>
      </head>
      <body>
        <h1>pdf2csvhub</h1>
        <p class="tagline">
          Turn PDF tables (bank statements, invoices, reports) into clean CSV or JSON with a simple API.
        </p>

        <div class="box">
          <h2>Who this is for</h2>
          <ul>
            <li>People with bank statements, invoices, or reports stuck in PDF</li>
            <li>Who want the data in Excel/Sheets quickly</li>
            <li>And don&apos;t want to manually copy/paste tables</li>
          </ul>
        </div>

        <div class="box">
          <h2>How it works</h2>
          <ol>
            <li>Upload a PDF with tables.</li>
            <li>We detect the tables and extract the rows.</li>
            <li>You get back CSV (download) or JSON (for code).</li>
          </ol>
          <p>
            Try it in your browser:
            <br>
            <a class="button" href="/demo">Open the demo</a>
          </p>
        </div>

        <div class="box">
          <h2>API usage</h2>
          <p>Base URL: <code>https://api.pdf2csvhub.com</code></p>

          <p><strong>Health check</strong></p>
          <pre><code>GET /health
→ {"ok": true}</code></pre>

          <p><strong>Extract tables from a PDF</strong></p>
<pre><code>POST /extract
Content-Type: multipart/form-data

Fields:
  file   → PDF file (required)
  output → "json" or "csv" (optional, default "csv")</code></pre>

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

        <div class="box">
          <h2>Pricing (starter)</h2>
          <ul>
            <li><strong>Free</strong>: use the demo page for small files.</li>
            <li><strong>$19/month</strong>: API access for up to 5,000 pages/month.<br>
                (Manual onboarding for now – email to get access.)</li>
          </ul>
          <p class="small">
            To discuss access or higher volumes, email
            <a href="mailto:support@pdf2csvhub.com">support@pdf2csvhub.com</a>.
          </p>
        </div>

        <p class="small">
          Demo: <a href="/demo">/demo</a><br>
          Health: <code>/health</code> · API: <code>/extract</code>
        </p>
      </body>
    </html>
    """


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
          .small { font-size: 13px; color: #555; margin-top: 24px; }
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

        <p class="small">
          This form calls <code>POST /extract</code> on this same server.
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
