import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html

st.set_page_config(layout="wide")

# =========================
# 🎨 GLOBAL STYLES
# =========================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background-color: #0b0f14; }
[data-testid="stSidebar"] { background: #0a0f1a; }
h1 { color: #e5e7eb !important; font-size: 42px !important; font-weight: 700; }
label { color: #e5e7eb !important; font-size: 18px !important; }
div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    color: #9ca3af !important;
    border-radius: 10px !important;
    border: 1px solid #1f2937 !important;
}
.block {
    background: #111827;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-bottom: 15px;
}
.gold { color: #d4af37; font-weight: bold; }
.value { font-size: 26px; }
.green { color: #22c55e; font-weight: bold; }
.red { color: #ef4444; font-weight: bold; }
.label { color: #9ca3af; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.title("Smart Budget Dashboard")
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Compare"])

# =========================
# HELPERS
# =========================
def extract_sheet_id(url):
    return url.split("/d/")[1].split("/")[0] if "docs.google.com" in url else url

def load_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    return pd.concat(pd.read_excel(url, sheet_name=None).values(), ignore_index=True)

def preprocess(df):
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "date": "date",
        "expense": "description",
        "expns category": "category",
        "total cost": "amount",
        "paid by": "paid_by"
    })
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.strftime("%B")
    df["month_num"] = df["date"].dt.month
    return df.sort_values(["year", "month_num"])

def find_inhand(cols, person):
    for c in cols:
        if person in c.lower() and "hand" in c.lower():
            return c
    return None

# =========================
# DATA
# =========================
sheet = st.sidebar.text_input("Paste Google Sheet URL/ID")
df = pd.DataFrame()

if sheet:
    df = preprocess(load_sheet(extract_sheet_id(sheet)))

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard" and not df.empty:

    years = sorted(df["year"].unique())
    year = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = df[df["year"] == year].copy()
    year_df["category"] = year_df["category"].astype(str).str.lower()

    months_df = year_df.sort_values("month_num")
    months = months_df["month"].unique()
    month = st.selectbox("Select Month", months, index=len(months)-1)

    # ✅ FIX: exclude IPO only
    expense_df = year_df[year_df["category"] != "ipo"]

    # =========================
    # YEARLY
    # =========================
    total_year = expense_df["amount"].sum()

    st.markdown(f"""
    <div class="block">
    <div class="label">Total Yearly Spend</div>
    <div class="gold value">₹{total_year:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # IPO (FIXED ONLY)
    # =========================
    ipo_year = year_df[year_df["category"] == "ipo"]

    html(f"""
    <div style="background:#111827;padding:18px;border-radius:12px;border:1px solid #1f2937;margin-bottom:15px;">
        <div style="color:#d4af37;font-weight:bold;font-size:18px;">YEARLY IPO SUMMARY</div>

        <div style="display:flex;justify-content:space-between;margin-top:15px;">
            <div>
                <div style="color:#9ca3af;">Total Amount Utilised</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">
                    ₹{ipo_year['amount'].sum():,.0f}
                </div>
            </div>
            <div>
                <div style="color:#9ca3af;">Allotment Profit</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">₹0</div>
            </div>
        </div>

        <div style="display:flex;justify-content:space-between;margin-top:20px;">
            <div>
                <div style="color:#9ca3af;">Applied</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">
                    {len(ipo_year)}
                </div>
            </div>
            <div>
                <div style="color:#9ca3af;">Allotted</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">0</div>
            </div>
        </div>
    </div>
    """, height=220)

    # =========================
    # MONTHLY
    # =========================
    mdf = expense_df[expense_df["month"] == month]

    monthly_total = mdf["amount"].sum()

    st.markdown(f"""
    <div class="block">
    <div class="label">{month} Monthly Spend</div>
    <div class="gold value">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # EVERYTHING BELOW UNCHANGED (your original logic)
    # =========================
