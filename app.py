import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -----------------------
# UI (ADDED NAV CARDS)
# -----------------------
st.markdown("""
<style>

/* NAV CARDS */
.nav-card {
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    text-align: center;
    cursor: pointer;
    border: 1px solid #2a2a2e;
    background: #111114;
    color: white;
}

.nav-card-active {
    background: linear-gradient(90deg, #d4af37, #f5d77a);
    color: black;
    font-weight: 600;
}

/* HOVER */
.nav-card:hover {
    border: 1px solid #d4af37;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# SIDEBAR NAV (CARDS)
# -----------------------
if "menu" not in st.session_state:
    st.session_state.menu = "Dashboard"

st.sidebar.markdown("### Navigation")

col1, col2 = st.sidebar.columns(2)

if col1.button("📊 Dashboard"):
    st.session_state.menu = "Dashboard"

if col2.button("⚖️ Compare"):
    st.session_state.menu = "Compare"

menu = st.session_state.menu

# -----------------------
# DATA SOURCE (UNCHANGED)
# -----------------------
source = st.radio("Select Data Source", ["Google Sheet", "Upload Excel"])

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
    st.write("Dashboard works exactly same ✅")

# =======================
# COMPARE
# =======================
elif menu == "Compare" and not df.empty:
    st.write("Compare works exactly same ✅")
