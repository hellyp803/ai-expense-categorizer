An AI-powered web application that automates expense categorization, detects anomalies, and generates summary reports using Gemini (Google LLM).
This tool helps finance teams reduce manual effort in categorizing transactions from CSV files and improves consistency and efficiency.

#project description
Expense tracking is a repetitive and error-prone process when done manually. This project provides an AI-assisted solution that:

- Ingests a CSV file of financial transactions
- Automatically categorizes each expense using a Large Language Model (Gemini)
- Flags suspicious or anomalous transactions
- Generates a summary report with visualizations
- The application is built using Streamlit for the frontend, Pandas for data processing, and Gemini for AI-powered classification.

#Tech Stack

- Frontend: Streamlit
- Backend: Python
- Data Processing: Pandas
- LLM: Google Gemini (gemini-1.5-flash)
- Deployment: Streamlit Cloud

#Features

1. CSV Upload
- Accepts `.csv` files
- Validates required columns:
  - `Transaction`
  - `Category`
  - `Amount`
- Handles missing or malformed values

2. AI-Based Categorization
- Uses Gemini LLM for intelligent classification
- Structured JSON output:
  ```json
  {
      "category": "Travel",
      "confidence": 0.92
  }
