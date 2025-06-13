

### Use Bank Statement Processor API via cURL

#### Health Check Endpoint

Check if the server is running:

```bash
curl -X GET http://localhost:8000/api/health
```

**Response:**

```json
{
  "status": "ok",
  "message": "Bank Statement Processor API is running"
}
```

---

#### Upload a Bank Statement (PDF)

Send a PDF file for processing:

```bash
curl -X POST http://localhost:8000/api/process-statement \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/statement.pdf"
```

> Replace `/path/to/your/statement.pdf` with the full path to your actual PDF file.

**Example:**

```bash
curl -X POST http://localhost:8000/api/process-statement \
  -F "file=@bank-statement-may.pdf"
```

**Success Response:**

```json
{
  "transactions": [
    {
      "date": "2025-05-01",
      "description": "Amazon Purchase",
      "amount": -54.90,
      "balance": 945.10
    },
    ...
  ]
}
```

**Error Response (e.g. wrong file type):**

```json
{
  "detail": "Only PDF files are supported"
}
```

---

#### CORS Note

* This API currently accepts requests from **any origin** (`Access-Control-Allow-Origin: *`)
* No authentication is required at this stage — **use responsibly** if deploying publicly.

