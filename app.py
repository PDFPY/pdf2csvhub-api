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
          * { box-sizing: border-box; }
          body {
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #050816;
            color: #f9fafb;
          }
          a { color: inherit; }
          .wrapper {
            max-width: 1040px;
            margin: 0 auto;
            padding: 32px 16px 40px;
          }
          header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
          }
          .logo {
            font-weight: 700;
            letter-spacing: 0.04em;
            font-size: 18px;
          }
          .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            background: rgba(96,165,250,0.12);
            color: #bfdbfe;
            border: 1px solid rgba(96,165,250,0.4);
          }
          nav a {
            font-size: 14px;
            margin-left: 16px;
            text-decoration: none;
            color: #e5e7eb;
            opacity: 0.9;
          }
          nav a:hover { opacity: 1; }

          .hero {
            display: grid;
            grid-template-columns: minmax(0, 3fr) minmax(0, 2.4fr);
            gap: 32px;
            align-items: center;
            margin-bottom: 40px;
          }
          @media (max-width: 800px) {
            .hero {
              grid-template-columns: minmax(0, 1fr);
            }
          }
          .hero-title {
            font-size: 34px;
            line-height: 1.1;
            margin: 12px 0 12px;
          }
          .hero-sub {
            font-size: 15px;
            color: #9ca3af;
            max-width: 520px;
          }
          .hero-buttons {
            margin-top: 18px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 9px 16px;
            border-radius: 999px;
            font-size: 14px;
            border: 1px solid transparent;
            text-decoration: none;
            cursor: pointer;
          }
          .btn-primary {
            background: linear-gradient(135deg,#4f46e5,#06b6d4);
            color: white;
            border-color: transparent;
          }
          .btn-primary:hover {
            filter: brightness(1.08);
          }
          .btn-ghost {
            background: transparent;
            border-color: rgba(148,163,184,0.6);
            color: #e5e7eb;
          }
          .btn-ghost:hover {
            background: rgba(148,163,184,0.08);
          }

          .hero-card {
            background: radial-gradient(circle at top left,#1f2937,#020617);
            border-radius: 16px;
            padding: 18px 18px 16px;
            border: 1px solid rgba(148,163,184,0.4);
            font-size: 12px;
          }
          .hero-card h3 {
            font-size: 12px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #9ca3af;
            margin: 0 0 6px;
          }
          pre {
            background: rgba(15,23,42,0.9);
            border-radius: 10px;
            padding: 10px 12px;
            overflow-x: auto;
            border: 1px solid rgba(31,41,55,0.9);
            font-size: 11px;
            line-height: 1.5;
          }

          .section {
            margin-top: 32px;
          }
          .section h2 {
            font-size: 18px;
            margin-bottom: 10px;
          }
          .muted {
            font-size: 13px;
            color: #9ca3af;
            max-width: 520px;
          }
          .cards {
            display: grid;
            grid-template-columns: repeat(3,minmax(0,1fr));
            gap: 14px;
            margin-top: 14px;
          }
          @media (max-width: 900px) {
            .cards { grid-template-columns: repeat(2,minmax(0,1fr)); }
          }
          @media (max-width: 640px) {
            .cards { grid-template-columns: minmax(0,1fr); }
          }
          .card {
            border-radius: 12px;
            padding: 12px 12px 13px;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(31,41,55,0.95);
            font-size: 13px;
          }
          .card h3 {
            font-size: 14px;
            margin: 0 0 6px;
          }
          .card p {
            margin: 0;
            color: #9ca3af;
          }

          .pricing-row {
            display: grid;
            grid-template-columns: minmax(0,1.2fr) minmax(0,2fr);
            gap: 18px;
            margin-top: 16px;
          }
          @media (max-width: 700px) {
            .pricing-row { grid-template-columns: minmax(0,1fr); }
          }
          .pricing-card {
            border-radius: 12px;
            padding: 14px 14px 13px;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(55,65,81,0.9);
          }
          .price-tag {
            font-size: 22px;
            font-weight: 600;
          }
          .price-tag span {
            font-size: 12px;
            font-weight: 400;
            color: #9ca3af;
          }
          ul {
            padding-left: 18px;
          }
          footer {
            margin-top: 36px;
            border-top: 1px solid rgba(31,41,55,0.9);
            padding-top: 12px;
            font-size: 12px;
            color: #6b7280;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
          }
          footer a {
            color: #9ca3af;
            text-decoration: none;
          }
          footer a:hover { color: #e5e7eb; }
        </style>
      </head>
      <body>
        <div class="wrapper">
          <header>
            <div>
              <div class="logo">pdf2csvhub</div>
              <div class="badge">EARLY ACCESS · FREE DURING BETA</div>
            </div>
            <nav>
              <a href="#how">How it works</a>
              <a href="#api">API</a>
              <a href="#pricing">Pricing</a>
              <a href="/demo">Live demo</a>
            </nav>
          </header>

          <section class="hero">
            <div>
              <p style="font-size:12px; color:#9ca3af; margin:0 0 4px;">PDF → CSV/JSON in one call</p>
              <h1 class="hero-title">Turn bank statements & invoice PDFs into data you can actually use.</h1>
              <p class="hero-sub">
                Upload a PDF with tables and get clean rows back as CSV or JSON.
                Designed for statements, invoices and transaction reports — without writing your own parser.
              </p>
              <div class="hero-buttons">
                <a class="btn btn-primary" href="/demo">Try the live demo</a>
                <a class="btn btn-ghost" href="#api">View API usage</a>
              </div>
            </div>

            <div class="hero-card">
              <h3>API EXAMPLE</h3>
              <pre><code>POST https://api.pdf2csvhub.com/extract
Content-Type: multipart/form-data

file   = &lt;your PDF file&gt;
output = json  # or csv

# response (example)
{
  "rows": 4,
  "data": [
    ["Date","Description","Amount"],
    ["2025-01-01","Opening Bal","1000.00"],
    ["2025-01-03","Coffee Shop","-4.50"],
    ["2025-01-05","Grocery Store","-32.10"]
  ]
}</code></pre>
            </div>
          </section>

          <section id="how" class="section">
            <h2>Who it&apos;s for &amp; how it helps</h2>
            <p class="muted">
              pdf2csvhub is for people sitting on piles of PDF statements or reports who just want a structured file
              they can drop into Excel, Google Sheets or a database.
            </p>
            <div class="cards">
              <div class="card">
                <h3>Analysts & operators</h3>
                <p>Stop copy-pasting tables out of PDFs. Upload once, export CSV, and move on to the actual analysis.</p>
              </div>
              <div class="card">
                <h3>Developers</h3>
                <p>Need transaction data from a PDF in your app? Call the API and get JSON back in one step.</p>
              </div>
              <div class="card">
                <h3>Bookkeeping & finance</h3>
                <p>Turn client statements and invoices into rows you can import into your accounting tools.</p>
              </div>
            </div>
          </section>

          <section id="api" class="section">
            <h2>API usage</h2>
            <p class="muted">Base URL: <code>https://api.pdf2csvhub.com</code></p>

            <div class="cards">
              <div class="card">
                <h3>Health check</h3>
<pre><code>GET /health

# response
{"ok": true}</code></pre>
              </div>
              <div class="card">
                <h3>Extract tables</h3>
<pre><code>POST /extract
Content-Type: multipart/form-data

file   → PDF file (required)
output → "json" or "csv" (optional, default "csv")</code></pre>
              </div>
              <div class="card">
                <h3>Typical flow</h3>
                <p style="margin-bottom:4px;">1. Upload a statement or invoice PDF.</p>
                <p style="margin-bottom:4px;">2. We detect tables and extract rows.</p>
                <p>3. Save as CSV or work directly with JSON.</p>
              </div>
            </div>
          </section>

          <section id="pricing" class="section">
            <h2>Pricing</h2>
            <p class="muted">
              Early access is free while the service is in beta. Paid plans for heavier API usage are coming soon.
            </p>
            <div class="pricing-row">
              <div class="pricing-card">
                <div class="price-tag">Free <span>· during beta</span></div>
                <ul>
                  <li>Use the live demo for small/occasional files.</li>
                  <li>Reasonable API usage while we test and improve extraction.</li>
                  <li>Good way to see if it fits your workflow.</li>
                </ul>
                <a class="btn btn-primary" href="/demo">Start with the demo</a>
              </div>
              <div class="pricing-card">
                <div class="price-tag">$19/mo <span>· planned starter plan</span></div>
                <ul>
                  <li>Intended for up to ~5,000 pages/month.</li>
                  <li>Priority on improvements around your use case.</li>
                  <li>API keys and metering will be added as beta solidifies.</li>
                </ul>
                <p style="font-size:13px; color:#9ca3af;">
                  Interested in early paid access or higher volumes?
                  Email <a href="mailto:support@pdf2csvhub.com">support@pdf2csvhub.com</a> briefly describing your use case.
                </p>
              </div>
            </div>
          </section>

          <footer>
            <div>© pdf2csvhub · Early access</div>
            <div>
              <a href="/demo">Live demo</a> ·
              <a href="mailto:support@pdf2csvhub.com">Contact</a>
            </div>
          </footer>
        </div>
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
          body {
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #020617;
            color: #e5e7eb;
          }
          .wrapper {
            max-width: 640px;
            margin: 0 auto;
            padding: 32px 16px 40px;
          }
          h1 { font-size: 24px; margin-bottom: 6px; }
          p { font-size: 14px; color: #9ca3af; }
          label { display: block; margin-top: 14px; font-size: 14px; }
          input[type="file"], select {
            margin-top: 4px;
            font-size: 14px;
          }
          button {
            margin-top: 18px;
            padding: 8px 16px;
            border-radius: 999px;
            border: 1px solid transparent;
            background: linear-gradient(135deg,#4f46e5,#06b6d4);
            color: white;
            font-size: 14px;
            cursor: pointer;
          }
          button:hover { filter: brightness(1.08); }
          a { color: #9ca3af; }
          .note { font-size: 12px; color: #9ca3af; margin-top: 18px; }
        </style>
      </head>
      <body>
        <div class="wrapper">
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

          <p class="note">
            This uses the same endpoint your code would call:
            <code>POST https://api.pdf2csvhub.com/extract</code>.
          </p>

          <p class="note">
            For feedback or issues, email
            <a href="mailto:support@pdf2csvhub.com">support@pdf2csvhub.com</a>.
          </p>
        </div>
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
