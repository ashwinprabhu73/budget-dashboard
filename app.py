import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -----------------------
# 🎨 UI STYLES
# -----------------------
st.markdown("""
<style>

/* GLOBAL */
body {
    background: #0b0f14;
    color: #ffffff;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0a0e13;
    border-right: 1px solid #1f2937;
}

/* CARDS */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #1f2937;
}

/* TITLES */
.title {
    font-size: 18px;
    color: #9ca3af;
}

.main-value {
    font-size: 34px;
    font-weight: 700;
    color: #eab308;
}

/* PERSON */
.person {
    font-size: 22px;
    font-weight: 700;
    color: #fbbf24;
}

.label {
    color: #9ca3af;
    font-size: 14px;
}

.value {
    font-size: 26px;
    font-weight: 600;
    color: #fbbf24;
}

.positive {
    color: #22c55e;
    font-size: 26px;
    font-weight: 600;
}

.negative {
    color: #ef4444;
    font-size: 26px;
    font-weight: 600;
}

.note-positive {
    color: #22c55e;
    font-size: 13px;
}

.note-negative {
    color: #ef4444;
    font-size: 13px;
}

hr {
    border: none;
    height: 1px;
    background: #1f2937;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# HEADER
# -----------------------
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Compare"])

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
    return df

def find_inhand_column(cols, person):
    for c in cols:
        if person in c and "hand" in c:
            return c
    return None

# -----------------------
# DATA
# -----------------------
sheet_input = st.sidebar.text_input("Google Sheet URL/ID")

df = pd.DataFrame()

if sheet_input:
    df = load_google_sheet(extract_sheet_id(sheet_input))
    df = preprocess(df)

# =======================
# DASHBOARD
# =======================
if menu == "Dashboard" and not df.empty:

    year = st.selectbox("Select Year", sorted(df["year"].unique()))
    year_df = df[df["year"] == year]

    total_year = year_df[year_df["category"].str.lower() != "ipo"]["amount"].sum()

    st.markdown(f"""
    <div class="card">
        <div class="title">Total Yearly Spend</div>
        <div class="main-value">₹{total_year:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    month = st.selectbox("Select Month", year_df["month"].unique())

    mdf = year_df[(year_df["month"] == month) & (year_df["category"].str.lower() != "ipo")]

    monthly_total = mdf["amount"].sum()

    st.markdown(f"""
    <div class="card">
        <div class="title">{month} Monthly Spend</div>
        <div class="main-value">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------
    # PAID BY
    # -----------------------
    a_spend = 0
    h_spend = 0

    for _, r in mdf.iterrows():
        p = str(r.get("paid_by", "")).lower()

        if p == "ashwin":
            a_spend += r["amount"]
        elif p == "harshita":
            h_spend += r["amount"]
        elif p == "us":
            a_spend += r["amount"]/2
            h_spend += r["amount"]/2

    # -----------------------
    # IN HAND
    # -----------------------
    cols = df.columns
    a_col = find_inhand_column(cols, "ashwin")
    h_col = find_inhand_column(cols, "harshita")

    a_in = year_df[a_col].dropna().iloc[-1] if a_col else 0
    h_in = year_df[h_col].dropna().iloc[-1] if h_col else 0

    a_save = a_in - a_spend
    h_save = h_in - h_spend

    col1, col2 = st.columns(2)

    def card(name, income, spend, save):
        if save >= 0:
            savings_html = f'<div class="positive">₹{save:,.0f}</div><div class="note-positive">✔ Great! You\'re saving well.</div>'
        else:
            savings_html = f'<div class="negative">-₹{abs(save):,.0f}</div><div class="note-negative">⚠ You\'ve overspent this month.</div>'

        return f"""
        <div class="card">
            <div class="person">{name}</div>
            <div class="label">In Hand</div>
            <div class="value">₹{income:,.0f}</div>
            <hr>
            <div class="label">Spent</div>
            <div class="value">₹{spend:,.0f}</div>
            <hr>
            <div class="label">Savings</div>
            {savings_html}
        </div>
        """

    with col1:
        st.markdown(card("Ashwin", a_in, a_spend, a_save), unsafe_allow_html=True)

    with col2:
        st.markdown(card("Harshita", h_in, h_spend, h_save), unsafe_allow_html=True)

    # -----------------------
    # IPO
    # -----------------------
    ipo = year_df[(year_df["month"] == month) & (year_df["category"].str.lower() == "ipo")]

    st.markdown(f"""
    <div class="card">
        <div class="title">IPO SUMMARY</div>
        <div>Amount: ₹{ipo['amount'].sum():,.0f}</div>
        <div>Entries: {len(ipo)}</div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------
    # BAR CHART (UNCHANGED)
    # -----------------------
    cat = mdf.groupby("category")["amount"].sum().reset_index()

    total = cat["amount"].sum()
    cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({(x['amount']/total)*100:.1f}%)", axis=1)

    fig = px.bar(cat, x="category", y="amount", text="label")
    fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

    # -----------------------
    # OTHERS DONUT (IMPROVED STYLE)
    # -----------------------
    others = mdf[mdf["category"].str.lower() == "others"]

    if not others.empty:
        grp = others.groupby("description")["amount"].sum().reset_index()

        fig2 = px.pie(grp, names="description", values="amount", hole=0.6)

        fig2.update_traces(textinfo="percent+label")

        fig2.update_layout(
            plot_bgcolor="#0b0f14",
            paper_bgcolor="#0b0f14",
            font=dict(color="white"),
            title="Others Breakdown"
        )

        st.plotly_chart(fig2, use_container_width=True)

# =======================
# COMPARE (UNCHANGED)
# =======================
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

    comp = comp.sort_values(by=list(comp.columns)[0], ascending=False).head(10)

    comp = comp.reset_index().melt(id_vars="category", var_name="Month", value_name="amount")

    fig = px.bar(comp, x="category", y="amount", color="Month", barmode="group")
    fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)
