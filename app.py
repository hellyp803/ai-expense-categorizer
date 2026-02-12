import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# title
st.title("Universal CSV Expense Analyzer")

# taking api key
api_key = st.sidebar.text_input("enter api key", type="password")

# stop if api key not entered
if not api_key:
    st.warning("Please enter Gemini API key.")
    st.stop()

# configure gemini
genai.configure(api_key=api_key)

# loading model
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

# upload csv
data = st.file_uploader("Upload any CSV file", type=["csv"])

# check if file uploaded
if data is not None:

    # read csv
    df = pd.read_csv(data)

    # remove extra spaces from column names
    df.columns = df.columns.str.strip()

    st.subheader("Raw Data")
    st.dataframe(df)

    # find text and numeric columns automatically
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    # if no numeric column found stop
    if not numeric_cols:
        st.error("No numeric column found in this CSV")
        st.stop()

    # user selects which column is description
    transaction_col = st.selectbox("Select description column", text_cols)

    # user selects which column is amount
    amount_col = st.selectbox("Select amount column", numeric_cols)

    # cleaning selected columns
    df[transaction_col] = df[transaction_col].astype(str).str.lower().str.strip()
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")

    # remove empty rows
    df = df.dropna(subset=[transaction_col, amount_col])

    # run button
    if st.button("Run Analysis"):

        categories = []
        confidences = []

        # loop for each transaction
        for desc in df[transaction_col]:

            # prompt for gemini
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
                # get response
                response = model.generate_content(prompt)
                result = response.text.strip()

                parsed = json.loads(result)

                category = parsed.get("category", "Other")
                confidence = parsed.get("confidence", 0.5)

                # if model gives wrong category
                if category not in cat:
                    category = "Other"

            except:
                # if error happens
                category = "Other"
                confidence = 0.5

            categories.append(category)
            confidences.append(confidence)

        # add predicted columns
        df["Predicted_Category"] = categories
        df["Confidence"] = confidences

        st.subheader("Categorized Data")
        st.dataframe(df)

        # ---------------- anomaly detection ----------------

        anomalies = []

        mean = df[amount_col].mean()
        std = df[amount_col].std()
        threshold = mean + (2 * std)

        # high amount detection
        for index, row in df.iterrows():
            if row[amount_col] > threshold:
                anomalies.append({
                    "Description": row[transaction_col],
                    "Amount": row[amount_col],
                    "Issue": "High Amount"
                })

        # duplicate detection
        duplicates = df[df.duplicated(subset=[transaction_col, amount_col], keep=False)]

        for index, row in duplicates.iterrows():
            anomalies.append({
                "Description": row[transaction_col],
                "Amount": row[amount_col],
                "Issue": "Duplicate Entry"
            })

        anomaly_df = pd.DataFrame(anomalies)

        # ---------------- summary ----------------

        st.subheader("Summary Report")

        total = df[amount_col].sum()
        st.write(f"Total Amount: {round(total, 2)}")

        summary = df.groupby("Predicted_Category")[amount_col].sum()
        st.bar_chart(summary)

        percentage = (summary / total) * 100
        st.write("Category Percentage")
        st.dataframe(percentage.round(2))

        # show anomalies
        st.subheader("Anomalies")

        if len(anomaly_df) > 0:
            st.dataframe(anomaly_df)
        else:
            st.success("No anomalies detected")
