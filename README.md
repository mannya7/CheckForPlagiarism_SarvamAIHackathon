# Academic Assignment Overlap Checker

A small Streamlit app that compares an assignment with reference documents and reports exact shared phrases.

## What it does

1. Takes one submission and one or more reference files (`.pdf` or `.docx`).
2. Extracts the text. DOCX files are processed by the app; PDFs are sent to Sarvam Document Intelligence for text extraction.
3. Finds exact matching eight-word phrases and reports the overlap percentage and example matches for each reference.

## Run locally (Windows)

1. Install Python 3.9 or newer.
2. Open this folder in VS Code and open **Terminal → New Terminal**.
3. Install the dependencies:

   ```powershell
   py -m pip install --user -r requirements.txt
   ```

4. Create your local key file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Open `.env` and add your Sarvam API key:

   ```text
   SARVAM_API_KEY=your_key_here
   ```

6. Start the app:

   ```powershell
   py -m streamlit run app.py
   ```

Keep `.env` private. It is excluded from Git. The key is needed only when PDFs are submitted; DOCX files do not call Sarvam.

## Deploy and share on Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, `pdf_plagiarism.py`, `.gitignore`, `README.md`, and `.env.example` to your GitHub repository. Do not upload `.env` or assignment documents.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and create an app from your repository. Use `app.py` as the app file.
3. In **Advanced settings → Secrets**, enter:

   ```toml
   SARVAM_API_KEY = "your_key_here"
   ```

   Do not put the key in GitHub. Streamlit Community Cloud stores app secrets separately from the repository.

The repository is private, so deploy the app privately first. You can invite specific viewers in Streamlit. A public app would let anyone use the app with your Sarvam key and credits. Community Cloud needs permission to access your private GitHub repository before it can deploy.

## Data handling

- Uploaded DOCX files are processed by the Streamlit app server.
- Uploaded PDFs are sent from the app server to Sarvam for text extraction. PDF parsing supports up to 30 pages per file.
- The app does not save uploaded files after the current check finishes.

## Scope and limitations

- This prototype checks exact phrase overlap against the reference files you provide. It does not search the web or detect paraphrasing, translations, citation issues, or code copying.
- An overlap score is a review aid, not a plagiarism verdict. Common wording may match, and paraphrases may not.
- It does not determine whether text was written by an LLM. Text-only AI detectors can misclassify work; their scores should not be treated as proof of misconduct ([study](https://link.springer.com/article/10.1007/s40979-023-00146-z), [evaluation](https://aclanthology.org/2025.findings-naacl.271/)).
- To compare against a specific LLM answer, save that answer as a `.docx` or `.pdf` and upload it as a reference.

## Files

- `app.py` — Streamlit upload and results interface.
- `pdf_plagiarism.py` — text extraction and phrase comparison logic.
- `requirements.txt` — pinned Python packages.
- `sarvam_chat.py` — minimal Sarvam API chat smoke test.
- `.env.example` — blank local key template.
