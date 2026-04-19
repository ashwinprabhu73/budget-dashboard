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
    return pd.concat(all_sheets.values(), ignore_index=True)

# -----------------------
# Load Excel
# -----------------------
def load_excel(file):
    all_sheets = pd.read_excel(file, sheet_name=None)
    return pd.concat(all_sheets.values(), ignore_index=True)

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
source = st.radio("Select Data Source", ["Google Sheet", "Upload Excel"])

df = pd.DataFrame()

if source == "Google Sheet":
    sheet_input = st.text_input("🔗 Paste Google Sheet URL or ID")
    if sheet_input:
        df = load_google_sheet(extract_sheet_id(sheet_input))

elif source == "Upload Excel":
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = load_excel(file)

if not df.empty:
    df = preprocess(df)

# =======================
# DASHBOARD
# =======================
if menu == "Dashboard" and not df.empty:

    selected_year = st.selectbox("📅 Select Year", sorted(df["year"].unique()))
    year_df = df[df["year"] == selected_year]

    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    yearly_total = expense_df["amount"].sum()
    avg_monthly = yearly_total / expense_df["month_num"].nunique()

    st.markdown("### 💰 Total Spend")
    st.success(f"₹{yearly_total:,.0f}")
    st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

    selected_month = st.selectbox("📊 Select Month", year_df["month"].unique())

    # IPO Summary
    st.markdown("### 💼 IPO Summary")
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    col1, col2 = st.columns(2)
    col1.metric("IPO Amount", f"₹{ipo_month['amount'].sum():,.0f}")
    col2.metric("IPO Entries", len(ipo_month))

    # Filter
    filtered = expense_df[expense_df["month"] == selected_month]
    monthly_total = filtered["amount"].sum()

    st.subheader(
        f"📊 Category Breakdown - {selected_month} | ₹{monthly_total:,.0f}"
    )

    cat = filtered.groupby("category")["amount"].sum().reset_index()
    cat = cat.sort_values(by="amount", ascending=False)

    if not cat.empty:
        total = cat["amount"].sum()

        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(
            lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
        )

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, yaxis=dict(visible=False))

        st.plotly_chart(fig, use_container_width=True)

        # Others Breakdown
        others_data = filtered[filtered["category"].str.lower() == "others"]

        if not others_data.empty:
            st.markdown("### 🔍 Others Breakdown")

            others_group = others_data.groupby("description")["amount"].sum().reset_index()

            total_others = others_group["amount"].sum()
            others_group["percent"] = (others_group["amount"] / total_others) * 100

            major = others_group[others_group["percent"] >= 1]
            minor = others_group[others_group["percent"] < 1]

            misc_total = minor["amount"].sum()

            if misc_total > 0:
                major = pd.concat([
                    major,
                    pd.DataFrame([{
                        "description": "Miscellaneous",
                        "amount": misc_total
                    }])
                ])

            fig2 = px.pie(
                major,
                names="description",
                values="amount",
                hole=0.5
            )

            fig2.update_traces(textinfo="percent+label")

            st.plotly_chart(fig2, use_container_width=True)

# =======================
# COMPARE
# =======================
elif menu == "Compare" and not df.empty:

    st.subheader("⚖️ Compare Months")

    col1, col2 = st.columns(2)

    y1 = col1.selectbox("Year 1", sorted(df["year"].unique()))
    y2 = col2.selectbox("Year 2", sorted(df["year"].unique()))

    m1 = col1.selectbox("Month 1", df[df["year"] == y1]["month"].unique())
    m2 = col2.selectbox("Month 2", df[df["year"] == y2]["month"].unique())

    df1 = df[(df["year"] == y1) & (df["month"] == m1)]
    df2 = df[(df["year"] == y2) & (df["month"] == m2)]

    df1 = df1[df1["category"].str.lower() != "ipo"]
    df2 = df2[df2["category"].str.lower() != "ipo"]

    total1 = df1["amount"].sum()
    total2 = df2["amount"].sum()

    diff = total1 - total2

    st.markdown("### 🔥 Total Difference")

    if diff > 0:
        st.error(f"₹{abs(diff):,.0f} higher")
    elif diff < 0:
        st.success(f"₹{abs(diff):,.0f} lower")
    else:
        st.info("No difference")

    # Top 10 Compare
    st.markdown("### 📊 Top 10 Category Comparison")

    cat1 = df1.groupby("category")["amount"].sum()
    cat2 = df2.groupby("category")["amount"].sum()

    compare = pd.DataFrame({
        f"{m1}-{y1}": cat1,
        f"{m2}-{y2}": cat2
    }).fillna(0)

    compare["total"] = compare.sum(axis=1)
    compare = compare.sort_values(by="total", ascending=False).head(10)
    compare = compare.drop(columns=["total"]).reset_index()

    compare[f"{m1}-{y1}_pct"] = (compare[f"{m1}-{y1}"] / total1) * 100
    compare[f"{m2}-{y2}_pct"] = (compare[f"{m2}-{y2}"] / total2) * 100

    melted = pd.DataFrame()

    for month in [f"{m1}-{y1}", f"{m2}-{y2}"]:
        temp = compare[["category", month, f"{month}_pct"]].copy()
        temp.columns = ["category", "amount", "percent"]
        temp["Month"] = month
        melted = pd.concat([melted, temp])

    melted["label"] = melted.apply(
        lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
    )

    fig = px.bar(
        melted,
        x="category",
        y="amount",
        color="Month",
        barmode="group",
        text="label"
    )

    fig.update_traces(textposition="outside")

    # 🔥 CLEAN LOOK FIX
    fig.update_layout(
        height=500,
        yaxis=dict(visible=False),
        xaxis_title=""
    )

    st.plotly_chart(fig, use_container_width=True)
