import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(layout="wide")

# =========================
# 🎨 LIGHT CSS ONLY (SAFE)
# =========================
st.markdown("""
<style>
.big-number {
    color: #d4af37;
    font-size: 28px;
    font-weight: bold;
}
.person-title {
    color: #d4af37;
    font-size: 20px;
    font-weight: bold;
}
.green { color: #22c55e; font-weight: bold; }
.red { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("Smart Budget Dashboard")

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Compare"])

# =========================
# HELPERS (UNCHANGED)
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
    df = load_sheet(extract_sheet_id(sheet))
    df = preprocess(df)

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard" and not df.empty:

    year = st.selectbox("Select Year", sorted(df["year"].unique()))
    year_df = df[df["year"] == year]

    expense_df = year_df[year_df["category"].str.lower() != "ipo"]

    total_year = expense_df["amount"].sum()

    st.subheader("Total Yearly Spend")
    st.markdown(f"<div class='big-number'>₹{total_year:,.0f}</div>", unsafe_allow_html=True)

    month = st.selectbox("Select Month", year_df.sort_values("month_num")["month"].unique())

    mdf = expense_df[expense_df["month"] == month]
    monthly_total = mdf["amount"].sum()

    st.subheader(f"{month} Monthly Spend")
    st.markdown(f"<div class='big-number'>₹{monthly_total:,.0f}</div>", unsafe_allow_html=True)

    # =========================
    # PAID BY
    # =========================
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

    # =========================
    # IN HAND
    # =========================
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

    with col1:
        st.markdown("<div class='person-title'>Ashwin</div>", unsafe_allow_html=True)
        st.write("In Hand")
        st.markdown(f"<div class='big-number'>₹{a_in:,.0f}</div>", unsafe_allow_html=True)

        st.write("Spent")
        st.markdown(f"<div class='big-number'>₹{a_spend:,.0f}</div>", unsafe_allow_html=True)

        st.write("Savings")
        if a_save >= 0:
            st.markdown(f"<div class='green'>₹{a_save:,.0f}</div>", unsafe_allow_html=True)
            st.markdown("<div class='green'>✔ Great! You're saving well.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='red'>-₹{abs(a_save):,.0f}</div>", unsafe_allow_html=True)
            st.markdown("<div class='red'>⚠ You've overspent this month.</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='person-title'>Harshita</div>", unsafe_allow_html=True)
        st.write("In Hand")
        st.markdown(f"<div class='big-number'>₹{h_in:,.0f}</div>", unsafe_allow_html=True)

        st.write("Spent")
        st.markdown(f"<div class='big-number'>₹{h_spend:,.0f}</div>", unsafe_allow_html=True)

        st.write("Savings")
        if h_save >= 0:
            st.markdown(f"<div class='green'>₹{h_save:,.0f}</div>", unsafe_allow_html=True)
            st.markdown("<div class='green'>✔ Great! You're saving well.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='red'>-₹{abs(h_save):,.0f}</div>", unsafe_allow_html=True)
            st.markdown("<div class='red'>⚠ You've overspent this month.</div>", unsafe_allow_html=True)

    # =========================
    # IPO
    # =========================
    ipo = year_df[(year_df["month"] == month) & (year_df["category"].str.lower() == "ipo")]

    st.subheader("IPO Summary")
    st.write("Amount:", ipo["amount"].sum())
    st.write("Entries:", len(ipo))

    # =========================
    # BAR CHART
    # =========================
    cat = mdf.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({(x['amount']/total)*100:.1f}%)", axis=1)

        fig = px.bar(cat, x="category", y="amount", text="label")
        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # DONUT
    # =========================
    others = mdf[mdf["category"].str.lower() == "others"]

    if not others.empty:
        grp = others.groupby("description")["amount"].sum().reset_index()
        fig = go.Figure(data=[go.Pie(labels=grp["description"], values=grp["amount"], hole=0.6)])
        st.plotly_chart(fig, use_container_width=True)

# =========================
# COMPARE
# =========================
elif menu == "Compare" and not df.empty:

    y1 = st.selectbox("Year 1", df["year"].unique())
    y2 = st.selectbox("Year 2", df["year"].unique())

    m1 = st.selectbox("Month 1", df[df["year"]==y1]["month"].unique())
    m2 = st.selectbox("Month 2", df[df["year"]==y2]["month"].unique())

    d1 = df[(df["year"]==y1)&(df["month"]==m1)]
    d2 = df[(df["year"]==y2)&(df["month"]==m2)]

    comp = pd.DataFrame({
        f"{m1}-{y1}": d1.groupby("category")["amount"].sum(),
        f"{m2}-{y2}": d2.groupby("category")["amount"].sum()
    }).fillna(0)

    comp = comp.reset_index().melt(id_vars="category", var_name="Month", value_name="amount")

    fig = px.bar(comp, x="category", y="amount", color="Month", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
