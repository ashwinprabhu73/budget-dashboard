import streamlit as st
import pandas as pd
import plotly.express as px

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
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    all_sheets = pd.read_excel(url, sheet_name=None)

    df_list = []
    for _, sheet_data in all_sheets.items():
        df_list.append(sheet_data)

    return pd.concat(df_list, ignore_index=True)

# -----------------------
# Load Excel
# -----------------------
def load_excel(file):
    all_sheets = pd.read_excel(file, sheet_name=None)

    df_list = []
    for _, sheet_data in all_sheets.items():
        df_list.append(sheet_data)

    return pd.concat(df_list, ignore_index=True)

# -----------------------
# Preprocess
# -----------------------
def preprocess(df):
    df = df.rename(columns={
        "Date": "date",
        "Expense": "description",
        "Expns Category": "category",
        "Total cost": "amount",
        "Recurring Expense": "recurring"
    })

    df = df.fillna("")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.strftime("%B")

    return df.sort_values("month_num")

# -----------------------
# UI
# -----------------------
st.set_page_config(layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare"])

# -----------------------
# Data Source
# -----------------------
source = st.radio("Select Data Source", ["Google Sheet", "Upload Excel"])

df = pd.DataFrame()

if source == "Google Sheet":
    sheet_input = st.text_input("🔗 Paste Google Sheet URL or ID")

    if sheet_input:
        sheet_id = extract_sheet_id(sheet_input)
        df = load_google_sheet(sheet_id)

elif source == "Upload Excel":
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = load_excel(file)

# -----------------------
# PROCESS DATA
# -----------------------
if not df.empty:
    df = preprocess(df)

# =======================
# DASHBOARD
# =======================
if menu == "Dashboard" and not df.empty:

    years = sorted(df["year"].unique())
    selected_year = st.selectbox("📅 Select Year", years)

    year_df = df[df["year"] == selected_year]

    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    yearly_total = expense_df["amount"].sum()
    month_count = expense_df["month_num"].nunique()
    avg_monthly = yearly_total / month_count if month_count else 0

    st.markdown("### 💰 Total Spend")
    st.success(f"₹{yearly_total:,.0f}")
    st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

    months = year_df["month"].unique()
    selected_month = st.selectbox("📊 Select Month", months)

    # IPO
    st.markdown("### 💼 IPO Summary")
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    col1, col2 = st.columns(2)
    col1.metric("IPO Amount", f"₹{ipo_month['amount'].sum():,.0f}")
    col2.metric("IPO Entries", len(ipo_month))

    # Expense Chart
    filtered = expense_df[expense_df["month"] == selected_month]

    st.subheader(f"📊 Category Breakdown - {selected_month}")

    cat = filtered.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig = px.bar(cat, x="category", y="amount", text="label")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, yaxis=dict(visible=False))

        st.plotly_chart(fig, use_container_width=True)

# =======================
# COMPARE TAB (NEW 🔥)
# =======================
elif menu == "Compare" and not df.empty:

    st.subheader("⚖️ Compare Months")

    years = sorted(df["year"].unique())

    col1, col2 = st.columns(2)
    y1 = col1.selectbox("Year 1", years)
    y2 = col2.selectbox("Year 2", years)

    m1 = col1.selectbox("Month 1", df[df["year"] == y1]["month"].unique())
    m2 = col2.selectbox("Month 2", df[df["year"] == y2]["month"].unique())

    df1 = df[(df["year"] == y1) & (df["month"] == m1)]
    df2 = df[(df["year"] == y2) & (df["month"] == m2)]

    # Remove IPO from comparison
    df1 = df1[df1["category"].str.lower() != "ipo"]
    df2 = df2[df2["category"].str.lower() != "ipo"]

    cat1 = df1.groupby("category")["amount"].sum()
    cat2 = df2.groupby("category")["amount"].sum()

    compare = pd.DataFrame({
        f"{m1}-{y1}": cat1,
        f"{m2}-{y2}": cat2
    }).fillna(0).reset_index()

    if not compare.empty:
        fig = px.bar(compare, x="category", y=compare.columns[1:], barmode="group")

        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

        # Insight
        total1 = df1["amount"].sum()
        total2 = df2["amount"].sum()

        diff = total1 - total2

        st.subheader("🧠 Insights")

        if diff > 0:
            st.warning(f"{m1}-{y1} is ₹{diff:,.0f} higher")
        else:
            st.success(f"{m1}-{y1} is ₹{abs(diff):,.0f} lower")
