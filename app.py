import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

st.title("Expense categorizer") #title
api_key = st.sidebar.text_input("enter api key",type="password")

#stop if apikey is not provided
if not api_key:
    st.warning("Please enter Gemini API key.")
    st.stop()

genai.configure(api_key=api_key)

#loading gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

#defining categoties which i have
cat = [
    "Travel",
    "Food & drinks",
    "Rent",
    "Shopping",
    "Health",
    "Invetsment",
    "Bills"
]

data = st.file_uploader("Upload .csv file here",type=["csv"])
#uploading csv file

#checking fileis uploaded or not
if data is not None:
    df = pd.read_csv(data)

    req_col = ["Transaction", "Category", "Amount"]

    for col in req_col:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.stop()
        
    st.subheader("Original Data")
    st.dataframe(df)
#data processing 
    df["Transaction"] = df["Transaction"].astype(str).str.lower()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
#removing rows with missing val
    df = df.dropna(subset=["Transaction", "Amount"])


#running ai
if st.button("Run"):
        categories = []
        confidences = []

#loop for each transaction
        for desc in df["Transaction"]:

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
#response
            try:
                response = model.generate_content(prompt)
                result = response.text.strip()

                parsed = json.loads(result)

                category = parsed.get("category", "Other")
                confidence = parsed.get("confidence", 0.5)

                if category not in cat:
                    category = "Other"

            except:
                category = "Other"
                confidence = 0.5

            categories.append(category)
            confidences.append(confidence)
#prediction
        df["Predicted_Category"] = categories
        df["Confidence"] = confidences


#display categoris
st.subheader("Categorized Data")
st.dataframe(df)


#anomaly detection
anomalies = []

mean = df["Amount"].mean()
std = df["Amount"].std()
threshold = mean + (2 * std)

        # high amount detection
for index, row in df.iterrows():
            if row["Amount"] > threshold:
                anomalies.append({
                    "Transaction": row["Transaction"],
                    "Category": row["Category"],
                    "Amount": row["Amount"],
                    "Issue": "High Amount"
                })

        # duplicate detection
duplicates = df[df.duplicated(subset=["Transaction", "Category", "Amount"], keep=False)]

for index, row in duplicates.iterrows():
            anomalies.append({
                "Transaction": row["Transaction"],
                "Category": row["Category"],
                "Amount": row["Amount"],
                "Issue": "Duplicate Entry"
            })
#anomalies -> dataframe
anomaly_df = pd.DataFrame(anomalies)


st.subheader("Summary")

total_spending = df["Amount"].sum()
st.write(f"Total Spending: ₹ {round(total_spending, 2)}")

summary = df.groupby("Predicted_Category")["Amount"].sum()
st.bar_chart(summary)

perct = (summary / total_spending) * 100
st.write("Category Percentage Description")
st.dataframe(perct.round(2))

st.subheader("Anomalies")

if len(anomaly_df) > 0:
    st.dataframe(anomaly_df)
else:
    st.success("No anomalies")
