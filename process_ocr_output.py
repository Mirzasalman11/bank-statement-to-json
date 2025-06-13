import os
import pdfplumber
import pandas as pd
import logging
import re
from datetime import datetime
from openai import OpenAI
import json
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_table_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_output_directories():
    os.makedirs('table_txt', exist_ok=True)

def parse_text_line(line):
    # Customize this regex based on your statement layout!
    # This example splits on 2+ spaces (for most bank statements)
    return re.split(r'\s{2,}', line.strip())

def process_pdf(pdf):
    logger.info(f"Processing PDF")
    found_tables = False
    
    # Initialize empty DataFrames to store all data
    all_tables_data = []
    all_text_data = []
    
    try:
        # Process all pages first and collect data
        for page_num, page in enumerate(pdf.pages, 1):
            logger.info(f"Extracting tables from page {page_num}/{len(pdf.pages)}")
            tables = page.extract_tables()
            
            if tables and tables[0] and len(tables[0]) > 1:
                found_tables = True
                for table_idx, table in enumerate(tables, 1):
                    df = pd.DataFrame(table)
                    # Add page number and table index as columns
                    all_tables_data.append(df)
                    logger.info(f"Processed table {table_idx} from page {page_num}")
            else:
                logger.info(f"No tables found on page {page_num}, extracting text as fallback...")
                # Text extraction for non-tabular layout
                text = page.extract_text()
                if text:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    parsed_rows = [parse_text_line(line) for line in lines]
                    df = pd.DataFrame(parsed_rows)
                    all_text_data.append(df)
                    logger.info(f"Processed text from page {page_num}")
        
        # Return the processed data
        result = {}
        
        # Combine all tables data if any exists
        if all_tables_data:
            result['tables'] = pd.concat(all_tables_data, ignore_index=True)
            logger.info("Tables data processed successfully")
        
        # Combine all text data if any exists
        if all_text_data:
            result['text'] = pd.concat(all_text_data, ignore_index=True)
            logger.info("Text data processed successfully")
        
        logger.info("PDF processing complete.")
        return result
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise

def split_into_chunks(text_data, max_chars=8000):
    """
    Split the statement text into manageable chunks based on character count.
    Each chunk will contain at most max_chars characters.
    """
    # If text is short enough, return as a single chunk
    if len(text_data) <= max_chars:
        return [text_data]
    
    # Split into chunks with some overlap to avoid missing context
    overlap = 500  # Character overlap between chunks
    chunks = []
    
    for i in range(0, len(text_data), max_chars - overlap):
        chunk = text_data[i:min(i + max_chars, len(text_data))]
        chunks.append(chunk)
    
    logger.info(f"Split data into {len(chunks)} chunks with {overlap} character overlap")
    return chunks

def extract_account_info(raw_statement: str) -> dict:
    """
    Uses OpenAI API to extract just the account information from the bank statement.
    """
    system_prompt = (
        "You are a finance expert that extracts structured data from raw bank statements. "
        "Extract ONLY the account information from the statement, not the transactions. "
        "IMPORTANT: Pay special attention to finding the account holder name, account number, and statement period. "
        "Look carefully through the entire text for these details, as they may be formatted in various ways."
    )

    user_prompt = f"""
Extract ONLY the following account information from this bank statement into JSON:

{{
  "account_holder": "",  // IMPORTANT: Look for names in ALL CAPS or special formatting
  "account_number": "",  // Look for account numbers, IBAN, or any numerical identifiers
  "statement_period": {{
    "start": "YYYY-MM-DD",  // Convert any date format to ISO
    "end": "YYYY-MM-DD"    // Convert any date format to ISO
  }},
  "opening_balance": 0.0,  // Numeric value only
  "closing_balance": 0.0,  // Numeric value only
  "currency": "",         // USD, EUR, GBP, PKR, etc.
  "statement_format": "wise/nayapay/bank_of_america/traditional/unknown"  // Identify the bank if possible
}}

IMPORTANT: Examine the entire text carefully for account holder name and account number.
They might appear in different formats or locations.

STATEMENT TEXT:
{raw_statement[:3000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        logger.info("Successfully extracted account information")
        
        # Try to parse response as JSON
        return json.loads(content)

    except json.JSONDecodeError:
        logger.error("GPT response for account info is not valid JSON")
        return {
            "account_holder": "",
            "account_number": "",
            "statement_period": {"start": "", "end": ""},
            "opening_balance": 0.0,
            "closing_balance": 0.0,
            "currency": "",
            "statement_format": "unknown"
        }
    except Exception as e:
        logger.error(f"Error extracting account info: {e}")
        return {
            "account_holder": "",
            "account_number": "",
            "statement_period": {"start": "", "end": ""},
            "opening_balance": 0.0,
            "closing_balance": 0.0,
            "currency": "",
            "statement_format": "unknown"
        }

def extract_transactions_from_chunk(chunk: str) -> list:
    """
    Uses OpenAI API to extract transactions from a chunk of the bank statement.
    """
    system_prompt = (
        "You are a finance expert that extracts structured data from raw bank statements. "
        "Extract ONLY the transactions from the statement chunk. "
        "IMPORTANT: Make sure to capture ALL transaction types, including currency conversions. "
        "Each line that contains a date, amount, and description should be considered a transaction."
    )

    user_prompt = f"""
Extract ONLY the transactions from this bank statement chunk into JSON array:

[
  {{
    "date": "YYYY-MM-DD",  // Convert any date format to ISO
    "description": "cleaned description",
    "type": "debit/credit",  // debit for negative amounts, credit for positive
    "amount": 0.0,  // Absolute value
    "amount_with_sign": 0.0,  // Negative for debits, positive for credits
    "running_balance": 0.0,  // Balance after this transaction
    "reference": "if available"  // Any reference number or additional info
  }}
]

IMPORTANT INSTRUCTIONS:
1. Include ALL transactions, especially currency conversions (e.g., 'Converted USD to PKR').
2. For currency conversions, the description should be 'Converted USD to PKR' or similar.
3. If the transaction has a negative amount or words like 'sent', 'payment', 'withdrawal', it's a debit (type: "debit").
4. If the transaction has a positive amount or words like 'received', 'deposit', it's a credit (type: "credit").

STATEMENT CHUNK:
{chunk}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        
        # Try to parse response as JSON
        transactions = json.loads(content)
        return transactions if isinstance(transactions, list) else []

    except json.JSONDecodeError:
        logger.error("GPT response for transactions is not valid JSON")
        return []
    except Exception as e:
        logger.error(f"Error extracting transactions: {e}")
        return []

def parse_bank_statement_to_json(raw_statement: str) -> dict:
    """
    Uses OpenAI API to convert a raw bank statement string into structured JSON format.
    Splits the statement into chunks to handle large statements efficiently.
    """
    # First, get account information from the beginning of the statement
    account_info = extract_account_info(raw_statement)
    
    # Split the statement into manageable chunks
    chunks = split_into_chunks(raw_statement, max_chars=8000)
    
    # Process each chunk and collect transactions
    all_transactions = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}")
        chunk_transactions = extract_transactions_from_chunk(chunk)
        all_transactions.extend(chunk_transactions)
    
    # Remove duplicate transactions
    unique_transactions = []
    seen_transactions = set()
    
    for transaction in all_transactions:
        # Create a unique identifier for each transaction
        # Using date, description, and amount as the key
        transaction_key = (transaction.get('date', ''), 
                          transaction.get('description', ''), 
                          transaction.get('amount', 0))
        
        if transaction_key not in seen_transactions:
            seen_transactions.add(transaction_key)
            unique_transactions.append(transaction)
    
    # Combine account info with all transactions
    result = account_info
    result['transactions'] = unique_transactions
    
    logger.info(f"Total unique transactions extracted: {len(unique_transactions)}")
    return result



def process_pdf_to_json(file_obj):
    # Open the PDF file using pdfplumber
    try:
        # If file_obj is a path string
        if isinstance(file_obj, str):
            pdf = pdfplumber.open(file_obj)
        # If file_obj is a file-like object (from FastAPI)
        else:
            pdf = pdfplumber.open(file_obj)
            
        # Call process_pdf function with the opened PDF
        extracted_text = process_pdf(pdf)
        
        # Close the PDF after processing
        pdf.close()
        
        try:
            extracted_text = extracted_text['tables']
        except:
            extracted_text = extracted_text['text']
            
        # Convert DataFrame to string if it's a DataFrame
        extracted_text_string = extracted_text.to_string(index=False) if isinstance(extracted_text, pd.DataFrame) else extracted_text
        
        # Process the extracted text using the chunking approach
        structured_data = parse_bank_statement_to_json(extracted_text_string)
        return structured_data
    except Exception as e:
        logger.error(f"Error in process_pdf_to_json: {str(e)}")
        return {"error": f"Failed to process PDF: {str(e)}"}









# pdf_path = r"test\statement3.pdf"  # Update path if needed

# # Open the PDF file first
# logger.info(f"Opening PDF: {pdf_path}")
# pdf = pdfplumber.open(pdf_path)

# structured_data = process_pdf_to_json(pdf)


# # Close the PDF after processing
# pdf.close()

# # Save to a file
# with open("table_txt/statement3.json", "w", encoding="utf-8") as f:
#     json.dump(structured_data, f, indent=4)



















