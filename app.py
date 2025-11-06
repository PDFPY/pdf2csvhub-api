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
                tables = pdf.pages[pdf.pages.index(page)].extract_tables()
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
        <title>pdf2csvhub – PDF to CSV/JSON</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top, #0f172a 0, #020617 45%, #000 100%);
            color: #e5e7eb;
          }
          a { color: inherit; text-decoration: none; }

          .shell {
            max-width: 1040px;
            margin: 0 auto;
            padding: 24px 16px 40px;
          }

          header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 32px;
          }

          .brand {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .logo {
            font-weight: 700;
            letter-spacing: 0.08em;
            font-size: 18px;
            text-transform: uppercase;
          }

          .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            background: rgba(56,189,248,0.14);
            color: #a5f3fc;
            border: 1px solid rgba(56,189,248,0.7);
          }

          nav {
            font-size: 13px;
            color: #9ca3af;
          }
          nav a {
            margin-left: 14px;
            opacity: 0.9;
          }
          nav a:hover { opacity: 1; color: #e5e7eb; }

          .layout {
            display: grid;
            grid-template-columns: minmax(0, 3fr) minmax(0, 2.5fr);
            gap: 26px;
            align-items: stretch;
          }
          @media (max-width: 900px) {
            .layout {
              grid-template-columns: minmax(0, 1fr);
            }
          }

          .hero-title {
            font-size: 34px;
            line-height: 1.1;
            margin: 4px 0 10px;
          }
          .hero-kicker {
            font-size: 12px;
            color: #9ca3af;
            letter-spacing: 0.12em;
            text-transform: uppercase;
          }
          .hero-sub {
            font-size: 14px;
            color: #9ca3af;
            max-width: 520px;
          }
          .hero-list {
            margin-top: 16px;
            padding-left: 18px;
            font-size: 13px;
            color: #9ca3af;
          }

          .tag-row {
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 11px;
            color: #9ca3af;
          }
          .tag {
            padding: 3px 9px;
            border-radius: 999px;
            border: 1px solid rgba(75,85,99,0.8);
            background: rgba(15,23,42,0.9);
          }

          .upload-card {
            background: radial-gradient(circle at top left, #1f2937, #020617);
            border-radius: 18px;
            padding: 18px 18px 16px;
            border: 1px solid rgba(148,163,184,0.6);
            box-shadow: 0 18px 35px rgba(0,0,0,0.6);
          }

          .upload-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
          }
          .upload-header h2 {
            font-size: 15px;
            margin: 0;
          }
          .pill {
            font-size: 11px;
            padding: 3px 10px;
            border-radius: 999px;
            background: rgba(22,163,74,0.1);
            border: 1px solid rgba(34,197,94,0.6);
            color: #bbf7d0;
          }

          form {
            margin: 0;
          }

          .drop-zone {
            margin-top: 6px;
            border-radius: 12px;
            border: 1px dashed rgba(148,163,184,0.7);
            padding: 18px 14px;
            background: rgba(15,23,42,0.95);
            text-align: left;
            font-size: 13px;
          }
          .drop-zone strong {
            display: block;
            margin-bottom: 4px;
          }
          .drop-zone input[type="file"] {
            margin-top: 10px;
            font-size: 12px;
          }

          .field-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 14px;
            gap: 10px;
            font-size: 13px;
          }
          .field-row select {
            background: #020617;
            color: #e5e7eb;
            border-radius: 999px;
            border: 1px solid rgba(55,65,81,0.9);
            padding: 6px 9px;
            font-size: 12px;
          }

          .buttons-row {
            margin-top: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 16px;
            border-radius: 999px;
            font-size: 13px;
            border: 1px solid transparent;
            cursor: pointer;
          }
          .btn-primary {
            background: linear-gradient(135deg,#4f46e5,#06b6d4);
            color: white;
            border-color: transparent;
          }
          .btn-primary[disabled] {
            opacity: 0.5;
            cursor: default;
          }
          .btn-secondary {
            background: transparent;
            border-color: rgba(148,163,184,0.7);
            color: #e5e7eb;
          }
          .btn-secondary:hover {
            background: rgba(15,23,42,0.9);
          }

          .status-line {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 8px;
            min-height: 16px;
          }

          .result-card {
            margin-top: 14px;
            border-radius: 12px;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(31,41,55,0.9);
            padding: 10px 12px;
            font-size: 12px;
          }
          .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
          }
          .result-header span {
            color: #9ca3af;
          }
          .result-body {
            max-height: 260px;
            overflow: auto;
          }
          pre {
            margin: 0;
            font-size: 11px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
          }

          .small-note {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 8px;
          }

          footer {
            margin-top: 32px;
            padding-top: 10px;
            border-top: 1px solid rgba(31,41,55,0.9);
            font-size: 11px;
            color: #6b7280;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
          }
          footer a { color: #9ca3af; }
          footer a:hover { color: #e5e7eb; }
        </style>
      </head>
      <body>
        <div class="shell">
          <header>
            <div class="brand">
              <div class="logo">pdf2csvhub</div>
              <div class="badge">EARLY ACCESS · FREE WHILE IN BETA</div>
            </div>
            <nav>
              <a href="#tool">Converter</a>
              <a href="#how">How it works</a>
              <a href="#api">API</a>
            </nav>
          </header>

          <div class="layout">
            <!-- Left: marketing copy -->
            <section>
              <p class="hero-kicker">PDF ➝ CSV / JSON · TABLES ONLY</p>
              <h1 class="hero-title">Turn bank statements & invoice PDFs into structured data in seconds.</h1>
              <p class="hero-sub">
                Drop in a PDF with tables and get rows back as CSV or JSON. Built for statements, invoices and
                transaction reports — without having to write your own parser.
              </p>
              <ul class="hero-list">
                <li>Perfect for Excel / Google Sheets imports.</li>
                <li>Designed for table-heavy PDFs (statements, reports, exports).</li>
                <li>Simple API for developers, no heavy SDKs.</li>
              </ul>

              <div class="tag-row">
                <div class="tag">No sign-up required during beta</div>
                <div class="tag">Free for light usage</div>
                <div class="tag">API-ready response format</div>
              </div>
            </section>

            <!-- Right: main tool card -->
            <section id="tool">
              <div class="upload-card">
                <div class="upload-header">
                  <h2>Try it now</h2>
                  <div class="pill">Live converter</div>
                </div>
                <p style="margin:0; font-size:12px; color:#9ca3af;">
                  Upload a PDF with at least one table. For best results, use digital PDFs (not blurry scans).
                </p>

                <form id="convertForm">
                  <div class="drop-zone">
                    <strong>PDF file</strong>
                    <span style="font-size:12px; color:#9ca3af;">Click to choose a file from your device.</span>
                    <br>
                    <input type="file" name="file" id="fileInput" accept="application/pdf" required>
                  </div>

                  <div class="field-row">
                    <div>
                      <div style="font-size:12px; color:#9ca3af;">Output format</div>
                      <select name="output" id="outputSelect">
                        <option value="json">JSON (preview on this page)</option>
                        <option value="csv">CSV (download as file)</option>
                      </select>
                    </div>
                    <div style="text-align:right; font-size:11px; color:#9ca3af;">
                      <div>Tables only · No OCR yet</div>
                      <div>Great for statements / invoice exports</div>
                    </div>
                  </div>

                  <div class="buttons-row">
                    <button type="submit" class="btn btn-primary" id="convertBtn">
                      Convert PDF
                    </button>
                    <button type="button" class="btn btn-secondary" id="clearBtn">
                      Clear result
                    </button>
                  </div>

                  <div class="status-line" id="statusText"></div>

                  <div class="result-card" id="resultCard" style="display:none;">
                    <div class="result-header">
                      <strong>Result</strong>
                      <span id="resultMeta"></span>
                    </div>
                    <div class="result-body">
                      <pre id="resultPre"></pre>
                    </div>
                    <div class="small-note">
                      JSON is truncated in this preview if it&apos;s very large. Use the API for programmatic access.
                    </div>
                  </div>
                </form>
              </div>
            </section>
          </div>

          <!-- How it works / API sections -->
          <section id="how" class="section" style="margin-top:32px;">
            <h2 style="font-size:18px; margin-bottom:8px;">How it works</h2>
            <p style="font-size:13px; color:#9ca3af; max-width:520px;">
              pdf2csvhub looks through each page of your PDF, detects tabular regions, and flattens them into rows.
              You can export directly to CSV for spreadsheets, or work with JSON if you&apos;re integrating this into
              an app or script.
            </p>
          </section>

          <section id="api" class="section" style="margin-top:20px;">
            <h2 style="font-size:18px; margin-bottom:8px;">API usage</h2>
            <p style="font-size:13px; color:#9ca3af;">Base URL: <code>https://api.pdf2csvhub.com</code></p>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; margin-top:10px;">
              <div style="border-radius:12px; padding:10px 12px; background:rgba(15,23,42,0.96); border:1px solid rgba(31,41,55,0.9); font-size:12px;">
                <strong>Health check</strong>
                <pre>{ "method": "GET", "path": "/health" }</pre>
              </div>
              <div style="border-radius:12px; padding:10px 12px; background:rgba(15,23,42,0.96); border:1px solid rgba(31,41,55,0.9); font-size:12px;">
                <strong>Extract tables</strong>
                <pre>POST /extract
Content-Type: multipart/form-data

file   → PDF file (required)
output → "json" or "csv" (optional, default "csv")</pre>
              </div>
              <div style="border-radius:12px; padding:10px 12px; background:rgba(15,23,42,0.96); border:1px solid rgba(31,41,55,0.9); font-size:12px;">
                <strong>Example response (JSON)</strong>
                <pre>{
  "rows": 4,
  "data": [
    ["Date","Description","Amount"],
    ["2025-01-01","Opening Bal","1000.00"],
    ["2025-01-03","Coffee Shop","-4.50"],
    ["2025-01-05","Grocery Store","-32.10"]
  ]
}</pre>
              </div>
            </div>
          </section>

          <footer>
            <div>© pdf2csvhub · Early access</div>
            <div>
              <a href="mailto:support@pdf2csvhub.com">Contact</a>
            </div>
          </footer>
        </div>

        <script>
          (function() {
            const form = document.getElementById('convertForm');
            const fileInput = document.getElementById('fileInput');
            const outputSelect = document.getElementById('outputSelect');
            const convertBtn = document.getElementById('convertBtn');
            const clearBtn = document.getElementById('clearBtn');
            const statusText = document.getElementById('statusText');
            const resultCard = document.getElementById('resultCard');
            const resultPre = document.getElementById('resultPre');
            const resultMeta = document.getElementById('resultMeta');

            function setStatus(msg) {
              statusText.textContent = msg || '';
            }

            function clearResult() {
              resultCard.style.display = 'none';
              resultPre.textContent = '';
              resultMeta.textContent = '';
              setStatus('');
            }

            clearBtn.addEventListener('click', function() {
              clearResult();
              fileInput.value = '';
            });

            form.addEventListener('submit', async function(e) {
              e.preventDefault();
              clearResult();

              if (!fileInput.files || !fileInput.files.length) {
                setStatus('Please choose a PDF file first.');
                return;
              }

              const output = outputSelect.value;
              const formData = new FormData();
              formData.append('file', fileInput.files[0]);
              formData.append('output', output);

              convertBtn.disabled = true;
              setStatus('Uploading and converting...');

              try {
                const resp = await fetch('/extract', {
                  method: 'POST',
                  body: formData
                });

                if (!resp.ok) {
                  let text = '';
                  try { text = await resp.text(); } catch (_) {}
                  setStatus('Error from server: ' + resp.status + (text ? ' – ' + text.slice(0, 120) : ''));
                  convertBtn.disabled = false;
                  return;
                }

                if (output === 'json') {
                  const data = await resp.json();
                  const rows = typeof data.rows === 'number' ? data.rows : 'unknown';
                  resultMeta.textContent = rows + ' row(s)';
                  let pretty = JSON.stringify(data, null, 2);
                  if (pretty.length > 8000) {
                    pretty = pretty.slice(0, 8000) + '\\n... (truncated preview)';
                  }
                  resultPre.textContent = pretty;
                  resultCard.style.display = 'block';
                  setStatus('Done. Showing JSON preview.');
                } else {
                  // CSV: download as file
                  const blob = await resp.blob();
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'extracted.csv';
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  URL.revokeObjectURL(url);
                  setStatus('CSV downloaded. Open it in Excel, Sheets, or your CSV viewer.');
                }
              } catch (err) {
                console.error(err);
                setStatus('Something went wrong while talking to the server.');
              } finally {
                convertBtn.disabled = false;
              }
            });
          })();
        </script>
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
