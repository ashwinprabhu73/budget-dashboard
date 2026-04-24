import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(layout="wide")

# =========================
# 🎨 EXACT UI STYLE
# =========================
st.markdown("""
<style>

/* PAGE */
body {
    background: #0b0f14;
    color: white;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1a, #0b0f14);
    border-right: 1px solid #1f2937;
}

/* CARDS */
.card {
    background: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
}

/* TITLES */
.label {
    color: #9ca3af;
    font-size: 14px;
}

.value-gold {
    color: #d4af37;
    font-size: 30px;
    font-weight: 700;
}

/* PERSON */
.person {
    color: #d4af37;
    font-size: 22px;
    font-weight: 700;
}

/* NUMBERS */
.value {
    color: #d4af37;
    font-size: 22px;
    font-weight: 600;
}

.green {
    color: #22c55e;
    font-size: 22px;
    font-weight: 600;
}

.red {
    color: #ef4444;
    font-size: 22px;
    font-weight: 600;
}

.note-green {
    color: #22c55e;
    font-size: 13px;
}

.note-red {
    color: #ef4444;
    font-size: 13px;
}

/* DIVIDER */
hr {
    border: none;
    height: 1px;
    background: #1f2937;
    margin: 10px 0;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
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

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.strftime("%B")
    df["month_num"] = df["date"].dt.month
    return df

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

    st.markdown(f"""
    <div class="card">
        <div class="label">Total Yearly Spend</div>
        <div class="value-gold">₹{total_year:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    month = st.selectbox("Select Month", year_df.sort_values("month_num")["month"].unique())

    mdf = expense_df[expense_df["month"] == month]
    monthly_total = mdf["amount"].sum()

    st.markdown(f"""
    <div class="card">
        <div class="label">{month} Monthly Spend</div>
        <div class="value-gold">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

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

    cols = df.columns
    a_col = find_inhand(cols, "ashwin")
    h_col = find_inhand(cols, "harshita")

    a_in = year_df[a_col].dropna().iloc[-1] if a_col else 0
    h_in = year_df[h_col].dropna().iloc[-1] if h_col else 0

    a_save = a_in - a_spend
    h_save = h_in - h_spend

    col1, col2 = st.columns(2)

    def person_card(name, income, spend, save):
        if save >= 0:
            saving_html = f"""
            <div class="green">₹{save:,.0f}</div>
            <div class="note-green">✔ Great! You're saving well.</div>
            """
        else:
            saving_html = f"""
            <div class="red">-₹{abs(save):,.0f}</div>
            <div class="note-red">⚠ You've overspent this month.</div>
            """

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
            {saving_html}
        </div>
        """

    with col1:
        st.markdown(person_card("Ashwin", a_in, a_spend, a_save), unsafe_allow_html=True)

    with col2:
        st.markdown(person_card("Harshita", h_in, h_spend, h_save), unsafe_allow_html=True)

    # =========================
    # IPO
    # =========================
    ipo = year_df[(year_df["month"] == month) & (year_df["category"].str.lower() == "ipo")]

    st.markdown(f"""
    <div class="card">
        <div class="label">IPO SUMMARY</div>
        <div>Amount: ₹{ipo['amount'].sum():,.0f}</div>
        <div>Entries: {len(ipo)}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # BAR CHART (UNCHANGED)
    # =========================
    cat = mdf.groupby("category")["amount"].sum().reset_index()

    total = cat["amount"].sum()
    cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({(x['amount']/total)*100:.1f}%)", axis=1)

    fig = px.bar(cat, x="category", y="amount", text="label")
    fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # DONUT WITH SIDE LEGEND
    # =========================
    others = mdf[mdf["category"].str.lower() == "others"]

    if not others.empty:
        grp = others.groupby("description")["amount"].sum().reset_index()

        col1, col2 = st.columns([2,1])

        with col1:
            fig = go.Figure(data=[go.Pie(
                labels=grp["description"],
                values=grp["amount"],
                hole=0.6
            )])
            fig.update_layout(
                paper_bgcolor="#0b0f14",
                font=dict(color="white")
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            for _, r in grp.iterrows():
                st.write(f"{r['description']} — ₹{r['amount']:,.0f}")

# =========================
# COMPARE (UNCHANGED)
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
    fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)
