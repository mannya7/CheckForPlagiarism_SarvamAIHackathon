"""Streamlit interface for the assignment overlap checker."""

import os
import ssl
import tempfile
from pathlib import Path

import httpx
import streamlit as st
from sarvamai import SarvamAI

from pdf_plagiarism import _compare, _load_api_key, parse_pdf, read_docx


st.set_page_config(page_title="Assignment Overlap Checker", page_icon="📄")
st.title("Assignment Overlap Checker")
st.write("Compare one assignment with reference documents for exact shared phrases.")
st.info(
    "PDFs are sent to Sarvam for text extraction. Word files are processed by this app. "
    "AI authorship is not determined."
)

submission_upload = st.file_uploader(
    "Assignment to check", type=["pdf", "docx"], key="submission"
)
reference_uploads = st.file_uploader(
    "Reference documents (class work or a saved LLM answer)",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    key="references",
)
language = st.text_input("Language code for PDFs", value="en-IN")


def _get_api_key():
    try:
        key = st.secrets.get("SARVAM_API_KEY")
    except Exception:
        key = None
    if key:
        return key
    if os.environ.get("SARVAM_API_KEY"):
        return os.environ["SARVAM_API_KEY"]
    try:
        return _load_api_key()
    except SystemExit:
        return None


def _write_upload(upload, folder, label):
    name = Path(upload.name).name
    path = folder / f"{label}_{name}"
    path.write_bytes(upload.getvalue())
    return path


if st.button("Check for matching phrases", type="primary"):
    if submission_upload is None:
        st.error("Choose an assignment to check.")
    elif not reference_uploads:
        st.error("Choose at least one reference document.")
    else:
        uploads = [submission_upload, *reference_uploads]
        needs_sarvam = any(Path(upload.name).suffix.lower() == ".pdf" for upload in uploads)
        api_key = _get_api_key() if needs_sarvam else None
        if needs_sarvam and not api_key:
            st.error("Add SARVAM_API_KEY in Streamlit app Secrets to process PDFs.")
        else:
            try:
                with tempfile.TemporaryDirectory() as temporary_directory:
                    folder = Path(temporary_directory)
                    paths = [
                        _write_upload(upload, folder, f"file_{index}")
                        for index, upload in enumerate(uploads)
                    ]
                    if needs_sarvam:
                        with httpx.Client(
                            verify=ssl.create_default_context(), timeout=60
                        ) as http_client:
                            client = SarvamAI(
                                api_subscription_key=api_key,
                                httpx_client=http_client,
                            )
                            with st.spinner("Extracting text and comparing documents…"):
                                texts = [
                                    read_docx(path)
                                    if path.suffix.lower() == ".docx"
                                    else parse_pdf(path, client, http_client, language)
                                    for path in paths
                                ]
                    else:
                        with st.spinner("Reading and comparing documents…"):
                            texts = [read_docx(path) for path in paths]

                st.subheader("Results")
                for reference_upload, reference_text in zip(reference_uploads, texts[1:]):
                    percent, matched, total, examples = _compare(texts[0], reference_text)
                    st.metric(
                        label=reference_upload.name,
                        value=f"{percent:.1f}% phrase overlap",
                        delta=f"{matched} of {total} eight-word phrases matched",
                        delta_color="off",
                    )
                    if examples:
                        with st.expander("Show matching phrases"):
                            for phrase in examples:
                                st.write(f"- {phrase}")
                st.caption(
                    "Exact phrase overlap is a review aid, not a plagiarism verdict. "
                    "Common wording can match, and paraphrases may not."
                )
                st.caption("LLM authorship: not determined.")
            except Exception as error:
                st.error(
                    f"The comparison did not finish ({type(error).__name__}). "
                    "Check the files, API key, and app logs, then try again."
                )
