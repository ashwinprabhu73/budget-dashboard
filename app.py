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
# Category Icons
# -----------------------
CATEGORY_ICONS = {
    "Food": "🍔",
    "Rent": "🏠",
    "Travel": "✈️",
    "Shopping": "🛍️",
    "Bills": "💡",
    "Entertainment": "🎬"
}

def get_icon(category):
    return CATEGORY_ICONS.get(category, "💰")

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

menu = st.sidebar.radio("Menu", ["Dashboard", "Upload File", "Add Entry"])

# -----------------------
# Upload Section
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload your budget file", type=["xlsx", "csv"])

    if file:
        df = pd.read_excel(file)

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
# Add Entry (NEW)
# -----------------------
elif menu == "Add Entry":
    st.subheader("➕ Add Expense / Income")

    date = st.date_input("Date", datetime.today())
    description = st.text_input("Description")
    category = st.text_input("Category")
    amount = st.number_input("Amount")
    paid_by = st.text_input("Paid By")
    paid_via = st.selectbox("Paid Via", ["UPI", "Card", "Cash", "Bank"])
    bank = st.text_input("Bank")
    status = st.selectbox("Status", ["Paid", "Pending"])
    notes = st.text_input("Notes")
    recurring = st.selectbox("Recurring", ["", "Recurring"])

    if st.button("Save Entry"):
        insert_data([
            str(date),
            description,
            category,
            amount,
            paid_by,
            paid_via,
            bank,
            status,
            notes,
            recurring
        ])
        st.success("✅ Entry added successfully!")

# -----------------------
# Dashboard Section
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

        # KPIs
        total_spend = df["amount"].sum()
        recurring_df = df[df["recurring"].str.lower() == "recurring"]
        recurring_spend = recurring_df["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total_spend:,.0f}")
        col2.metric("Recurring Spend", f"₹{recurring_spend:,.0f}")

        # Monthly Trend
        df["month"] = df["date"].dt.to_period("M")
        monthly = df.groupby("month")["amount"].sum()

        st.subheader("📈 Monthly Spending Trend")
        st.line_chart(monthly)

        # Category Breakdown with Icons
        st.subheader("📊 Category Breakdown")
        category = df.groupby("category")["amount"].sum().sort_values(ascending=False)

        cat_display = category.copy()
        cat_display.index = [f"{get_icon(cat)} {cat}" for cat in cat_display.index]

        st.bar_chart(cat_display)

        # Recurring Section (NEW)
        st.subheader("🔁 Recurring Expenses Analysis")

        if not recurring_df.empty:
            recurring_month = recurring_df.groupby("month")["amount"].sum()
            st.line_chart(recurring_month)

            recurring_cat = recurring_df.groupby("category")["amount"].sum()
            st.bar_chart(recurring_cat)
        else:
            st.info("No recurring expenses found.")

        # Paid By
        st.subheader("👤 Spending by Person")
        person = df.groupby("paid_by")["amount"].sum()
        st.bar_chart(person)

        # Insights
        st.subheader("🧠 Insights")

        if not category.empty:
            st.write(f"👉 Highest spending category: **{category.idxmax()}**")

        if recurring_spend > total_spend * 0.5:
            st.warning("⚠️ High recurring expenses detected!")
