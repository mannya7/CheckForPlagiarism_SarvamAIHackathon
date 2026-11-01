# Academic Assignment Overlap Checker

A small prototype that compares one assignment with reference assignments and reports exact shared phrases.

## What it does

1. Takes one submission and one or more reference files (`.pdf` or `.docx`).
2. Extracts the text. Word documents are read locally. PDFs are uploaded to Sarvam Document Intelligence for text extraction.
3. Finds exact matching eight-word phrases and prints the overlap percentage and up to five examples for each reference.

Run with `--both-directions` to score each document as the submission.

## Setup (Windows)

1. Install Python 3.9 or newer.
2. Open this folder in VS Code and open **Terminal → New Terminal**.
3. Install Sarvam's Python SDK:

   ```powershell
   py -m pip install --user sarvamai
   ```

4. Create your local key file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Open `.env` and replace the blank value with your Sarvam API key:

   ```text
   SARVAM_API_KEY=your_key_here
   ```

Keep `.env` private. It is excluded from Git. The key is needed for PDF files; `.docx` files are read locally.

## Run

Pass the submission first, then reference files:

```powershell
py pdf_plagiarism.py "submission.docx" "reference1.docx" "reference2.pdf" --both-directions
```

Replace the example filenames with your own file paths. PDF parsing supports up to 30 pages per file.

## Scope and limitations

- This prototype checks exact phrase overlap only against the reference files you provide. It does not search the web or detect paraphrasing, translations, citation issues, or code copying.
- An overlap score is a review aid, not a plagiarism verdict. Common wording may match, and paraphrases may not.
- It does not determine whether text was written by an LLM. Text-only AI detectors can misclassify work; their scores should not be treated as proof of misconduct ([study](https://link.springer.com/article/10.1007/s40979-023-00146-z), [evaluation](https://aclanthology.org/2025.findings-naacl.271/)).
- If you want to compare against a particular LLM answer, save that answer as a `.docx` or `.pdf` and pass it as a reference file.

## Files

- `pdf_plagiarism.py` — assignment comparison prototype.
- `sarvam_chat.py` — minimal Sarvam API chat smoke test.
- `.env.example` — blank key template; copy to `.env` and add your private key.
