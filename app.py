import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# Extract Sheet ID
# -----------------------
def extract_sheet_id(input_text):
    if "docs.google.com" in input_text:
        return input_text.split("/d/")[1].split("/")[0]
    return input_text

# -----------------------
# Load ALL Tabs (IMPORTANT CHANGE)
# -----------------------
def load_google_sheet_all_tabs(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    all_sheets = pd.read_excel(url, sheet_name=None)

    df_list = []

    for sheet_name, sheet_data in all_sheets.items():
        sheet_data["sheet_name"] = sheet_name
        df_list.append(sheet_data)

    df = pd.concat(df_list, ignore_index=True)

    df = df.rename(columns={
        "Date": "date",
        "Expense": "description",
        "Expns Category": "category",
        "Total cost": "amount",
        "Recurring Expense": "recurring"
    })

    df = df.fillna("")

    return df

# -----------------------
# UI
# -----------------------
st.set_page_config(layout="wide")
st.title("💰 Smart Budget Dashboard")

sheet_input = st.text_input("🔗 Paste Google Sheet URL or ID")

if sheet_input:
    sheet_id = extract_sheet_id(sheet_input)

    if st.button("🔄 Refresh Data"):
        st.rerun()

    df = load_google_sheet_all_tabs(sheet_id)

    if df.empty:
        st.warning("No data found")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        df["year"] = df["date"].dt.year
        df["month_num"] = df["date"].dt.month
        df["month"] = df["date"].dt.strftime("%B")

        df = df.sort_values("month_num")

        # Year selection
        years = sorted(df["year"].unique())
        selected_year = st.selectbox("📅 Select Year", years)

        year_df = df[df["year"] == selected_year]

        # Total + Avg
        yearly_total = year_df["amount"].sum()
        month_count = year_df["month_num"].nunique()
        avg_monthly = yearly_total / month_count if month_count else 0

        st.markdown("### 💰 Total Spend")
        st.success(f"₹{yearly_total:,.0f}")
        st.markdown(f"**Avg: ₹{avg_monthly:,.0f} / month**")

        # Month selection
        months = year_df.sort_values("month_num")["month"].unique()
        selected_month = st.selectbox("📊 Select Month", months)

        filtered = year_df[year_df["month"] == selected_month]

        # Chart
        st.subheader(f"📊 Category Breakdown - {selected_month}")

        cat = filtered.groupby("category")["amount"].sum().reset_index()
        cat = cat.sort_values(by="amount", ascending=False)

        if not cat.empty:
            cat["label"] = cat["amount"].apply(lambda x: f"₹{x:,.0f}")

            fig = px.bar(cat, x="category", y="amount", text="label")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=400, yaxis=dict(visible=False))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for this month")

        # Recurring
        st.subheader("🔁 Recurring Breakdown")

        rec = filtered[filtered["recurring"].str.lower() == "recurring"]

        if not rec.empty:
            rec_cat = rec.groupby("category")["amount"].sum().reset_index()
            rec_cat["label"] = rec_cat["amount"].apply(lambda x: f"₹{x:,.0f}")

            fig2 = px.bar(rec_cat, x="category", y="amount", text="label")
            fig2.update_traces(textposition="outside")
            fig2.update_layout(height=400, yaxis=dict(visible=False))

            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No recurring expenses")
