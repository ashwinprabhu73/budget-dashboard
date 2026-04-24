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

    # -----------------------
    # PAID BY + IN HAND + SAVINGS
    # -----------------------
    ashwin_spend = 0
    harshita_spend = 0

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

    cols = df.columns

    ashwin_inhand = 0
    harshita_inhand = 0

    if "ashwin in hand" in cols:
        ashwin_inhand = year_df["ashwin in hand"].dropna().iloc[-1]

    if "harshita in hand" in cols:
        harshita_inhand = year_df["harshita in hand"].dropna().iloc[-1]

    ashwin_savings = ashwin_inhand - ashwin_spend
    harshita_savings = harshita_inhand - harshita_spend

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Ashwin</div>
            <div class="caption">In Hand</div>
            <div class="big-number">₹{ashwin_inhand:,.0f}</div>
            <div class="caption">Spent</div>
            <div>₹{ashwin_spend:,.0f}</div>
            <div class="caption">Savings</div>
            <div>₹{ashwin_savings:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Harshita</div>
            <div class="caption">In Hand</div>
            <div class="big-number">₹{harshita_inhand:,.0f}</div>
            <div class="caption">Spent</div>
            <div>₹{harshita_spend:,.0f}</div>
            <div class="caption">Savings</div>
            <div>₹{harshita_savings:,.0f}</div>
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

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------
    # CATEGORY CHART (FIXED)
    # -----------------------
    cat = monthly_df.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        total = cat["amount"].sum()
        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(
            lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
        )

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(textposition="outside", textfont=dict(size=14, color="white"))
        fig.update_layout(
            yaxis=dict(visible=False),
            plot_bgcolor="#0a0a0c",
            paper_bgcolor="#0a0a0c",
            font=dict(color="white")
        )

        st.plotly_chart(fig, use_container_width=True)

# =======================
# COMPARE
# =======================
elif menu == "Compare" and not df.empty:
    st.write("Compare unchanged ✅")
