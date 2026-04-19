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

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare", "Upload File", "Add Entry"])

# -----------------------
# Upload
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
# Add Entry
# -----------------------
elif menu == "Add Entry":
    st.subheader("➕ Add Expense")

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

    if st.button("Save"):
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
        st.success("✅ Saved successfully!")

# -----------------------
# Dashboard (Single Month)
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%B")

        st.subheader("📅 Select Month")

        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("Year", years)

        months = df[df["year"] == selected_year]["month"].unique()
        selected_month = st.selectbox("Month", months)

        filtered_df = df[
            (df["year"] == selected_year) &
            (df["month"] == selected_month)
        ]

        # KPIs
        total = filtered_df["amount"].sum()
        recurring = filtered_df[
            filtered_df["recurring"].str.lower() == "recurring"
        ]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total:,.0f}")
        col2.metric("Recurring", f"₹{recurring:,.0f}")

        # Category chart
        st.subheader("📊 Category Breakdown")

        cat = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        cat.index = [f"{get_icon(c)} {c}" for c in cat.index]

        st.bar_chart(cat)

        # Recurring
        st.subheader("🔁 Recurring Breakdown")
        rec = filtered_df[filtered_df["recurring"].str.lower() == "recurring"]

        if not rec.empty:
            st.bar_chart(rec.groupby("category")["amount"].sum())
        else:
            st.info("No recurring expenses")

# -----------------------
# Compare Section (NEW)
# -----------------------
elif menu == "Compare":
    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%B")

        st.subheader("⚖️ Compare Months")

        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("Year", years)

        months = df[df["year"] == selected_year]["month"].unique()

        col1, col2 = st.columns(2)
        m1 = col1.selectbox("Month 1", months)
        m2 = col2.selectbox("Month 2", months)

        df1 = df[(df["year"] == selected_year) & (df["month"] == m1)]
        df2 = df[(df["year"] == selected_year) & (df["month"] == m2)]

        cat1 = df1.groupby("category")["amount"].sum()
        cat2 = df2.groupby("category")["amount"].sum()

        compare = pd.DataFrame({
            m1: cat1,
            m2: cat2
        }).fillna(0)

        st.bar_chart(compare)

        # Insight
        st.subheader("🧠 Insights")

        total1 = df1["amount"].sum()
        total2 = df2["amount"].sum()

        diff = total1 - total2

        if diff > 0:
            st.warning(f"⚠️ {m1} is ₹{diff:,.0f} higher than {m2}")
        else:
            st.success(f"✅ {m1} is ₹{abs(diff):,.0f} lower than {m2}")
