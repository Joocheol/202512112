# 202512112

## Generating a PDF from the saved page

### Option 1: Chromium (best visual fidelity)

1. Install dependencies and the headless Chromium binary:
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

2. Render the saved HTML to PDF (default paths are `gpt.html` → `gpt.pdf`):
   ```bash
   python generate_pdf.py
   ```
   The script copies `gpt.html` and the `gpt_files` directory into a temporary
   working area, strips CDN-hosted references, and then uses Chromium to print
   the page to PDF so the conversion matches the original layout.

   The resulting PDF is not checked into version control; run the command above
   whenever you need to regenerate it.

### Option 2: wkhtmltopdf (fallback renderer)

1. Install wkhtmltopdf:
   ```bash
   sudo apt-get update
   sudo apt-get install -y wkhtmltopdf
   ```

2. Render using wkhtmltopdf:
   ```bash
   python generate_pdf.py --engine wkhtmltopdf
   ```

### Custom paths
```bash
python generate_pdf.py path/to/page.html output.pdf
```
