import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# PREMIUM UI THEME
# -----------------------
st.set_page_config(layout="wide")

st.markdown("""
<style>

/* Background */
body {
    background-color: #f8f5f0;
}

/* Container spacing */
.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Headings */
h1, h2, h3 {
    font-family: Georgia, serif;
    color: #2c2c2c;
}

/* Premium cards */
.premium-card {
    background: linear-gradient(135deg, #fdfaf6, #f4efe6);
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #e6dccb;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}

/* Standard card */
.card {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #eee;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* Big number */
.big-number {
    font-size: 30px;
    font-weight: 600;
    color: #1f3d2b;
}

/* Caption */
.caption {
    font-size: 13px;
    color: #7a766f;
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: #e8e2d8;
    margin: 25px 0;
}

</style>
""", unsafe_allow_html=True)

st.title("💰 Smart Budget Dashboard")

# -----------------------
# Helpers
# -----------------------
def load_excel(file):
    sheets = pd.read_excel(file, sheet_name=None)
    return pd.concat(sheets.values(), ignore_index=True)

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

# -----------------------
# Upload
# -----------------------
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = preprocess(load_excel(file))

    # -----------------------
    # Year & Month Selection
    # -----------------------
    years = sorted(df["year"].unique())
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = df[df["year"] == selected_year]

    months = year_df.sort_values("month_num")["month"].unique()
    selected_month = st.selectbox("Select Month", months, index=len(months)-1)

    expense_df = year_df[year_df["category"].str.lower() != "ipo"]
    ipo_df = year_df[year_df["category"].str.lower() == "ipo"]

    yearly_total = expense_df["amount"].sum()
    monthly_total = expense_df[expense_df["month"] == selected_month]["amount"].sum()

    # -----------------------
    # PREMIUM HEADER CARDS
    # -----------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">Total Yearly Spend</div>
            <div class="big-number">₹{yearly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="premium-card">
            <div class="caption">{selected_month} Monthly Spend</div>
            <div class="big-number">₹{monthly_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------
    # IPO SECTION
    # -----------------------
    ipo_month = ipo_df[ipo_df["month"] == selected_month]

    st.markdown(f"""
    <div class="card">
        <div class="caption">IPO Summary</div><br>
        <b>Amount:</b> ₹{ipo_month['amount'].sum():,.0f} &nbsp;&nbsp;&nbsp;
        <b>Entries:</b> {len(ipo_month)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------
    # CATEGORY CHART
    # -----------------------
    st.markdown(f"### 📊 Category Breakdown - {selected_month}")

    filtered = expense_df[expense_df["month"] == selected_month]

    cat = filtered.groupby("category")["amount"].sum().reset_index()
    cat = cat.sort_values(by="amount", ascending=False)

    if not cat.empty:
        total = cat["amount"].sum()

        cat["percent"] = (cat["amount"] / total) * 100
        cat["label"] = cat.apply(
            lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
        )

        fig = px.bar(cat, x="category", y="amount", text="label")

        fig.update_traces(
            textposition="outside",
            textfont=dict(size=16)
        )

        fig.update_layout(
            height=420,
            yaxis=dict(visible=False),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Georgia", size=12)
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------
    # OTHERS DONUT
    # -----------------------
    others_data = filtered[filtered["category"].str.lower() == "others"]

    if not others_data.empty:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🔍 Others Breakdown")

        others_group = others_data.groupby("description")["amount"].sum().reset_index()

        total_others = others_group["amount"].sum()
        others_group["percent"] = (others_group["amount"] / total_others) * 100

        major = others_group[others_group["percent"] >= 1]
        minor = others_group[others_group["percent"] < 1]

        misc_total = minor["amount"].sum()

        if misc_total > 0:
            major = pd.concat([
                major,
                pd.DataFrame([{
                    "description": "Miscellaneous",
                    "amount": misc_total
                }])
            ])

        fig2 = px.pie(
            major,
            names="description",
            values="amount",
            hole=0.5
        )

        fig2.update_traces(
            textinfo="percent+label",
            textfont=dict(size=14)
        )

        fig2.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Georgia")
        )

        st.plotly_chart(fig2, use_container_width=True)
