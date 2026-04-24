import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html

st.set_page_config(layout="wide")

# =========================
# 🎨 UI STYLES
# =========================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background-color: #0b0f14; }
[data-testid="stSidebar"] { background: #0a0f1a; }

.block {
    background: #111827;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-bottom: 15px;
}

.gold { color: #d4af37; font-weight: bold; }
.value { font-size: 26px; }
.label { color: #9ca3af; font-size: 13px; }
.green { color: #22c55e; }
.red { color: #ef4444; }

.section-title {
    color: #60a5fa;
    font-size: 20px;
    margin-top: 20px;
}
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
    return df

def find_inhand(cols, name):
    for c in cols:
        if name in c.lower() and "hand" in c.lower():
            return c
    return None

# =========================
# DATA
# =========================
sheet = st.sidebar.text_input("Paste Sheet URL")
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

    # FILTER
    expense_df = year_df[year_df["category"] != "ipo"]

    # =========================
    # YEARLY
    # =========================
    total_year = expense_df["amount"].sum()
    st.markdown(f"<div class='block'><div class='label'>Total Yearly Spend</div><div class='gold value'>₹{total_year:,.0f}</div></div>", unsafe_allow_html=True)

    # =========================
    # IPO
    # =========================
    ipo_year = year_df[year_df["category"] == "ipo"]

    html(f"""
    <div style="background:#111827;padding:18px;border-radius:12px;border:1px solid #1f2937;margin-bottom:15px;">
        <div style="color:#d4af37;font-weight:bold;font-size:18px;">YEARLY IPO SUMMARY</div>
        <div style="display:flex;justify-content:space-between;margin-top:15px;">
            <div>
                <div style="color:#9ca3af;">Total Amount Utilised</div>
                <div style="color:#d4af37;font-size:24px;">₹{ipo_year['amount'].sum():,.0f}</div>
            </div>
            <div>
                <div style="color:#9ca3af;">Applied</div>
                <div style="color:#d4af37;font-size:24px;">{len(ipo_year)}</div>
            </div>
        </div>
    </div>
    """, height=200)

    # =========================
    # MONTHLY
    # =========================
    mdf = expense_df[expense_df["month"] == month]
    monthly_total = mdf["amount"].sum()

    st.markdown(f"<div class='block'><div class='label'>{month} Spend</div><div class='gold value'>₹{monthly_total:,.0f}</div></div>", unsafe_allow_html=True)

    # =========================
    # PERSON CARDS (RESTORED)
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

    cols = df.columns
    a_in = year_df[find_inhand(cols, "ashwin")].dropna().iloc[-1]
    h_in = year_df[find_inhand(cols, "harshita")].dropna().iloc[-1]

    col1, col2 = st.columns(2)

    def card(name, income, spend, col):
        save = income - spend
        color = "green" if save >= 0 else "red"

        with col:
            st.markdown(f"""
            <div class="block">
                <div class="gold">{name}</div>
                <div class="label">In Hand</div>
                <div class="gold value">₹{income:,.0f}</div>

                <div class="label">Spent</div>
                <div class="gold value">₹{spend:,.0f}</div>

                <div class="label">Savings</div>
                <div class="{color} value">₹{save:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    card("Ashwin", a_in, a_spend, col1)
    card("Harshita", h_in, h_spend, col2)

    # =========================
    # EXPENSE BREAKDOWN (RESTORED)
    # =========================
    st.markdown("<div class='section-title'>Expense Breakdown</div>", unsafe_allow_html=True)

    cat = mdf.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({(x['amount']/total)*100:.1f}%)", axis=1)

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(marker_color="#d4af37", textposition="outside")

        fig.update_layout(
            plot_bgcolor="#0b0f14",
            paper_bgcolor="#0b0f14",
            font=dict(color="white"),
            yaxis=dict(showgrid=False, showticklabels=False)
        )

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # OTHER EXPENSES (RESTORED)
    # =========================
    others = mdf[mdf["category"] == "others"]

    if not others.empty:
        st.markdown("<div class='section-title'>Other Expenses</div>", unsafe_allow_html=True)

        grp = others.groupby("description")["amount"].sum().reset_index()

        fig = go.Figure(data=[go.Pie(
            labels=grp["description"],
            values=grp["amount"],
            hole=0.6
        )])

        st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig, use_container_width=True)
