import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# =========================
# 🎨 GLOBAL DARK THEME
# =========================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b0f14;
}

[data-testid="stSidebar"] {
    background: #0a0f1a;
}

h1 {
    color: #e5e7eb !important;
    font-size: 42px !important;
    font-weight: 700;
}

label {
    color: #e5e7eb !important;
    font-size: 18px !important;
    font-weight: 500;
}

div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    color: #9ca3af !important;
    border-radius: 10px !important;
    border: 1px solid #1f2937 !important;
}

div[data-baseweb="select"] span {
    color: #9ca3af !important;
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
    if "docs.google.com" in url:
        return url.split("/d/")[1].split("/")[0]
    return url

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
        if person in c and "hand" in c:
            return c
    return None

# =========================
# DATA
# =========================
sheet = st.sidebar.text_input("Paste Google Sheet")
df = pd.DataFrame()

if sheet:
    df = preprocess(load_sheet(extract_sheet_id(sheet)))

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard" and not df.empty:

    years = sorted(df["year"].unique())
    default_year = max(years)

    year = st.selectbox("Select Year", years, index=years.index(default_year))
    year_df = df[df["year"] == year]

    months_df = year_df.sort_values("month_num")
    months = months_df["month"].unique()
    latest_month = months_df.iloc[-1]["month"]

    month = st.selectbox("Select Month", months, index=list(months).index(latest_month))

    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    total_year = expense_df["amount"].sum()

    st.markdown(f"""
<div class="block">
<div class="label">Total Yearly Spend</div>
<div class="gold value">₹{total_year:,.0f}</div>
</div>
""", unsafe_allow_html=True)

    mdf = expense_df[expense_df["month"] == month]
    monthly_total = mdf["amount"].sum()

    st.markdown(f"""
<div class="block">
<div class="label">{month} Monthly Spend</div>
<div class="gold value">₹{monthly_total:,.0f}</div>
</div>
""", unsafe_allow_html=True)

    # Paid By logic (UNCHANGED)
    a_spend, h_spend = 0, 0
    for _, r in mdf.iterrows():
        p = str(r.get("paid_by", "")).lower()
        if p == "ashwin":
            a_spend += r["amount"]
        elif p == "harshita":
            h_spend += r["amount"]
        elif p == "us":
            a_spend += r["amount"]/2
            h_spend += r["amount"]/2

    cols = df.columns
    a_col = find_inhand(cols, "ashwin")
    h_col = find_inhand(cols, "harshita")

    a_in, h_in = 0, 0

    if a_col:
        vals = year_df[a_col].dropna()
        if not vals.empty:
            a_in = vals.iloc[-1]

    if h_col:
        vals = year_df[h_col].dropna()
        if not vals.empty:
            h_in = vals.iloc[-1]

    a_save = a_in - a_spend
    h_save = h_in - h_spend

    col1, col2 = st.columns(2)

    def render_person(name, income, spend, save, col):
        with col:
            html = f"""<div class="block">
<div class="gold" style="font-size:22px;">{name}</div>
<div class="label">In Hand</div>
<div class="gold value">₹{income:,.0f}</div>
<div class="label">Spent</div>
<div class="gold value">₹{spend:,.0f}</div>
<div class="label">Savings</div>"""

            if save >= 0:
                html += f"""
<div class="green value">₹{save:,.0f}</div>
<div class="green">✔ Great! You're saving well.</div>"""
            else:
                html += f"""
<div class="red value">-₹{abs(save):,.0f}</div>
<div class="red">⚠ You've overspent this month.</div>"""

            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

    render_person("Ashwin", a_in, a_spend, a_save, col1)
    render_person("Harshita", h_in, h_spend, h_save, col2)

    # =========================
    # COMPARE TAB
    # =========================
elif menu == "Compare" and not df.empty:

    years = sorted(df["year"].unique())
    latest_year = max(years)

    col1, col2 = st.columns(2)

    with col1:
        y1 = st.selectbox("Year 1", years, index=years.index(latest_year))
    with col2:
        y2 = st.selectbox("Year 2", years, index=years.index(latest_year))

    df_y1 = df[df["year"] == y1].sort_values("month_num")
    df_y2 = df[df["year"] == y2].sort_values("month_num")

    months1 = df_y1["month"].unique()
    months2 = df_y2["month"].unique()

    latest_m1 = df_y1.iloc[-1]["month"]
    latest_m2 = df_y2.iloc[-1]["month"]

    col3, col4 = st.columns(2)

    with col3:
        m1 = st.selectbox("Month 1", months1, index=list(months1).index(latest_m1))
    with col4:
        m2 = st.selectbox("Month 2", months2, index=list(months2).index(latest_m2))

    d1 = df[(df["year"]==y1)&(df["month"]==m1)]
    d2 = df[(df["year"]==y2)&(df["month"]==m2)]

    comp = pd.DataFrame({
        f"{m1}-{y1}": d1.groupby("category")["amount"].sum(),
        f"{m2}-{y2}": d2.groupby("category")["amount"].sum()
    }).fillna(0)

    comp = comp.reset_index().melt(id_vars="category", var_name="Month", value_name="amount")

    fig = px.bar(comp, x="category", y="amount", color="Month", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
