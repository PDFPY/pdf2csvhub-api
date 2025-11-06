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
            margin-bottom: 28px;
          }

          .brand-main {
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .logo-mark {
            width: 26px;
            height: 26px;
            border-radius: 9px;
            background: radial-gradient(circle at top left,#38bdf8,#4f46e5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
          }

          .logo-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
          }

          .logo-name {
            font-weight: 600;
            font-size: 17px;
            letter-spacing: 0.02em;
          }

          .logo-sub {
            font-size: 11px;
            color: #9ca3af;
          }

          .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            background: rgba(56,189,248,0.14);
            color: #a5f3fc;
            border: 1px solid rgba(56,189,248,0.7);
            margin-top: 4px;
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
            grid-template-columns: minmax(0, 3.2fr) minmax(0, 2.3fr);
            gap: 24px;
            align-items: flex-start;
          }
          @media (max-width: 900px) {
            .layout {
              grid-template-columns: minmax(0, 1fr);
            }
          }

          .big-title {
            font-size: 30px;
            line-height: 1.1;
            margin: 0 0 8px;
          }
          .big-sub {
            font-size: 13px;
            color: #9ca3af;
            margin-bottom: 12px;
          }
          .quick-list {
            font-size: 12px;
            color: #9ca3af;
            padding-left: 16px;
            margin: 0 0 10px;
          }

          .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 11px;
            color: #9ca3af;
          }
          .tag {
            padding: 3px 9px;
            border-radius: 999px;
            border: 1px solid rgba(75,85,99,0.85);
            background: rgba(15,23,42,0.9);
          }

          .tool-card {
            background: radial-gradient(circle at top left, #111827, #020617 70%);
            border-radius: 18px;
            padding: 18px 18px 16px;
            border: 1px solid rgba(148,163,184,0.6);
            box-shadow: 0 18px 35px rgba(0,0,0,0.6);
          }

          .tool-title {
            font-size: 16px;
            margin: 0 0 4px;
          }
          .tool-sub {
            font-size: 12px;
            color: #9ca3af;
            margin: 0 0 10px;
          }

          form { margin: 0; }

          .drop-zone {
            border-radius: 12px;
            border: 1px dashed rgba(148,163,184,0.8);
            padding: 18px 14px;
            background: rgba(15,23,42,0.98);
            text-align: left;
            font-size: 13px;
          }
          .drop-main {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 4px;
          }
          .drop-sub {
            font-size: 12px;
            color: #9ca3af;
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
            font-size: 12px;
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
            font-size: 11px;
            color: #9ca3af;
            margin-top: 8px;
            min-height: 16px;
          }

          .result-card {
            margin-top: 14px;
            border-radius: 12px;
            background: rgba(15,23,42,0.97);
            border: 1px solid rgba(31,41,55,0.9);
            padding: 10px 12px;
            font-size: 12px;
          }
          .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
          }
          .result-meta {
            font-size: 11px;
            color: #9ca3af;
          }

          .view-toggle {
            display: inline-flex;
            border-radius: 999px;
            border: 1px solid rgba(55,65,81,0.9);
            overflow: hidden;
            font-size: 11px;
          }
          .view-toggle button {
            border: none;
            background: transparent;
            padding: 4px 10px;
            color: #9ca3af;
            cursor: pointer;
          }
          .view-toggle button.active {
            background: rgba(37,99,235,0.25);
            color: #e5e7eb;
          }

          .table-wrapper {
            max-height: 260px;
            overflow: auto;
            border-radius: 8px;
            border: 1px solid rgba(31,41,55,0.9);
            background: rgba(15,23,42,0.98);
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
          }
          thead {
            position: sticky;
            top: 0;
            background: rgba(15,23,42,1);
            z-index: 1;
          }
          th, td {
            border-bottom: 1px solid rgba(31,41,55,0.9);
            padding: 4px 6px;
            text-align: left;
            max-width: 240px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          th {
            font-weight: 500;
            color: #e5e7eb;
          }
          tbody tr:nth-child(even) {
            background: rgba(15,23,42,0.92);
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
            margin-top: 6px;
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
            <div>
              <div class="brand-main">
                <div class="logo-mark">P</div>
                <div class="logo-text">
                  <div class="logo-name">pdf2csvhub</div>
                  <div class="logo-sub">PDF → CSV / JSON for table-heavy PDFs</div>
                </div>
              </div>
              <div class="badge">EARLY ACCESS · FREE WHILE IN BETA</div>
            </div>
            <nav>
              <a href="#tool">Converter</a>
              <a href="#api">API</a>
            </nav>
          </header>

          <div class="layout">
            <!-- Left: main tool -->
            <section id="tool">
              <div class="tool-card">
                <h1 class="tool-title">Drop a PDF, get CSV or JSON back.</h1>
                <p class="tool-sub">No account needed right now. Great for bank statements, invoices and reports with tables.</p>

                <form id="convertForm">
                  <div class="drop-zone">
                    <div class="drop-main">Choose your PDF file</div>
                    <div class="drop-sub">Click below and pick a PDF from your computer.</div>
                    <input type="file" name="file" id="fileInput" accept="application/pdf" required>
                  </div>

                  <div class="field-row">
                    <div>
                      <div style="font-size:12px; color:#9ca3af;">Output format</div>
                      <select name="output" id="outputSelect">
                        <option value="json">JSON (table preview + raw)</option>
                        <option value="csv">CSV (download file)</option>
                      </select>
                    </div>
                    <div style="text-align:right; font-size:11px; color:#9ca3af;">
                      <div>Tables only · No OCR yet</div>
                      <div>Works best on digital PDFs</div>
                    </div>
                  </div>

                  <div class="buttons-row">
                    <button type="submit" class="btn btn-primary" id="convertBtn">
                      Convert PDF
                    </button>
                    <button type="button" class="btn btn-secondary" id="clearBtn">
                      Clear
                    </button>
                  </div>

                  <div class="status-line" id="statusText"></div>

                  <div class="result-card" id="resultCard" style="display:none;">
                    <div class="result-header">
                      <div>
                        <strong>Result</strong>
                        <span class="result-meta" id="resultMeta"></span>
                      </div>
                      <div class="view-toggle">
                        <button type="button" id="viewTableBtn" class="active">Table</button>
                        <button type="button" id="viewJsonBtn">JSON</button>
                      </div>
                    </div>
                    <div id="tableView" class="table-wrapper" style="display:none;">
                      <table>
                        <thead id="tableHead"></thead>
                        <tbody id="tableBody"></tbody>
                      </table>
                    </div>
                    <div id="jsonView" style="display:none; max-height:260px; overflow:auto; border-radius:8px; border:1px solid rgba(31,41,55,0.9); padding:8px 10px; background:rgba(15,23,42,0.98);">
                      <pre id="resultPre"></pre>
                    </div>
                    <div class="small-note">
                      Preview shows the first few rows. Use JSON or CSV output in the API for full data.
                    </div>
                  </div>
                </form>
              </div>
            </section>

            <!-- Right: ultra-short explanation -->
            <section>
              <h2 class="big-title">Made for “just give me the rows” people.</h2>
              <p class="big-sub">
                You shouldn&apos;t have to fight your bank or invoicing software just to get data into a spreadsheet.
                pdf2csvhub turns table-heavy PDFs into rows you can drop into Excel, Google Sheets, or your own tools.
              </p>
              <ul class="quick-list">
                <li>Upload a PDF with tables.</li>
                <li>We flatten the tables into rows.</li>
                <li>Download CSV or work with JSON.</li>
              </ul>
              <div class="tag-row">
                <div class="tag">No sign-up during beta</div>
                <div class="tag">Free for light usage</div>
                <div class="tag">Simple API for automation</div>
              </div>
            </section>
          </div>

          <section id="api" style="margin-top:26px;">
            <h3 style="font-size:16px; margin-bottom:6px;">API basics</h3>
            <p style="font-size:12px; color:#9ca3af; margin-bottom:10px;">
              Base URL: <code>https://api.pdf2csvhub.com</code>
            </p>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; font-size:12px;">
              <div style="border-radius:10px; padding:9px 11px; background:rgba(15,23,42,0.97); border:1px solid rgba(31,41,55,0.9);">
                <strong>Health check</strong>
                <pre>{ "method": "GET", "path": "/health" }</pre>
              </div>
              <div style="border-radius:10px; padding:9px 11px; background:rgba(15,23,42,0.97); border:1px solid rgba(31,41,55,0.9);">
                <strong>Extract tables</strong>
                <pre>POST /extract
Content-Type: multipart/form-data

file   → PDF file (required)
output → "json" or "csv" (optional, default "csv")</pre>
              </div>
              <div style="border-radius:10px; padding:9px 11px; background:rgba(15,23,42,0.97); border:1px solid rgba(31,41,55,0.9);">
                <strong>Example JSON response</strong>
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
            const resultMeta = document.getElementById('resultMeta');
            const resultPre = document.getElementById('resultPre');

            const tableView = document.getElementById('tableView');
            const jsonView = document.getElementById('jsonView');
            const tableHead = document.getElementById('tableHead');
            const tableBody = document.getElementById('tableBody');
            const viewTableBtn = document.getElementById('viewTableBtn');
            const viewJsonBtn = document.getElementById('viewJsonBtn');

            let lastData = null;

            function setStatus(msg) {
              statusText.textContent = msg || '';
            }

            function setView(mode) {
              if (mode === 'table') {
                tableView.style.display = 'block';
                jsonView.style.display = 'none';
                viewTableBtn.classList.add('active');
                viewJsonBtn.classList.remove('active');
              } else {
                tableView.style.display = 'none';
                jsonView.style.display = 'block';
                viewJsonBtn.classList.add('active');
                viewTableBtn.classList.remove('active');
              }
            }

            function clearResult() {
              resultCard.style.display = 'none';
              resultMeta.textContent = '';
              resultPre.textContent = '';
              tableHead.innerHTML = '';
              tableBody.innerHTML = '';
              lastData = null;
              setStatus('');
            }

            clearBtn.addEventListener('click', function() {
              clearResult();
              fileInput.value = '';
            });

            viewTableBtn.addEventListener('click', function() {
              if (!lastData) return;
              setView('table');
            });

            viewJsonBtn.addEventListener('click', function() {
              if (!lastData) return;
              setView('json');
            });

            function renderTable(data) {
              const rows = Array.isArray(data.data) ? data.data : [];
              if (!rows.length) {
                tableHead.innerHTML = '<tr><th>No rows found</th></tr>';
                tableBody.innerHTML = '';
                return;
              }

              const maxPreviewRows = 12;
              const previewRows = rows.slice(0, maxPreviewRows);
              const headerRow = previewRows[0] || [];
              const bodyRows = previewRows.slice(1);

              const maxCols = Math.max(...previewRows.map(r => r.length));
              const safeHeader = headerRow.concat(Array(maxCols - headerRow.length).fill(''));

              tableHead.innerHTML = '<tr>' + safeHeader.map(c => '<th>' + String(c || '') + '</th>').join('') + '</tr>';

              tableBody.innerHTML = bodyRows.map(r => {
                const safeRow = r.concat(Array(maxCols - r.length).fill(''));
                return '<tr>' + safeRow.map(c => '<td>' + String(c || '') + '</td>').join('') + '</tr>';
              }).join('');

              if (rows.length > maxPreviewRows) {
                const extra = rows.length - maxPreviewRows;
                const colspan = maxCols || 1;
                tableBody.innerHTML += '<tr><td colspan="' + colspan + '">… +' + extra + ' more row(s) not shown</td></tr>';
              }
            }

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
              setStatus('Uploading and converting…');

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
                  lastData = data;
                  const rows = typeof data.rows === 'number' ? data.rows : (Array.isArray(data.data) ? data.data.length : 0);
                  resultMeta.textContent = ' · ' + rows + ' row(s)';
                  let pretty = JSON.stringify(data, null, 2);
                  if (pretty.length > 8000) {
                    pretty = pretty.slice(0, 8000) + '\\n… (truncated preview)';
                  }
                  resultPre.textContent = pretty;

                  renderTable(data);
                  resultCard.style.display = 'block';
                  setView('table');
                  setStatus('Done. Showing preview.');
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
