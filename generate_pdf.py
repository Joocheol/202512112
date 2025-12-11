import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_HTML = "gpt.html"
DEFAULT_PDF = "gpt.pdf"
DEFAULT_ENGINE = "chromium"
CDN_PATTERN = re.compile(r"https://cdn\.oaistatic\.com[^'\"\s>]+", re.IGNORECASE)
FONT_FACE_PATTERN = re.compile(
    r"@font-face\s*\{[^}]*cdn\.oaistatic\.com[^}]*\}", re.IGNORECASE | re.DOTALL
)


def strip_cdn_assets(text: str) -> str:
    cleaned = re.sub(
        r"<script[^>]+https://cdn\.oaistatic\.com[^>]*></script>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"<link[^>]+https://cdn\.oaistatic\.com[^>]*>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = FONT_FACE_PATTERN.sub("", cleaned)
    cleaned = CDN_PATTERN.sub("", cleaned)
    return cleaned


def scrub_directory(temp_dir: Path) -> None:
    for css_file in (temp_dir / "gpt_files").rglob("*.css"):
        css_text = css_file.read_text(encoding="utf-8", errors="ignore")
        css_text = FONT_FACE_PATTERN.sub("", css_text)
        css_text = CDN_PATTERN.sub("", css_text)
        css_file.write_text(css_text, encoding="utf-8")


def generate_pdf(html_path: Path, output_path: Path, engine: str) -> None:
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    cleaned_html = strip_cdn_assets(html_text)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_html_path = temp_dir / html_path.name
        temp_html_path.write_text(cleaned_html, encoding="utf-8")

        assets_src = html_path.parent / "gpt_files"
        assets_dest = temp_dir / "gpt_files"
        if assets_src.exists():
            shutil.copytree(assets_src, assets_dest)
            scrub_directory(temp_dir)

        if engine == "wkhtmltopdf":
            run_wkhtmltopdf(temp_html_path, output_path)
        else:
            run_chromium(temp_html_path, output_path)


def run_wkhtmltopdf(temp_html_path: Path, output_path: Path) -> None:
    wkhtmltopdf = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf:
        raise RuntimeError("wkhtmltopdf is not installed or not found on PATH.")

    cmd = [
        wkhtmltopdf,
        "--enable-local-file-access",
        str(temp_html_path),
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def run_chromium(temp_html_path: Path, output_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(temp_html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a PDF from a saved HTML file using Chromium or wkhtmltopdf."
    )
    parser.add_argument(
        "html",
        nargs="?",
        default=DEFAULT_HTML,
        type=Path,
        help="Path to the HTML file (default: gpt.html)",
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=DEFAULT_PDF,
        type=Path,
        help="Path to the output PDF (default: gpt.pdf)",
    )
    parser.add_argument(
        "--engine",
        choices=("chromium", "wkhtmltopdf"),
        default=DEFAULT_ENGINE,
        help="Rendering engine to use (default: chromium)",
    )

    args = parser.parse_args()
    generate_pdf(args.html, args.pdf, args.engine)
