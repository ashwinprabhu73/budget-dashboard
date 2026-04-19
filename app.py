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
# UI Setup
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare", "Upload File", "Add Entry"])

# -----------------------
# Upload (Multi-sheet)
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        all_sheets = pd.read_excel(file, sheet_name=None)

        df_list = []
        for _, sheet_data in all_sheets.items():
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

        st.success("✅ Data uploaded successfully!")

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
        st.success("Saved successfully!")

# -----------------------
# Dashboard
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.strftime("%B")

        # -----------------------
        # Year Selection
        # -----------------------
        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("📅 Select Year", years)

        year_df = df[df["year"] == selected_year]

        # -----------------------
        # Total Spend + Monthly Avg
        # -----------------------
        yearly_total = year_df["amount"].sum()
        months_count = year_df["month"].nunique()

        avg_monthly = yearly_total / months_count if months_count > 0 else 0

        st.markdown("### 💰 Total Spend")
        st.success(f"₹{yearly_total:,.0f}")

        st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

        # -----------------------
        # Month Selection
        # -----------------------
        months = year_df["month"].unique()
        selected_month = st.selectbox("📊 Select Month", months)

        filtered = year_df[year_df["month"] == selected_month]

        # -----------------------
        # Category Chart
        # -----------------------
        st.subheader(f"📊 Category Breakdown - {selected_month}")

        cat = filtered.groupby("category")["amount"].sum().reset_index()
        cat = cat.sort_values(by="amount", ascending=False)
        cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=400,
            yaxis=dict(visible=False),
            xaxis_title="",
            yaxis_title=""
        )

        st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # Recurring Section
        # -----------------------
        st.subheader("🔁 Recurring Breakdown")

        rec = filtered[filtered["recurring"].str.lower() == "recurring"]

        if not rec.empty:
            rec_cat = rec.groupby("category")["amount"].sum().reset_index()
            rec_cat["label"] = rec_cat["amount"].apply(lambda x: f"₹{x:,.0f}")

            fig2 = px.bar(rec_cat, x="category", y="amount", text="label")

            fig2.update_traces(textposition="outside")
            fig2.update_layout(
                height=400,
                yaxis=dict(visible=False)
            )

            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No recurring expenses")

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
