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
# Load Google Sheet (ALL TABS)
# -----------------------
def load_google_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    all_sheets = pd.read_excel(url, sheet_name=None)

    df_list = []
    for _, sheet_data in all_sheets.items():
        df_list.append(sheet_data)

    return pd.concat(df_list, ignore_index=True)

# -----------------------
# Load Excel Upload
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
# Process
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

    # Split IPO
    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    # Total + Avg
    yearly_total = expense_df["amount"].sum()
    month_count = expense_df["month_num"].nunique()
    avg_monthly = yearly_total / month_count if month_count else 0

    st.markdown("### 💰 Total Spend")
    st.success(f"₹{yearly_total:,.0f}")
    st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

    # Month
    months = year_df["month"].unique()
    selected_month = st.selectbox("📊 Select Month", months)

    # IPO Summary
    st.markdown("### 💼 IPO Summary")

    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    col1, col2 = st.columns(2)
    col1.metric("IPO Amount", f"₹{ipo_month['amount'].sum():,.0f}")
    col2.metric("IPO Entries", len(ipo_month))

    # Expense Chart
    filtered = expense_df[expense_df["month"] == selected_month]

    st.subheader(f"📊 Category Breakdown - {selected_month}")

    cat = filtered.groupby("category")["amount"].sum().reset_index()
    cat = cat.sort_values(by="amount", ascending=False)

    if not cat.empty:
        cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig = px.bar(cat, x="category", y="amount", text="label")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, yaxis=dict(visible=False))

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data")

    # Recurring
    st.subheader("🔁 Recurring Breakdown")

    rec = filtered[filtered["recurring"].str.lower() == "recurring"]

    if not rec.empty:
        rec_cat = rec.groupby("category")["amount"].sum().reset_index()
        rec_cat["label"] = rec_cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig2 = px.bar(rec_cat, x="category", y="amount", text="label")
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=400, yaxis=dict(visible=False))

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No recurring expenses")

# =======================
# COMPARE (NEW UX 🔥)
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

    # Remove IPO
    df1 = df1[df1["category"].str.lower() != "ipo"]
    df2 = df2[df2["category"].str.lower() != "ipo"]

    total1 = df1["amount"].sum()
    total2 = df2["amount"].sum()

    diff = total1 - total2

    # 🔥 Total Difference
    st.markdown("### 🔥 Total Difference")

    if diff > 0:
        st.error(f"₹{abs(diff):,.0f} higher than {m2}-{y2}")
    elif diff < 0:
        st.success(f"₹{abs(diff):,.0f} lower than {m2}-{y2}")
    else:
        st.info("No difference")

    # 📊 Category Drill-down
    st.markdown("### 📊 Category Comparison")

    categories = sorted(set(df1["category"]).union(set(df2["category"])))
    selected_category = st.selectbox("Select Category", categories)

    cat1 = df1[df1["category"] == selected_category]["amount"].sum()
    cat2 = df2[df2["category"] == selected_category]["amount"].sum()

    c1, c2 = st.columns(2)

    c1.metric(f"{m1}-{y1}", f"₹{cat1:,.0f}")
    c2.metric(f"{m2}-{y2}", f"₹{cat2:,.0f}")

    cat_diff = cat1 - cat2

    if cat_diff > 0:
        st.warning(f"Spending increased by ₹{cat_diff:,.0f}")
    elif cat_diff < 0:
        st.success(f"Spending reduced by ₹{abs(cat_diff):,.0f}")
    else:
        st.info("No change")
