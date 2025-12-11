import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DEFAULT_HTML = "gpt.html"
DEFAULT_PDF = "gpt.pdf"
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


def generate_pdf(html_path: Path, output_path: Path) -> None:
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    wkhtmltopdf = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf:
        raise RuntimeError("wkhtmltopdf is not installed or not found on PATH.")

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

        cmd = [
            wkhtmltopdf,
            "--enable-local-file-access",
            str(temp_html_path),
            str(output_path),
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a PDF from a saved HTML file using wkhtmltopdf."
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

    args = parser.parse_args()
    generate_pdf(args.html, args.pdf)
