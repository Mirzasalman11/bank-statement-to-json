import requests
import json
import os

# Ensure the output directory exists
os.makedirs("table_txt", exist_ok=True)

url = "http://localhost:8000/api/process-statement"
files = {"file": open("test/statement1.pdf", "rb")}
response = requests.post(url, files=files)

# Get the JSON data from the response
response_data = response.json()

# Print the response for debugging
print("API Response:")
print(response_data)

# Save the JSON response to a file
with open("table_txt/api_response1.json", "w", encoding="utf-8") as f:
    json.dump(response_data, f, indent=4)

print(f"Response saved to table_txt/api_response.json")
