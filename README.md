# Bank Statement Processor API

A FastAPI-based service that processes bank statement PDFs and extracts transaction data using OCR and AI-powered text analysis.

## Features

- **PDF Processing**: Extracts text from bank statement PDFs
- **AI-Powered Analysis**: Uses OpenAI's API to intelligently parse and structure transaction data
- **RESTful API**: Simple HTTP endpoints for processing statements
- **CORS Support**: Ready for web application integration
- **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

- Python 3.9+
- OpenAI API key
- Required Python packages (see [Installation](#installation))

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bank_statement_api
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix or MacOS
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. Start the FastAPI server:
   ```bash
   uvicorn app:app --reload
   ```

2. The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /api/process-statement`
  - Accepts a PDF file (bank statement)
  - Returns structured JSON with transaction data
  
  Example request using cURL:
  ```bash
  curl -X 'POST' \
    'http://localhost:8000/api/process-statement' \
    -H 'accept: application/json' \
    -H 'Content-Type: multipart/form-data' \
    -F 'file=@path/to/your/statement.pdf;type=application/pdf'
  ```

- `GET /health`
  - Health check endpoint
  - Returns `{"status": "ok"}` when service is running

## Project Structure

- `app.py` - Main FastAPI application and endpoints
- `process_ocr_output.py` - Core logic for PDF processing and text extraction
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not version controlled)
- `uploads/` - Directory for temporarily storing uploaded files
- `table_txt/` - Directory for storing intermediate text extraction results
- `test/` - Test files and test cases

## Logging

Logs are written to `pdf_table_extractor.log` in the project root directory.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [OpenAI](https://openai.com/) - For the AI/ML capabilities
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction library
