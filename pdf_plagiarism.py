"""Compare assignment PDFs or Word documents using exact phrase overlap."""

import argparse
import html.parser
import os
import re
import ssl
import time
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path, PurePosixPath

import httpx
from sarvamai import SarvamAI


TERMINAL_STATES = {"completed", "partially_completed", "failed", "rejected"}
SHINGLE_WORDS = 8


class _HtmlText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _load_api_key():
    env_file = Path(__file__).with_name(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() == "SARVAM_API_KEY":
                os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise SystemExit("Add your Sarvam API key to .env before running this script.")
    return key


def _extract_text(archive_bytes):
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        content_files = [
            name for name in archive.namelist()
            if PurePosixPath(name).suffix.lower() in {".html", ".md", ".txt"}
            and "/metadata/" not in f"/{name.lower()}"
        ]
        if not content_files:
            raise RuntimeError("Sarvam returned no readable text file for this PDF.")

        pieces = []
        for name in content_files:
            content = archive.read(name).decode("utf-8", errors="replace")
            if name.lower().endswith(".html"):
                parser = _HtmlText()
                parser.feed(content)
                content = " ".join(parser.parts)
            pieces.append(content)
        return "\n".join(pieces).strip()


def parse_pdf(path, client, http_client, language):
    print(f"Reading {path.name} with Sarvam Document Intelligence…")
    with path.open("rb") as pdf:
        job = client.doc_ai.parse(
            file=[(path.name, pdf, "application/pdf")],
            language=language,
        )

    deadline = time.monotonic() + 600
    while True:
        status = client.doc_ai.get_status(job_id=job.job_id)
        state = status.status.lower()
        if state in TERMINAL_STATES:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Sarvam is still processing {path.name}; try again later.")
        time.sleep(5)

    if state not in {"completed", "partially_completed"}:
        raise RuntimeError(f"Sarvam could not parse {path.name} (status: {state}).")

    download = client.doc_ai.get_download_url(job_id=job.job_id)
    response = http_client.get(download.url)
    response.raise_for_status()
    return _extract_text(response.content)


def read_docx(path):
    """Extract visible paragraph text locally from a Word document."""
    with zipfile.ZipFile(path) as docx:
        document_xml = ET.fromstring(docx.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in document_xml.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def read_document(path, client, http_client, language):
    if path.suffix.lower() == ".docx":
        print(f"Reading {path.name} locally…")
        return read_docx(path)
    return parse_pdf(path, client, http_client, language)


def _word_shingles(text):
    words = re.findall(r"[\w']+", text.casefold())
    shingles = [
        (" ".join(words[i:i + SHINGLE_WORDS]), i)
        for i in range(max(0, len(words) - SHINGLE_WORDS + 1))
    ]
    return words, shingles


def _compare(target_text, reference_text):
    target_words, target_shingles = _word_shingles(target_text)
    _, reference_shingles = _word_shingles(reference_text)
    reference_set = {phrase for phrase, _ in reference_shingles}
    matches = [(phrase, index) for phrase, index in target_shingles if phrase in reference_set]
    percent = 100 * len(matches) / len(target_shingles) if target_shingles else 0

    examples = []
    seen = set()
    for phrase, index in matches:
        if phrase not in seen:
            seen.add(phrase)
            example = " ".join(target_words[index:index + SHINGLE_WORDS])
            examples.append(example if len(example) <= 160 else example[:157] + "...")
        if len(examples) == 5:
            break
    return percent, len(matches), len(target_shingles), examples


def main():
    parser = argparse.ArgumentParser(
        description="Compare a submission PDF or DOCX with reference documents for exact phrase overlap."
    )
    parser.add_argument("submission", type=Path, help="PDF or DOCX to check")
    parser.add_argument("references", nargs="+", type=Path, help="PDFs or DOCX files to compare against")
    parser.add_argument("--language", default="en-IN", help="Document language code (default: en-IN)")
    parser.add_argument("--both-directions", action="store_true", help="Also compare each reference against the submission")
    args = parser.parse_args()

    paths = [args.submission, *args.references]
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".docx"}:
            raise SystemExit(f"Not a supported PDF or DOCX file: {path}")

    pdf_paths = [path for path in paths if path.suffix.lower() == ".pdf"]
    if pdf_paths:
        api_key = _load_api_key()
        with httpx.Client(verify=ssl.create_default_context(), timeout=60) as http_client:
            client = SarvamAI(api_subscription_key=api_key, httpx_client=http_client)
            parsed = {
                path: read_document(path, client, http_client, args.language)
                for path in paths
            }
    else:
        parsed = {path: read_docx(path) for path in paths}

    print(f"\nExact {SHINGLE_WORDS}-word phrase matches for {args.submission.name}:")
    for reference in args.references:
        percent, matched, total, examples = _compare(parsed[args.submission], parsed[reference])
        print(f"\n{reference.name}: {percent:.1f}% ({matched}/{total} phrases)")
        for phrase in examples:
            print(f"  - {phrase}")

        if args.both_directions:
            reverse_percent, reverse_matched, reverse_total, reverse_examples = _compare(
                parsed[reference], parsed[args.submission]
            )
            print(f"\n{reference.name} compared against {args.submission.name}: "
                  f"{reverse_percent:.1f}% ({reverse_matched}/{reverse_total} phrases)")
            for phrase in reverse_examples:
                print(f"  - {phrase}")

    print("\nThis is an exact-phrase overlap signal, not a plagiarism verdict.")
    print("Scope: supplied PDFs/DOCX only; this run does not search the web, detect paraphrases, assess citations, or compare code.")
    print("LLM authorship: not determined by this checker; text overlap cannot show who or what wrote it.")


if __name__ == "__main__":
    main()
