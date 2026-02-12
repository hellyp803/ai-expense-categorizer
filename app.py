import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import pdfplumber

# title
st.title("Universal CSV & PDF Expense Analyzer")

# taking api key
api_key = st.sidebar.text_input("enter api key", type="password")

if not api_key:
    st.warning("Please enter Gemini API key.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# category list
cat = [
    "Travel",
    "Food & drinks",
    "Rent",
    "Shopping",
    "Health",
    "Investment",
    "Bills",
    "Other"
]

# upload csv or pdf
data = st.file_uploader("Upload CSV or PDF file", type=["csv", "pdf"])

if data is not None:

    # ---------------------------
    # IF CSV
    # ---------------------------
    if data.name.endswith(".csv"):
        df = pd.read_csv(data)

    # ---------------------------
    # IF PDF
    # ---------------------------
    elif data.name.endswith(".pdf"):

        tables = []

        with pdfplumber.open(data) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    tables.append(pd.DataFrame(table[1:], columns=table[0]))

        if tables:
            df = pd.concat(tables, ignore_index=True)
        else:
            st.error("No table found in PDF.")
            st.stop()

    # clean column names
    df.columns = df.columns.str.strip()

    st.subheader("Raw Data")
    st.dataframe(df)

    # find text and numeric columns
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    # convert possible numeric columns if PDF
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    if not numeric_cols:
        st.error("No numeric column found.")
        st.stop()

    transaction_col = st.selectbox("Select description column", text_cols)
    amount_col = st.selectbox("Select amount column", numeric_cols)

    df[transaction_col] = df[transaction_col].astype(str).str.lower().str.strip()
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")

    df = df.dropna(subset=[transaction_col, amount_col])

    if st.button("Run Analysis"):

        categories = []
        confidences = []

        for desc in df[transaction_col]:

            prompt = f"""
            Categorize this expense into one of these categories:
            {cat}

            Return ONLY valid JSON:
            {{
                "category": "<category>",
                "confidence": <number between 0 and 1>
            }}

            Transaction: "{desc}"
            """

            try:
                response = model.generate_content(prompt)
                parsed = json.loads(response.text.strip())

                category = parsed.get("category", "Other")
                confidence = parsed.get("confidence", 0.5)

                if category not in cat:
                    category = "Other"

            except:
                category = "Other"
                confidence = 0.5

            categories.append(category)
            confidences.append(confidence)

        df["Predicted_Category"] = categories
        df["Confidence"] = confidences

        st.subheader("Categorized Data")
        st.dataframe(df)

        # anomaly detection
        anomalies = []

        mean = df[amount_col].mean()
        std = df[amount_col].std()
        threshold = mean + (2 * std)

        for index, row in df.iterrows():
            if row[amount_col] > threshold:
                anomalies.append({
                    "Description": row[transaction_col],
                    "Amount": row[amount_col],
                    "Issue": "High Amount"
                })

        anomaly_df = pd.DataFrame(anomalies)

        st.subheader("Summary Report")

        total = df[amount_col].sum()
        st.write(f"Total Amount: {round(total, 2)}")

        summary = df.groupby("Predicted_Category")[amount_col].sum()
        st.bar_chart(summary)

        st.subheader("Anomalies")

        if len(anomaly_df) > 0:
            st.dataframe(anomaly_df)
        else:
            st.success("No anomalies detected")
