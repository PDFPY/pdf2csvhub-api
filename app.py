from flask import Flask, request, jsonify, send_file
import io
import os
import tempfile
import csv
import pdfplumber

app = Flask(__name__)


def extract_tables(path):
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
            max-width: 960px;
            margin: 0 auto;
            padding: 24px 16px 40px;
          }

          header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 24px;
          }

          .logo-name {
            font-weight: 700;
            font-size: 26px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }
          .logo-two {
            position: relative;
            display: inline-block;
            padding: 0 4px;
            margin: 0 2px;
            background: linear-gradient(135deg,#38bdf8,#4f46e5);
            border-radius: 6px;
            color: #0b1120;
          }
          .logo-two::after {
            content: "→";
            position: absolute;
            right: -12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 13px;
            color: #38bdf8;
          }
          .badge {
            display: inline-block;
            margin-top: 4px;
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
          nav a { margin-left: 14px; opacity: 0.9; }
          nav a:hover { opacity: 1; color: #e5e7eb; }

          .layout {
            display: grid;
            grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
            gap: 24px;
          }
          @media (max-width: 900px) {
            .layout { grid-template-columns: minmax(0, 1fr); }
          }

          .tool-card {
            background: radial-gradient(circle at top left, #111827, #020617 70%);
            border-radius: 18px;
            padding: 18px;
            border: 1px solid rgba(148,163,184,0.6);
            box-shadow: 0 18px 35px rgba(0,0,0,0.6);
          }
          .tool-title {
            font-size: 18px;
            margin: 0 0 6px;
          }
          .tool-sub {
            font-size: 12px;
            color: #9ca3af;
            margin: 0 0 14px;
          }

          .drop-label {
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 6px;
          }
          .drop-zone {
            border-radius: 14px;
            border: 1px dashed rgba(148,163,184,0.9);
            padding: 22px 14px;
            background: rgba(15,23,42,0.98);
            text-align: center;
            cursor: pointer;
          }
          .drop-inner {
            max-width: 360px;
            margin: 0 auto;
          }
          .drop-icon {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            border: 1px solid rgba(96,165,250,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px;
            font-size: 24px;
            color: #bfdbfe;
          }
          .drop-main {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 4px;
          }
          .drop-sub {
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 12px;
          }
          .file-name {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 8px;
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
          }
          .btn-secondary {
            background: transparent;
            border-color: rgba(148,163,184,0.7);
            color: #e5e7eb;
          }
          .btn-secondary:hover {
            background: rgba(15,23,42,0.9);
          }

          .field-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 16px;
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
          th { font-weight: 500; color: #e5e7eb; }
          tbody tr:nth-child(even) { background: rgba(15,23,42,0.92); }

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
            margin-top: 28px;
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
              <div class="logo-name">
                PDF <span class="logo-two">2</span> CSV HUB
              </div>
              <div class="badge">EARLY ACCESS · FREE WHILE IN BETA</div>
            </div>
            <nav>
              <a href="#tool">Converter</a>
              <a href="#api">API</a>
            </nav>
          </header>

          <div class="layout">
            <section id="tool">
              <div class="tool-card">
                <h1 class="tool-title">Drop a PDF, get CSV or JSON back.</h1>
                <p class="tool-sub">
                  No account needed right now. Built for bank statements, invoices and reports with tables.
                </p>

                <form id="convertForm">
                  <div class="drop-label">Upload your PDF</div>
                  <div class="drop-zone" id="dropZone">
                    <div class="drop-inner">
                      <div class="drop-icon">📄</div>
                      <div class="drop-main">Drag & drop your PDF here</div>
                      <div class="drop-sub">or click the button below to choose a file</div>
                      <label for="fileInput" class="btn btn-primary">Choose PDF</label>
                      <input type="file" name="file" id="fileInput" accept="application/pdf" required hidden>
                      <div class="file-name" id="fileName">No file selected</div>
                    </div>
                  </div>

                  <div class="field-row">
                    <div>
                      <div style="font-size:12px; color:#9ca3af;">Output format</div>
                      <select name="output" id="outputSelect">
                        <option value="json">JSON (table preview)</option>
                        <option value="csv">CSV (download)</option>
                      </select>
                    </div>
                    <div style="text-align:right; font-size:11px; color:#9ca3af;">
                      <div>Tables only · No OCR yet</div>
                      <div>Works best on digital PDFs</div>
                    </div>
                  </div>

                  <div class="buttons-row">
                    <button type="submit" class="btn btn-primary" id="convertBtn">Convert PDF</button>
                    <button type="button" class="btn btn-secondary" id="clearBtn">Clear</button>
                  </div>

                  <div class="status-line" id="statusText"></div>

                  <div class="result-card" id="resultCard" style="display:none;">
                    <div class="result-header">
                      <div>
                        <strong>Result</strong>
                        <span class="result-meta" id="resultMeta"></span>
                      </div>
                    </div>
                    <div class="table-wrapper" id="tableWrapper" style="display:none;">
                      <table>
                        <thead id="tableHead"></thead>
                        <tbody id="tableBody"></tbody>
                      </table>
                    </div>
                    <div id="jsonWrapper" style="display:none; max-height:260px; overflow:auto; border-radius:8px; border:1px solid rgba(31,41,55,0.9); padding:8px 10px; background:rgba(15,23,42,0.98);">
                      <pre id="resultPre"></pre>
                    </div>
                    <div class="small-note">
                      Preview shows the first few rows. Use JSON or CSV output in the API for full data.
                    </div>
                  </div>
                </form>
              </div>
            </section>

            <section>
              <h2 style="font-size:22px; margin:0 0 8px;">Made for “just give me the rows” people.</h2>
              <p style="font-size:13px; color:#9ca3af; margin:0 0 10px;">
                Drop in a PDF with tables, get rows you can paste into Excel, Google Sheets or your own tools.
              </p>
              <ul style="font-size:12px; color:#9ca3af; padding-left:18px; margin:0 0 10px;">
                <li>Upload a PDF with tables.</li>
                <li>We flatten the tables into rows.</li>
                <li>Download CSV or work with JSON.</li>
              </ul>
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
            </div>
          </section>

          <footer>
            <div>© pdf2csvhub · Early access</div>
            <div><a href="mailto:support@pdf2csvhub.com">Contact</a></div>
          </footer>
        </div>

        <script>
          (function() {
            var form = document.getElementById('convertForm');
            var fileInput = document.getElementById('fileInput');
            var fileNameEl = document.getElementById('fileName');
            var dropZone = document.getElementById('dropZone');
            var outputSelect = document.getElementById('outputSelect');
            var convertBtn = document.getElementById('convertBtn');
            var clearBtn = document.getElementById('clearBtn');
            var statusText = document.getElementById('statusText');

            var resultCard = document.getElementById('resultCard');
            var resultMeta = document.getElementById('resultMeta');
            var resultPre = document.getElementById('resultPre');
            var tableWrapper = document.getElementById('tableWrapper');
            var jsonWrapper = document.getElementById('jsonWrapper');
            var tableHead = document.getElementById('tableHead');
            var tableBody = document.getElementById('tableBody');

            function setStatus(msg) {
              statusText.textContent = msg || '';
            }

            function updateFileName() {
              if (!fileInput.files || !fileInput.files.length) {
                fileNameEl.textContent = 'No file selected';
              } else {
                fileNameEl.textContent = fileInput.files[0].name;
              }
            }

            fileInput.addEventListener('change', updateFileName);

            dropZone.addEventListener('click', function() {
              fileInput.click();
            });

            dropZone.addEventListener('dragover', function(e) {
              e.preventDefault();
            });

            dropZone.addEventListener('drop', function(e) {
              e.preventDefault();
              var files = e.dataTransfer && e.dataTransfer.files;
              if (!files || !files.length) return;
              var file = files[0];
              if (file.type === 'application/pdf' || file.name.toLowerCase().indexOf('.pdf') !== -1) {
                fileInput.files = files;
                updateFileName();
                setStatus('');
              } else {
                setStatus('Please drop a PDF file.');
              }
            });

            function clearResult() {
              resultCard.style.display = 'none';
              resultMeta.textContent = '';
              resultPre.textContent = '';
              tableHead.innerHTML = '';
              tableBody.innerHTML = '';
              tableWrapper.style.display = 'none';
              jsonWrapper.style.display = 'none';
            }

            clearBtn.addEventListener('click', function() {
              clearResult();
              fileInput.value = '';
              updateFileName();
              setStatus('');
            });

            form.addEventListener('submit', function(e) {
              e.preventDefault();
              clearResult();

              if (!fileInput.files || !fileInput.files.length) {
                setStatus('Please choose a PDF file first.');
                return;
              }

              var output = outputSelect.value;
              var formData = new FormData();
              formData.append('file', fileInput.files[0]);
              formData.append('output', output);

              convertBtn.disabled = true;
              setStatus('Uploading and converting…');

              fetch('/extract', {
                method: 'POST',
                body: formData
              }).then(function(resp) {
                if (!resp.ok) {
                  return resp.text().then(function(t) {
                    throw new Error('Error from server: ' + resp.status + (t ? ' – ' + t.slice(0, 120) : ''));
                  });
                }
                if (output === 'json') {
                  return resp.json().then(function(data) {
                    var rows = Array.isArray(data.data) ? data.data.length : 0;
                    resultMeta.textContent = ' · ' + rows + ' row(s)';
                    var pretty = JSON.stringify(data, null, 2);
                    if (pretty.length > 8000) {
                      pretty = pretty.slice(0, 8000) + '\\n… (truncated preview)';
                    }
                    resultPre.textContent = pretty;

                    if (Array.isArray(data.data) && data.data.length) {
                      var preview = data.data.slice(0, 12);
                      var header = preview[0];
                      var bodyRows = preview.slice(1);
                      tableHead.innerHTML = '';
                      tableBody.innerHTML = '';

                      if (header) {
                        var ths = header.map(function(c) {
                          return '<th>' + String(c || '') + '</th>';
                        }).join('');
                        tableHead.innerHTML = '<tr>' + ths + '</tr>';
                      }

                      bodyRows.forEach(function(r) {
                        var tds = r.map(function(c) {
                          return '<td>' + String(c || '') + '</td>';
                        }).join('');
                        tableBody.innerHTML += '<tr>' + tds + '</tr>';
                      });

                      tableWrapper.style.display = 'block';
                    } else {
                      tableWrapper.style.display = 'none';
                    }

                    jsonWrapper.style.display = 'block';
                    resultCard.style.display = 'block';
                    setStatus('Done. Showing preview.');
                  });
                } else {
                  return resp.blob().then(function(blob) {
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = 'extracted.csv';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);
                    setStatus('CSV downloaded. Open it in Excel, Sheets, or your CSV viewer.');
                  });
                }
              }).catch(function(err) {
                console.error(err);
                setStatus(err.message || 'Something went wrong while talking to the server.');
              }).finally(function() {
                convertBtn.disabled = false;
              });
            });
          })();
        </script>
      </body>
    </html>
    """


@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    f = request.files["file"]
    output = request.form.get("output", "csv")

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
        if output == "json":
            return jsonify({"rows": 0, "data": []})
        else:
            return jsonify({"rows": 0, "message": "no tables found"})

    if output == "json":
        return jsonify({"rows": len(rows), "data": rows})
    else:
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
