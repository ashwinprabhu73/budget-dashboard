import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -----------------------
# 🎨 UI (ONLY STYLING — NO LOGIC CHANGE)
# -----------------------
st.markdown("""
<style>

/* BACKGROUND */
body {
    background: #0b0f14;
    color: white;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0a0e13;
    border-right: 1px solid #1f2937;
}

/* CARD */
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #1f2937;
}

/* TEXT */
.title {
    font-size: 16px;
    color: #9ca3af;
}

.big {
    font-size: 32px;
    font-weight: 700;
    color: #fbbf24;
}

.person {
    font-size: 20px;
    font-weight: 700;
    color: #fbbf24;
}

.label {
    font-size: 13px;
    color: #9ca3af;
}

.value {
    font-size: 24px;
    font-weight: 600;
    color: #fbbf24;
}

.green {
    color: #22c55e;
    font-size: 24px;
    font-weight: 600;
}

.red {
    color: #ef4444;
    font-size: 24px;
    font-weight: 600;
}

.note-green {
    color: #22c55e;
    font-size: 12px;
}

.note-red {
    color: #ef4444;
    font-size: 12px;
}

hr {
    border: none;
    height: 1px;
    background: #1f2937;
    margin: 10px 0;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# HEADER
# -----------------------
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Compare"])

# -----------------------
# HELPERS (UNCHANGED)
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
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.strftime("%B")
    return df.sort_values(["year", "month_num"])

def find_inhand_column(cols, person):
    for c in cols:
        if person in c and "hand" in c:
            return c
    return None

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
        df = pd.concat(pd.read_excel(file, sheet_name=None).values(), ignore_index=True)

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

    st.markdown(f"""
    <div class="card">
        <div class="title">Total Yearly Spend</div>
        <div class="big">₹{yearly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    months = year_df.sort_values("month_num")["month"].unique()
    selected_month = st.selectbox("Select Month", months, index=len(months)-1)

    monthly_df = expense_df[expense_df["month"] == selected_month]
    monthly_total = monthly_df["amount"].sum()

    st.markdown(f"""
    <div class="card">
        <div class="title">{selected_month} Monthly Spend</div>
        <div class="big">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------
    # PAID BY (UNCHANGED LOGIC)
    # -----------------------
    ashwin_spend, harshita_spend = 0, 0

    if "paid_by" in monthly_df.columns:
        for _, row in monthly_df.iterrows():
            payer = str(row["paid_by"]).strip().lower()
            if payer == "ashwin":
                ashwin_spend += row["amount"]
            elif payer == "harshita":
                harshita_spend += row["amount"]
            elif payer == "us":
                ashwin_spend += row["amount"] / 2
                harshita_spend += row["amount"] / 2

    # -----------------------
    # IN HAND (FIXED)
    # -----------------------
    cols = df.columns

    ashwin_col = find_inhand_column(cols, "ashwin")
    harshita_col = find_inhand_column(cols, "harshita")

    ashwin_inhand = year_df[ashwin_col].dropna().iloc[-1] if ashwin_col else 0
    harshita_inhand = year_df[harshita_col].dropna().iloc[-1] if harshita_col else 0

    ashwin_savings = ashwin_inhand - ashwin_spend
    harshita_savings = harshita_inhand - harshita_spend

    col1, col2 = st.columns(2)

    def person_card(name, income, spend, savings):
        if savings >= 0:
            savings_html = f"""
            <div class="green">₹{savings:,.0f}</div>
            <div class="note-green">✔ Great! You're saving well.</div>
            """
        else:
            savings_html = f"""
            <div class="red">-₹{abs(savings):,.0f}</div>
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
            {savings_html}
        </div>
        """

    with col1:
        st.markdown(person_card("Ashwin", ashwin_inhand, ashwin_spend, ashwin_savings), unsafe_allow_html=True)

    with col2:
        st.markdown(person_card("Harshita", harshita_inhand, harshita_spend, harshita_savings), unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------
    # IPO (UNCHANGED)
    # -----------------------
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    st.markdown(f"""
    <div class="card">
        <div class="title">IPO SUMMARY</div>
        <div>Amount: ₹{ipo_month['amount'].sum():,.0f}</div>
        <div>Entries: {len(ipo_month)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------
    # CATEGORY BAR (UNCHANGED)
    # -----------------------
    cat = monthly_df.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1)

        fig = px.bar(cat, x="category", y="amount", text="label")
        fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)

    # -----------------------
    # OTHERS DONUT (IMPROVED STYLE ONLY)
    # -----------------------
    others_data = monthly_df[monthly_df["category"].str.lower() == "others"]

    if not others_data.empty:
        grp = others_data.groupby("description")["amount"].sum().reset_index()

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

    col1, col2 = st.columns(2)

    y1 = col1.selectbox("Year 1", sorted(df["year"].unique()))
    y2 = col2.selectbox("Year 2", sorted(df["year"].unique()))

    m1 = col1.selectbox("Month 1", df[df["year"] == y1]["month"].unique())
    m2 = col2.selectbox("Month 2", df[df["year"] == y2]["month"].unique())

    df1 = df[(df["year"] == y1) & (df["month"] == m1)]
    df2 = df[(df["year"] == y2) & (df["month"] == m2)]

    df1 = df1[df1["category"].str.lower() != "ipo"]
    df2 = df2[df2["category"].str.lower() != "ipo"]

    compare = pd.DataFrame({
        f"{m1}-{y1}": df1.groupby("category")["amount"].sum(),
        f"{m2}-{y2}": df2.groupby("category")["amount"].sum()
    }).fillna(0)

    compare["total"] = compare.sum(axis=1)
    compare = compare.sort_values(by="total", ascending=False).head(10).drop(columns=["total"]).reset_index()

    melted = compare.melt(id_vars="category", var_name="Month", value_name="amount")

    fig = px.bar(melted, x="category", y="amount", color="Month", barmode="group")
    fig.update_layout(plot_bgcolor="#0b0f14", paper_bgcolor="#0b0f14", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)
