import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -----------------------
# DB Setup
# -----------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    category TEXT,
    amount REAL,
    paid_by TEXT,
    paid_via TEXT,
    bank TEXT,
    status TEXT,
    notes TEXT,
    recurring TEXT
)
''')
conn.commit()

# -----------------------
# Category Icons
# -----------------------
CATEGORY_ICONS = {
    "Food": "🍔",
    "Rent": "🏠",
    "Travel": "✈️",
    "Shopping": "🛍️",
    "Bills": "💡",
    "Entertainment": "🎬"
}

def get_icon(category):
    return CATEGORY_ICONS.get(category, "💰")

# -----------------------
# Functions
# -----------------------
def insert_data(row):
    c.execute("""
        INSERT INTO expenses 
        (date, description, category, amount, paid_by, paid_via, bank, status, notes, recurring)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)
    conn.commit()

def load_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI Setup
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Upload File", "Add Entry"])

# -----------------------
# Upload Section
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload your budget file", type=["xlsx", "csv"])

    if file:
        df = pd.read_excel(file)

        df = df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount",
            "Paid by": "paid_by",
            "Paid Via": "paid_via",
            "Bank": "bank",
            "Status": "status",
            "Notes": "notes",
            "Recurring Expense": "recurring"
        })

        df = df.fillna("")

        for _, row in df.iterrows():
            insert_data([
                str(row.get("date", "")),
                str(row.get("description", "")),
                str(row.get("category", "")),
                float(row.get("amount", 0) or 0),
                str(row.get("paid_by", "")),
                str(row.get("paid_via", "")),
                str(row.get("bank", "")),
                str(row.get("status", "")),
                str(row.get("notes", "")),
                str(row.get("recurring", ""))
            ])

        st.success("✅ Data uploaded successfully!")

# -----------------------
# Add Entry Section
# -----------------------
elif menu == "Add Entry":
    st.subheader("➕ Add Expense / Income")

    date = st.date_input("Date", datetime.today())
    description = st.text_input("Description")
    category = st.text_input("Category")
    amount = st.number_input("Amount")
    paid_by = st.text_input("Paid By")
    paid_via = st.selectbox("Paid Via", ["UPI", "Card", "Cash", "Bank"])
    bank = st.text_input("Bank")
    status = st.selectbox("Status", ["Paid", "Pending"])
    notes = st.text_input("Notes")
    recurring = st.selectbox("Recurring", ["", "Recurring"])

    if st.button("Save Entry"):
        insert_data([
            str(date),
            description,
            category,
            amount,
            paid_by,
            paid_via,
            bank,
            status,
            notes,
            recurring
        ])
        st.success("✅ Entry added successfully!")

# -----------------------
# Dashboard Section
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

        # Extract time fields
        df["year"] = df["date"].dt.year
        df["month_num"] = df["date"].dt.month
        df["month"] = df["date"].dt.strftime("%B")

        # -----------------------
        # Filters
        # -----------------------
        st.subheader("📅 Filters")

        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("Select Year", years)

        months = df[df["year"] == selected_year]["month"].unique()
        selected_month = st.selectbox("Select Month", months)
        compare_month = st.selectbox("Compare With Month", months)

        # Filter data
        filtered_df = df[
            (df["year"] == selected_year) &
            (df["month"] == selected_month)
        ]

        compare_df = df[
            (df["year"] == selected_year) &
            (df["month"] == compare_month)
        ]

        # -----------------------
        # KPIs
        # -----------------------
        total_spend = filtered_df["amount"].sum()
        recurring_spend = filtered_df[
            filtered_df["recurring"].str.lower() == "recurring"
        ]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total_spend:,.0f}")
        col2.metric("Recurring Spend", f"₹{recurring_spend:,.0f}")

        # -----------------------
        # Category Breakdown
        # -----------------------
        st.subheader(f"📊 Category Breakdown - {selected_month}")

        cat1 = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=False)

        cat_display = cat1.copy()
        cat_display.index = [f"{get_icon(cat)} {cat}" for cat in cat_display.index]

        st.bar_chart(cat_display)

        # -----------------------
        # Comparison Chart
        # -----------------------
        st.subheader(f"⚖️ Comparison: {selected_month} vs {compare_month}")

        cat2 = compare_df.groupby("category")["amount"].sum()

        compare_table = pd.DataFrame({
            selected_month: cat1,
            compare_month: cat2
        }).fillna(0)

        st.bar_chart(compare_table)

        # -----------------------
        # Yearly Trend
        # -----------------------
        st.subheader("📈 Yearly Monthly Trend")

        yearly = df[df["year"] == selected_year].groupby("month_num")["amount"].sum()
        yearly.index = [pd.to_datetime(m, format='%m').strftime('%B') for m in yearly.index]

        st.line_chart(yearly)

        # -----------------------
        # Recurring Analysis
        # -----------------------
        st.subheader("🔁 Recurring Analysis")

        recurring_df = df[df["recurring"].str.lower() == "recurring"]

        if not recurring_df.empty:
            rec = recurring_df.groupby(["year", "month_num"])["amount"].sum().reset_index()
            rec["month"] = rec["month_num"].apply(lambda x: pd.to_datetime(str(x), format='%m').strftime('%B'))
            st.line_chart(rec.set_index("month")["amount"])

            rec_cat = recurring_df.groupby("category")["amount"].sum()
            st.bar_chart(rec_cat)
        else:
            st.info("No recurring expenses found.")

        # -----------------------
        # Insights
        # -----------------------
        st.subheader("🧠 Insights")

        if not cat1.empty:
            st.write(f"👉 Top category in {selected_month}: **{cat1.idxmax()}**")

        diff = total_spend - compare_df["amount"].sum()

        if compare_month != selected_month:
            if diff > 0:
                st.warning(f"⚠️ You spent ₹{diff:,.0f} more than {compare_month}")
            else:
                st.success(f"✅ You saved ₹{abs(diff):,.0f} compared to {compare_month}")import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# -----------------------
# DB Setup
# -----------------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    description TEXT,
    category TEXT,
    amount REAL,
    paid_by TEXT,
    paid_via TEXT,
    bank TEXT,
    status TEXT,
    notes TEXT,
    recurring TEXT
)
''')
conn.commit()

# -----------------------
# Category Icons
# -----------------------
CATEGORY_ICONS = {
    "Food": "🍔",
    "Rent": "🏠",
    "Travel": "✈️",
    "Shopping": "🛍️",
    "Bills": "💡",
    "Entertainment": "🎬"
}

def get_icon(category):
    return CATEGORY_ICONS.get(category, "💰")

# -----------------------
# Functions
# -----------------------
def insert_data(row):
    c.execute("""
        INSERT INTO expenses 
        (date, description, category, amount, paid_by, paid_via, bank, status, notes, recurring)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)
    conn.commit()

def load_data():
    return pd.read_sql("SELECT * FROM expenses", conn)

# -----------------------
# UI Setup
# -----------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Smart Budget Dashboard")

menu = st.sidebar.radio("Menu", ["Dashboard", "Upload File", "Add Entry"])

# -----------------------
# Upload Section
# -----------------------
if menu == "Upload File":
    file = st.file_uploader("Upload your budget file", type=["xlsx", "csv"])

    if file:
        df = pd.read_excel(file)

        df = df.rename(columns={
            "Date": "date",
            "Expense": "description",
            "Expns Category": "category",
            "Total cost": "amount",
            "Paid by": "paid_by",
            "Paid Via": "paid_via",
            "Bank": "bank",
            "Status": "status",
            "Notes": "notes",
            "Recurring Expense": "recurring"
        })

        df = df.fillna("")

        for _, row in df.iterrows():
            insert_data([
                str(row.get("date", "")),
                str(row.get("description", "")),
                str(row.get("category", "")),
                float(row.get("amount", 0) or 0),
                str(row.get("paid_by", "")),
                str(row.get("paid_via", "")),
                str(row.get("bank", "")),
                str(row.get("status", "")),
                str(row.get("notes", "")),
                str(row.get("recurring", ""))
            ])

        st.success("✅ Data uploaded successfully!")

# -----------------------
# Add Entry Section
# -----------------------
elif menu == "Add Entry":
    st.subheader("➕ Add Expense / Income")

    date = st.date_input("Date", datetime.today())
    description = st.text_input("Description")
    category = st.text_input("Category")
    amount = st.number_input("Amount")
    paid_by = st.text_input("Paid By")
    paid_via = st.selectbox("Paid Via", ["UPI", "Card", "Cash", "Bank"])
    bank = st.text_input("Bank")
    status = st.selectbox("Status", ["Paid", "Pending"])
    notes = st.text_input("Notes")
    recurring = st.selectbox("Recurring", ["", "Recurring"])

    if st.button("Save Entry"):
        insert_data([
            str(date),
            description,
            category,
            amount,
            paid_by,
            paid_via,
            bank,
            status,
            notes,
            recurring
        ])
        st.success("✅ Entry added successfully!")

# -----------------------
# Dashboard Section
# -----------------------
elif menu == "Dashboard":
    df = load_data()

    if df.empty:
        st.warning("No data available.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')

        # Extract time fields
        df["year"] = df["date"].dt.year
        df["month_num"] = df["date"].dt.month
        df["month"] = df["date"].dt.strftime("%B")

        # -----------------------
        # Filters
        # -----------------------
        st.subheader("📅 Filters")

        years = sorted(df["year"].dropna().unique())
        selected_year = st.selectbox("Select Year", years)

        months = df[df["year"] == selected_year]["month"].unique()
        selected_month = st.selectbox("Select Month", months)
        compare_month = st.selectbox("Compare With Month", months)

        # Filter data
        filtered_df = df[
            (df["year"] == selected_year) &
            (df["month"] == selected_month)
        ]

        compare_df = df[
            (df["year"] == selected_year) &
            (df["month"] == compare_month)
        ]

        # -----------------------
        # KPIs
        # -----------------------
        total_spend = filtered_df["amount"].sum()
        recurring_spend = filtered_df[
            filtered_df["recurring"].str.lower() == "recurring"
        ]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Spend", f"₹{total_spend:,.0f}")
        col2.metric("Recurring Spend", f"₹{recurring_spend:,.0f}")

        # -----------------------
        # Category Breakdown
        # -----------------------
        st.subheader(f"📊 Category Breakdown - {selected_month}")

        cat1 = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=False)

        cat_display = cat1.copy()
        cat_display.index = [f"{get_icon(cat)} {cat}" for cat in cat_display.index]

        st.bar_chart(cat_display)

        # -----------------------
        # Comparison Chart
        # -----------------------
        st.subheader(f"⚖️ Comparison: {selected_month} vs {compare_month}")

        cat2 = compare_df.groupby("category")["amount"].sum()

        compare_table = pd.DataFrame({
            selected_month: cat1,
            compare_month: cat2
        }).fillna(0)

        st.bar_chart(compare_table)

        # -----------------------
        # Yearly Trend
        # -----------------------
        st.subheader("📈 Yearly Monthly Trend")

        yearly = df[df["year"] == selected_year].groupby("month_num")["amount"].sum()
        yearly.index = [pd.to_datetime(m, format='%m').strftime('%B') for m in yearly.index]

        st.line_chart(yearly)

        # -----------------------
        # Recurring Analysis
        # -----------------------
        st.subheader("🔁 Recurring Analysis")

        recurring_df = df[df["recurring"].str.lower() == "recurring"]

        if not recurring_df.empty:
            rec = recurring_df.groupby(["year", "month_num"])["amount"].sum().reset_index()
            rec["month"] = rec["month_num"].apply(lambda x: pd.to_datetime(str(x), format='%m').strftime('%B'))
            st.line_chart(rec.set_index("month")["amount"])

            rec_cat = recurring_df.groupby("category")["amount"].sum()
            st.bar_chart(rec_cat)
        else:
            st.info("No recurring expenses found.")

        # -----------------------
        # Insights
        # -----------------------
        st.subheader("🧠 Insights")

        if not cat1.empty:
            st.write(f"👉 Top category in {selected_month}: **{cat1.idxmax()}**")

        diff = total_spend - compare_df["amount"].sum()

        if compare_month != selected_month:
            if diff > 0:
                st.warning(f"⚠️ You spent ₹{diff:,.0f} more than {compare_month}")
            else:
                st.success(f"✅ You saved ₹{abs(diff):,.0f} compared to {compare_month}")
