import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -----------------------
# DB Setup
# -----------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    category TEXT,
    amount REAL,
    paid_by TEXT,
    paid_via TEXT,
    bank TEXT,
    status TEXT,
    notes TEXT,
    recurring TEXT
)
''')
conn.commit()

# -----------------------
# Functions
# -----------------------
def insert_data(row):
    c.execute("""
        INSERT INTO expenses 
        (date, description, category, amount, paid_by, paid_via, bank, status, notes, recurring)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(row))
    conn.commit()

def load_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Upload File"])

# -----------------------
# Upload
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload your budget file", type=["xlsx", "csv"])

    if file:
        df = pd.read_excel(file)

        # Normalize columns
        df = df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount",
            "Paid by": "paid_by",
            "Paid Via": "paid_via",
            "Bank": "bank",
            "Status": "status",
            "Notes": "notes",
            "Recurring Expense": "recurring"
        })

        df = df.fillna("")

        for _, row in df.iterrows():
            insert_data(row.values)

        st.success("Data uploaded successfully!")

# -----------------------
# Dashboard
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available")
    else:
        df["date"] = pd.to_datetime(df["date"])

        # KPIs
        total = df["amount"].sum()
        recurring = df[df["recurring"] == "Recurring"]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total:,.0f}")
        col2.metric("Recurring Spend", f"₹{recurring:,.0f}")

        # Monthly Trend
        df["month"] = df["date"].dt.to_period("M")
        monthly = df.groupby("month")["amount"].sum()

        st.subheader("📈 Monthly Spending Trend")
        st.line_chart(monthly)

        # Category
        st.subheader("📊 Category Breakdown")
        cat = df.groupby("category")["amount"].sum()
        st.bar_chart(cat)

        # Paid By
        st.subheader("👤 Spending by Person")
        person = df.groupby("paid_by")["amount"].sum()
        st.bar_chart(person)

        # Payment Method
        st.subheader("💳 Payment Method")
        pay = df.groupby("paid_via")["amount"].sum()
        st.bar_chart(pay)

        # Insights
        st.subheader("🧠 Insights")

        top_cat = cat.idxmax()
        st.write(f"👉 Highest spending category: **{top_cat}**")

        if recurring > total * 0.5:
            st.warning("⚠️ More than 50% expenses are recurring")
