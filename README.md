# 202512112

## Generating a PDF from the saved page

1. Install the required system dependency (for rendering the HTML with local assets):
   ```bash
   sudo apt-get update
   sudo apt-get install -y wkhtmltopdf
   ```

2. Render the saved HTML to PDF (default paths are `gpt.html` → `gpt.pdf`):
   ```bash
   python generate_pdf.py
   ```
   The script copies `gpt.html` and the `gpt_files` directory into a temporary
   working area, strips CDN-hosted references, and then runs `wkhtmltopdf` so
   the conversion succeeds without external network access.

   The resulting PDF is not checked into version control; run the command above
   whenever you need to regenerate it.

You can also specify custom paths:
```bash
python generate_pdf.py path/to/page.html output.pdf
```
