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
    # Normalize column names (remove spaces)
df.columns = df.columns.str.strip()

# Try to detect important columns automatically
transaction_col = None
amount_col = None
category_col = None

for col in df.columns:
    if "transaction" in col.lower() or "description" in col.lower():
        transaction_col = col
    if "amount" in col.lower():
        amount_col = col
    if "category" in col.lower():
        category_col = col

if not transaction_col or not amount_col:
    st.error("Required columns (transaction/description and amount) not found.")
    st.write("Available columns:", df.columns)
    st.stop()



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
