import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# -----------------------
# Extract Sheet ID
# -----------------------
def extract_sheet_id(input_text):
    if "docs.google.com" in input_text:
        return input_text.split("/d/")[1].split("/")[0]
    return input_text

# -----------------------
# Load Google Sheet
# -----------------------
def load_google_sheet(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame()

# -----------------------
# Local DB (fallback)
# -----------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    category TEXT,
    amount REAL
)
''')
conn.commit()

def insert_data(row):
    c.execute("""
        INSERT INTO expenses (date, description, category, amount)
        VALUES (?, ?, ?, ?)
    """, row)
    conn.commit()

def load_local_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare", "Add Entry"])

# -----------------------
# Add Entry
# -----------------------
if menu == "Add Entry":
    st.subheader("➕ Add Expense")

    date = st.date_input("Date", datetime.today())
    category = st.text_input("Category")
    amount = st.number_input("Amount")

    if st.button("Save"):
        insert_data([str(date), "", category, amount])
        st.success("Saved locally!")

# -----------------------
# Dashboard
# -----------------------
elif menu == "Dashboard":

    st.subheader("🔗 Connect Google Sheet")

    sheet_input = st.text_input("Paste Google Sheet URL or ID")

    if sheet_input:
        sheet_id = extract_sheet_id(sheet_input)
        st.success(f"Connected to Sheet ID: {sheet_id}")

        if st.button("🔄 Refresh Data"):
            st.rerun()

        # Load data
        g_df = load_google_sheet(sheet_id)

        g_df = g_df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount"
        })

        g_df = g_df.fillna("")

        local_df = load_local_data()

        df = pd.concat([g_df, local_df], ignore_index=True)

        if df.empty:
            st.warning("No data available")
        else:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.strftime("%B")

            # Year selection
            years = sorted(df["year"].dropna().unique())
            selected_year = st.selectbox("📅 Select Year", years)

            year_df = df[df["year"] == selected_year]

            # Total + Avg
            yearly_total = year_df["amount"].sum()
            months_count = year_df["month"].nunique()
            avg_monthly = yearly_total / months_count if months_count > 0 else 0

            st.markdown("### 💰 Total Spend")
            st.success(f"₹{yearly_total:,.0f}")
            st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

            # Month
            months = year_df["month"].unique()
            selected_month = st.selectbox("📊 Select Month", months)

            filtered = year_df[year_df["month"] == selected_month]

            # Chart
            st.subheader(f"📊 Category Breakdown - {selected_month}")

            cat = filtered.groupby("category")["amount"].sum().reset_index()
            cat = cat.sort_values(by="amount", ascending=False)
            cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

            fig = px.bar(cat, x="category", y="amount", text="label")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=400, yaxis=dict(visible=False))

            st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Compare
# -----------------------
elif menu == "Compare":
    st.subheader("⚖️ Compare Months")

    sheet_input = st.text_input("Paste Google Sheet URL or ID", key="compare_sheet")

    if sheet_input:
        sheet_id = extract_sheet_id(sheet_input)

        df = load_google_sheet(sheet_id)

        df = df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount"
        })

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

        compare = pd.DataFrame({m1: cat1, m2: cat2}).fillna(0).reset_index()

        fig = px.bar(compare, x="category", y=[m1, m2], barmode="group")

        st.plotly_chart(fig, use_container_width=True)
