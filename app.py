import streamlit as st
import pandas as pd
import sqlite3

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
    """, row)
    conn.commit()

def load_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI Setup
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Upload File"])

# -----------------------
# Upload Section
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload your budget file", type=["xlsx", "csv"])

    if file:
        df = pd.read_excel(file)

        # Rename columns based on your sheet
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

        # Insert safely
        for _, row in df.iterrows():
            insert_data([
                str(row.get("date", "")),
                str(row.get("description", "")),
                str(row.get("category", "")),
                float(row.get("amount", 0) or 0),
                str(row.get("paid_by", "")),
                str(row.get("paid_via", "")),
                str(row.get("bank", "")),
                str(row.get("status", "")),
                str(row.get("notes", "")),
                str(row.get("recurring", ""))
            ])

        st.success("✅ Data uploaded successfully!")

# -----------------------
# Dashboard Section
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available. Please upload file.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

        # KPIs
        total_spend = df["amount"].sum()
        recurring_spend = df[df["recurring"].str.lower() == "recurring"]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total_spend:,.0f}")
        col2.metric("Recurring Spend", f"₹{recurring_spend:,.0f}")

        # Monthly Trend
        df["month"] = df["date"].dt.to_period("M")
        monthly = df.groupby("month")["amount"].sum()

        st.subheader("📈 Monthly Spending Trend")
        st.line_chart(monthly)

        # Category Breakdown
        st.subheader("📊 Category Breakdown")
        category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        st.bar_chart(category)

        # Spending by Person
        st.subheader("👤 Spending by Person")
        person = df.groupby("paid_by")["amount"].sum()
        st.bar_chart(person)

        # Payment Method
        st.subheader("💳 Payment Method")
        payment = df.groupby("paid_via")["amount"].sum()
        st.bar_chart(payment)

        # Top Categories Table
        st.subheader("🔥 Top Categories")
        st.dataframe(category.head(5))

        # Insights
        st.subheader("🧠 Insights")

        if not category.empty:
            st.write(f"👉 Highest spending category: **{category.idxmax()}**")

        if recurring_spend > total_spend * 0.5:
            st.warning("⚠️ More than 50% of your expenses are recurring!")
