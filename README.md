# AI Document Processing Backend

FastAPI backend for email-only login, document upload, S3 storage, text extraction, Bedrock Nova Micro summarization, MySQL history, and downloads.

## Main Flow

1. User submits email and receives a bearer token.
2. User uploads up to 3 files.
3. Backend validates file type and size.
4. Original file is uploaded to S3.
5. Backend extracts text from PDF, TXT, PNG, JPG, or JPEG.
6. Extracted text is sent to Amazon Bedrock Nova Micro.
7. Summary and metadata are stored in MySQL.
8. User views only their own history.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

For image OCR in Ubuntu/WSL, install Tesseract once:

```bash
sudo apt update
sudo apt install tesseract-ocr -y
```

## Docker MySQL

```bash
docker compose up -d mysql
```

## API Docs

After starting the app, open:

```text
http://localhost:8000/docs
```
