import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(layout="wide")

# -----------------------
# UI (SAFE DARK THEME ONLY)
# -----------------------
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top left, #1b1b1f, #0a0a0c 60%);
    color: #ffffff;
}
h1 { color: #f5f5f5; }

section[data-testid="stSidebar"] {
    background: #000000;
    color: #cfcfcf;
}

.premium-card {
    background: linear-gradient(145deg, #1a1a1d, #111114);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid #2a2a2e;
}

.caption {
    font-size: 12px;
    color: #9ca3af;
}

.big-number {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(90deg, #d4af37, #f5d77a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.gold-card {
    background: linear-gradient(145deg, #1a1a1d, #111114);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid #2a2a2e;
    position: relative;
}

.gold-card::before {
    content: "";
    position: absolute;
    top: 0;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, #d4af37, #f5d77a);
}

.gold-title { color: #d4af37; }
.gold-value { font-size: 18px; }

hr {
    border: none;
    height: 1px;
    background: #2a2a2e;
    margin: 25px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Dashboard")

# -----------------------
# NAVIGATION (ORIGINAL)
# -----------------------
menu = st.sidebar.radio("Menu", ["Dashboard", "Compare"])

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

    st.markdown("<hr>", unsafe_allow_html=True)

    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    st.markdown(f"""
    <div class="gold-card">
        <div class="gold-title">IPO SUMMARY</div>
        <div class="gold-value">Amount: ₹{ipo_month['amount'].sum():,.0f}</div>
        <div class="gold-value">Entries: {len(ipo_month)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    filtered = expense_df[expense_df["month"] == selected_month]

    st.subheader(f"📊 Category Breakdown - {selected_month}")

    cat = filtered.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1)

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside", textfont=dict(size=16, color="white"))
        fig.update_layout(
            yaxis=dict(visible=False),
            plot_bgcolor="#0a0a0c",
            paper_bgcolor="#0a0a0c",
            font=dict(color="white"),
            legend=dict(font=dict(color="white")),
            xaxis=dict(tickfont=dict(color="white"))
        )

        st.plotly_chart(fig, use_container_width=True)

    others_data = filtered[filtered["category"].str.lower() == "others"]

    if not others_data.empty:
        st.markdown("### 🔍 Others Breakdown")

        others_group = others_data.groupby("description")["amount"].sum().reset_index()

        fig2 = px.pie(others_group, names="description", values="amount", hole=0.5)

        fig2.update_layout(
            plot_bgcolor="#0a0a0c",
            paper_bgcolor="#0a0a0c",
            font=dict(color="white"),
            legend=dict(font=dict(color="white"))
        )

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

    st.markdown("### 🔥 Total Difference")
    st.write(f"{m1}-{y1}: ₹{total1:,.0f}")
    st.write(f"{m2}-{y2}: ₹{total2:,.0f}")

    cat1 = df1.groupby("category")["amount"].sum()
    cat2 = df2.groupby("category")["amount"].sum()

    compare = pd.DataFrame({
        f"{m1}-{y1}": cat1,
        f"{m2}-{y2}": cat2
    }).fillna(0)

    compare["total"] = compare.sum(axis=1)
    compare = compare.sort_values(by="total", ascending=False).head(10)
    compare = compare.drop(columns=["total"]).reset_index()

    melted = compare.melt(id_vars="category", var_name="Month", value_name="amount")
    melted["label"] = melted["amount"].apply(lambda x: f"₹{x:,.0f}")

    fig = px.bar(melted, x="category", y="amount", color="Month", barmode="group", text="label")

    fig.update_traces(textposition="outside", textfont=dict(size=14, color="white"))
    fig.update_layout(
        yaxis=dict(visible=False),
        plot_bgcolor="#0a0a0c",
        paper_bgcolor="#0a0a0c",
        font=dict(color="white"),
        legend=dict(font=dict(color="white")),
        xaxis=dict(tickfont=dict(color="white"))
    )

    st.plotly_chart(fig, use_container_width=True)
