import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# PREMIUM UI (SAFE)
# -----------------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
body {
    background-color: #f8f5f0;
}
h1, h2, h3 {
    font-family: Georgia, serif;
    color: #2c2c2c;
}
.premium-card {
    background: linear-gradient(135deg, #fdfaf6, #f4efe6);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e6dccb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.big-number {
    font-size: 26px;
    font-weight: 600;
    color: #1f3d2b;
}
.caption {
    font-size: 13px;
    color: #7a766f;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Dashboard")

# -----------------------
# HELPERS
# -----------------------
def extract_sheet_id(input_text):
    if "docs.google.com" in input_text:
        return input_text.split("/d/")[1].split("/")[0]
    return input_text

def load_google_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    return pd.concat(pd.read_excel(url, sheet_name=None).values(), ignore_index=True)

def load_excel(file):
    return pd.concat(pd.read_excel(file, sheet_name=None).values(), ignore_index=True)

def preprocess(df):
    df = df.rename(columns={
        "Date": "date",
        "Expense": "description",
        "Expns Category": "category",
        "Total cost": "amount"
    })
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.strftime("%B")
    return df.sort_values(["year", "month_num"])

# -----------------------
# DATA SOURCE
# -----------------------
menu = st.sidebar.radio("Menu", ["Dashboard", "Compare"])
source = st.radio("Select Data Source", ["Google Sheet", "Upload Excel"])

df = pd.DataFrame()

if source == "Google Sheet":
    sheet_input = st.text_input("Paste Google Sheet URL/ID")
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

    years = sorted(df["year"].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = df[df["year"] == selected_year]
    months = year_df.sort_values("month_num")["month"].unique()
    selected_month = st.selectbox("Select Month", months, index=len(months)-1)

    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    yearly_total = expense_df["amount"].sum()
    monthly_total = expense_df[expense_df["month"] == selected_month]["amount"].sum()

    # Premium Cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Total Yearly Spend</div>
            <div class="big-number">₹{yearly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">{selected_month} Monthly Spend</div>
            <div class="big-number">₹{monthly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # IPO
    st.markdown("### 💼 IPO Summary")
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    c1, c2 = st.columns(2)
    c1.metric("IPO Amount", f"₹{ipo_month['amount'].sum():,.0f}")
    c2.metric("IPO Entries", len(ipo_month))

    # Category
    filtered = expense_df[expense_df["month"] == selected_month]

    st.subheader(f"📊 Category Breakdown - {selected_month}")

    cat = filtered.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(
            lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
        )

        fig = px.bar(cat, x="category", y="amount", text="label")
        fig.update_traces(textposition="outside", textfont=dict(size=16))
        fig.update_layout(yaxis=dict(visible=False))

        st.plotly_chart(fig, use_container_width=True)

    # Others
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
                pd.DataFrame([{"description": "Miscellaneous", "amount": misc_total}])
            ])

        fig2 = px.pie(major, names="description", values="amount", hole=0.5)
        st.plotly_chart(fig2, use_container_width=True)

# =======================
# COMPARE (RESTORED ✅)
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
