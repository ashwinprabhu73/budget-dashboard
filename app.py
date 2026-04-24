import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html

st.set_page_config(layout="wide")

st.title("Smart Budget Dashboard")

# =========================
# MENU
# =========================
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

    months = year_df.sort_values("month_num")["month"].unique()
    month = st.selectbox("Select Month", months, index=len(months)-1)

    # ✅ FIX FILTER
    expense_df = year_df[year_df["category"] != "ipo"]

    # YEARLY
    total_year = expense_df["amount"].sum()
    st.write("Total Yearly Spend:", total_year)

    # IPO
    ipo_year = year_df[year_df["category"] == "ipo"]

    html(f"""
    <div style="background:#111827;padding:15px;border-radius:10px;">
        <h4 style="color:#d4af37;">IPO SUMMARY</h4>
        <p>Total: ₹{ipo_year['amount'].sum():,.0f}</p>
        <p>Applied: {len(ipo_year)}</p>
    </div>
    """, height=150)

    # MONTHLY
    mdf = expense_df[expense_df["month"] == month]

    # =========================
    # PERSON LOGIC
    # =========================
    a_spend = h_spend = 0

    for _, r in mdf.iterrows():
        p = str(r.get("paid_by", "")).lower()
        amt = r["amount"]

        if p == "ashwin":
            a_spend += amt
        elif p == "harshita":
            h_spend += amt
        elif p == "us":
            a_spend += amt/2
            h_spend += amt/2

    st.write("Ashwin:", a_spend)
    st.write("Harshita:", h_spend)

    # =========================
    # EXPENSE BREAKDOWN
    # =========================
    cat = mdf.groupby("category")["amount"].sum().reset_index()
    fig = px.bar(cat, x="category", y="amount")
    st.plotly_chart(fig)

    # =========================
    # OTHER
    # =========================
    others = mdf[mdf["category"] == "others"]

    if not others.empty:
        grp = others.groupby("description")["amount"].sum().reset_index()
        fig = go.Figure(data=[go.Pie(
            labels=grp["description"],
            values=grp["amount"]
        )])
        st.plotly_chart(fig)

# =========================
# COMPARE
# =========================
elif menu == "Compare" and not df.empty:

    years = sorted(df["year"].unique())
    y1 = st.selectbox("Year 1", years)
    y2 = st.selectbox("Year 2", years)

    df_y1 = df[df["year"] == y1]
    df_y2 = df[df["year"] == y2]

    comp = pd.DataFrame({
        str(y1): df_y1.groupby("category")["amount"].sum(),
        str(y2): df_y2.groupby("category")["amount"].sum()
    }).fillna(0)

    comp = comp.reset_index().melt(id_vars="category", var_name="Year", value_name="amount")

    fig = px.bar(comp, x="category", y="amount", color="Year", barmode="group")
    st.plotly_chart(fig)
