import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(layout="wide")

# -----------------------
# ULTRA PREMIUM UI (CAR BLACK + GOLD)
# -----------------------
st.markdown("""
<style>

/* ===== GLOSSY BLACK BACKGROUND ===== */
body {
    background: radial-gradient(circle at top left, #1a1a1d, #0a0a0c 60%);
    color: #ffffff;
}

/* ===== MAIN CONTAINER ===== */
.block-container {
    padding-top: 2rem;
}

/* ===== TITLE ===== */
h1 {
    color: #f5f5f5;
    font-weight: 600;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0c, #000000);
    color: #d4af37;
}

/* ===== CARD ===== */
.card {
    background: linear-gradient(145deg, #1a1a1d, #111114);
    border-radius: 18px;
    padding: 22px;
    border: 1px solid #2a2a2e;
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
}

/* ===== KPI ===== */
.kpi-card {
    background: linear-gradient(145deg, #1a1a1d, #111114);
    border-radius: 18px;
    padding: 24px;
    border: 1px solid #2a2a2e;
}

/* ===== GOLD TEXT ===== */
.gold-text {
    background: linear-gradient(90deg, #d4af37, #f5d77a, #d4af37);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ===== KPI TEXT ===== */
.kpi-label {
    font-size: 12px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.kpi-value {
    font-size: 36px;
    font-weight: 700;
}

/* ===== IPO CARD ===== */
.gold-card {
    background: linear-gradient(145deg, #1a1a1d, #111114);
    border-radius: 18px;
    padding: 24px;
    border: 1px solid #2a2a2e;
    position: relative;
}

/* GOLD LINE */
.gold-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, #d4af37, #f5d77a);
}

/* IPO TEXT */
.gold-title {
    font-size: 13px;
    color: #d4af37;
    margin-bottom: 10px;
}

.gold-value {
    font-size: 18px;
    font-weight: 600;
}

/* ===== DIVIDER ===== */
hr {
    border: none;
    height: 1px;
    background: #2a2a2e;
    margin: 30px 0;
}

</style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Dashboard")

# -----------------------
# HELPERS (UNCHANGED)
# -----------------------
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
# FILE UPLOAD (UNCHANGED)
# -----------------------
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = preprocess(load_excel(file))

    years = sorted(df["year"].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = df[df["year"] == selected_year]
    months = year_df.sort_values("month_num")["month"].unique()
    selected_month = st.selectbox("Select Month", months, index=len(months)-1)

    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    yearly_total = expense_df["amount"].sum()
    monthly_total = expense_df[expense_df["month"] == selected_month]["amount"].sum()

    # KPI CARDS
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Yearly Spend</div>
            <div class="kpi-value gold-text">₹{yearly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{selected_month} Monthly Spend</div>
            <div class="kpi-value gold-text">₹{monthly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # IPO
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    st.markdown(f"""
    <div class="gold-card">
        <div class="gold-title">IPO SUMMARY</div>
        <div class="gold-value">Amount: ₹{ipo_month['amount'].sum():,.0f}</div>
        <div class="gold-value">Entries: {len(ipo_month)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # CATEGORY
    filtered = expense_df[expense_df["month"] == selected_month]

    st.subheader(f"📊 Category Breakdown - {selected_month}")

    cat = filtered.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside", textfont=dict(size=16))
        fig.update_layout(
            yaxis=dict(visible=False),
            plot_bgcolor="#0a0a0c",
            paper_bgcolor="#0a0a0c",
            font=dict(color="white")
        )

        st.plotly_chart(fig, use_container_width=True)
