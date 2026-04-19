import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
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
    """, row)
    conn.commit()

def load_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare", "Upload File", "Add Entry"])

# -----------------------
# Upload (Multi-sheet support)
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        all_sheets = pd.read_excel(file, sheet_name=None)

        df_list = []

        for sheet_name, sheet_data in all_sheets.items():
            sheet_data["Sheet"] = sheet_name
            df_list.append(sheet_data)

        df = pd.concat(df_list, ignore_index=True)

        df = df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount"
        })

        df = df.fillna("")

        for _, row in df.iterrows():
            insert_data([
                str(row.get("date", "")),
                str(row.get("description", "")),
                str(row.get("category", "")),
                float(row.get("amount", 0) or 0),
                "", "", "", "", "", ""
            ])

        st.success("✅ Multi-sheet data uploaded!")

# -----------------------
# Add Entry
# -----------------------
elif menu == "Add Entry":
    st.subheader("➕ Add Expense")

    date = st.date_input("Date", datetime.today())
    category = st.text_input("Category")
    amount = st.number_input("Amount")

    if st.button("Save"):
        insert_data([
            str(date),
            "",
            category,
            amount,
            "", "", "", "", "", ""
        ])
        st.success("Saved!")

# -----------------------
# Dashboard
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%B")

        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("Year", years)

        months = df[df["year"] == selected_year]["month"].unique()
        selected_month = st.selectbox("Month", months)

        filtered = df[
            (df["year"] == selected_year) &
            (df["month"] == selected_month)
        ]

        total = filtered["amount"].sum()
        st.metric("Total Spend", f"₹{total:,.0f}")

        cat = filtered.groupby("category")["amount"].sum().reset_index()
        cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=400,
            yaxis=dict(visible=False)
        )

        st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Compare
# -----------------------
elif menu == "Compare":
    df = load_data()

    if df.empty:
        st.warning("No data")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%B")

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
        }).fillna(0).reset_index()

        fig = px.bar(compare, x="category", y=[m1, m2], barmode="group")

        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)
