import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -----------------------
# UI
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
    color: #ffffff;
}

/* CARDS */
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
    font-size: 28px;
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
}

hr {
    border: none;
    height: 1px;
    background: #2a2a2e;
    margin: 25px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Dashboard")

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
        "Total cost": "amount",
        "Paid By": "paid_by"
    })
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.strftime("%B")
    return df.sort_values(["year", "month_num"])

# -----------------------
# DATA
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

    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]
    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    yearly_total = expense_df["amount"].sum()

    # YEARLY
    st.markdown(f"""
    <div class="premium-card">
        <div class="caption">Total Yearly Spend</div>
        <div class="big-number">₹{yearly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # MONTH
    months = year_df.sort_values("month_num")["month"].unique()
    selected_month = st.selectbox("Select Month", months, index=len(months)-1)

    monthly_df = expense_df[expense_df["month"] == selected_month]
    monthly_total = monthly_df["amount"].sum()

    st.markdown(f"""
    <div class="premium-card">
        <div class="caption">{selected_month} Monthly Spend</div>
        <div class="big-number">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # ======================
    # NEW FEATURE 🔥
    # ======================
    ashwin = 0
    harshita = 0

    for _, row in monthly_df.iterrows():
        if row["paid_by"] == "Ashwin":
            ashwin += row["amount"]
        elif row["paid_by"] == "Harshita":
            harshita += row["amount"]
        elif row["paid_by"] == "US":
            ashwin += row["amount"] / 2
            harshita += row["amount"] / 2

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Ashwin Spend</div>
            <div class="big-number">₹{ashwin:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Harshita Spend</div>
            <div class="big-number">₹{harshita:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # IPO
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    st.markdown(f"""
    <div class="gold-card">
        <div class="caption">IPO SUMMARY</div>
        <div>Amount: ₹{ipo_month['amount'].sum():,.0f}</div>
        <div>Entries: {len(ipo_month)}</div>
    </div>
    """, unsafe_allow_html=True)
