# NewsScope AI

A Flask + Bootstrap news article analysis project.

## Features
- TXT, PDF and PNG upload
- PDF text extraction
- PNG OCR with Tesseract
- Upload success notifications
- Article preview before analysis
- Sentiment analysis
- Category classification
- Main-point extraction
- Confidence score
- SQLite history
- Open/delete history items
- Search by keyword, category and sentiment
- Responsive Bootstrap 5 UI
- Detailed About page

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Open http://127.0.0.1:5000

For PNG OCR, install Tesseract OCR separately on Windows and make sure it is available on PATH.
