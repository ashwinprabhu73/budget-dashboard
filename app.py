if menu == "Dashboard" and not df.empty:

    years = sorted(df["year"].unique())
    year = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = df[df["year"] == year].copy()
    year_df["category"] = year_df["category"].astype(str).str.lower()

    months_df = year_df.sort_values("month_num")
    months = months_df["month"].unique()
    month = st.selectbox("Select Month", months, index=len(months)-1)

    # =========================
    # FIX: correct filtering
    # =========================
    expense_df = year_df[year_df["category"] != "ipo"]

    # =========================
    # YEARLY
    # =========================
    total_year = expense_df["amount"].sum()

    st.markdown(f"""
    <div class="block">
    <div class="label">Total Yearly Spend</div>
    <div class="gold value">₹{total_year:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # IPO (KEEP WORKING)
    # =========================
    ipo_year = year_df[year_df["category"] == "ipo"]

    from streamlit.components.v1 import html
    html(f"""
    <div style="background:#111827;padding:18px;border-radius:12px;border:1px solid #1f2937;margin-bottom:15px;">
        <div style="color:#d4af37;font-weight:bold;font-size:18px;">YEARLY IPO SUMMARY</div>

        <div style="display:flex;justify-content:space-between;margin-top:15px;">
            <div>
                <div style="color:#9ca3af;">Total Amount Utilised</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">
                    ₹{ipo_year['amount'].sum():,.0f}
                </div>
            </div>
            <div>
                <div style="color:#9ca3af;">Allotment Profit</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">₹0</div>
            </div>
        </div>

        <div style="display:flex;justify-content:space-between;margin-top:20px;">
            <div>
                <div style="color:#9ca3af;">Applied</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">
                    {len(ipo_year)}
                </div>
            </div>
            <div>
                <div style="color:#9ca3af;">Allotted</div>
                <div style="color:#d4af37;font-size:26px;font-weight:bold;">0</div>
            </div>
        </div>
    </div>
    """, height=220)

    # =========================
    # MONTHLY
    # =========================
    mdf = expense_df[expense_df["month"] == month]
    monthly_total = mdf["amount"].sum()

    st.markdown(f"""
    <div class="block">
    <div class="label">{month} Monthly Spend</div>
    <div class="gold value">₹{monthly_total:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FIX: INVESTMENT + SPEND LOGIC
    # =========================
    a_spend, h_spend = 0, 0
    a_inv_rec, h_inv_rec = 0, 0
    a_inv_lump, h_inv_lump = 0, 0

    rec_col = None
    for c in df.columns:
        if "recurring" in c.lower():
            rec_col = c
            break

    for _, r in mdf.iterrows():

        p = str(r.get("paid_by", "")).strip().lower()
        cat = str(r.get("category", "")).strip().lower()
        amt = r["amount"]

        rec_flag = str(r.get(rec_col, "")).strip().lower() if rec_col else ""

        if cat == "investment":

            if "recurring" in rec_flag:
                if p == "ashwin":
                    a_inv_rec += amt
                elif p == "harshita":
                    h_inv_rec += amt
                elif p == "us":
                    a_inv_rec += amt / 2
                    h_inv_rec += amt / 2
            else:
                if p == "ashwin":
                    a_inv_lump += amt
                elif p == "harshita":
                    h_inv_lump += amt
                elif p == "us":
                    a_inv_lump += amt / 2
                    h_inv_lump += amt / 2

        else:
            if p == "ashwin":
                a_spend += amt
            elif p == "harshita":
                h_spend += amt
            elif p == "us":
                a_spend += amt / 2
                h_spend += amt / 2

    # =========================
    # IN HAND
    # =========================
    cols = df.columns
    a_col = find_inhand(cols, "ashwin")
    h_col = find_inhand(cols, "harshita")

    a_in = year_df[a_col].dropna().iloc[-1] if a_col and not year_df[a_col].dropna().empty else 0
    h_in = year_df[h_col].dropna().iloc[-1] if h_col and not year_df[h_col].dropna().empty else 0

    a_save = a_in - a_inv_rec - a_spend
    h_save = h_in - h_inv_rec - h_spend

    # =========================
    # PERSON CARDS (UNCHANGED UI)
    # =========================
    col1, col2 = st.columns(2)

    def render_person(name, income, inv_rec, inv_lump, spend, save, col):
        with col:
            html_block = f"""<div class="block">
<div class="gold">{name}</div>

<div class="label">In Hand</div>
<div class="gold value">₹{income:,.0f}</div>

<div class="label">Investment</div>
<div class="gold value">₹{inv_rec:,.0f}</div>

<div class="label">LumpSum Investment</div>
<div class="gold value">₹{inv_lump:,.0f}</div>

<div class="label">Spent</div>
<div class="gold value">₹{spend:,.0f}</div>

<div class="label">Savings</div>
"""
            if save >= 0:
                html_block += f"<div class='green value'>₹{save:,.0f}</div>"
            else:
                html_block += f"<div class='red value'>-₹{abs(save):,.0f}</div>"

            html_block += "</div>"
            st.markdown(html_block, unsafe_allow_html=True)

    render_person("Ashwin", a_in, a_inv_rec, a_inv_lump, a_spend, a_save, col1)
    render_person("Harshita", h_in, h_inv_rec, h_inv_lump, h_spend, h_save, col2)

    # =========================
    # EXPENSE BREAKDOWN (FIXED)
    # =========================
    st.markdown("<h3 style='color:#d4af37;'>Expense Breakdown</h3>", unsafe_allow_html=True)

    cat = mdf.groupby("category")["amount"].sum().reset_index()

    if not cat.empty:
        fig = px.bar(cat, x="category", y="amount", text="amount")

        fig.update_traces(
            marker_color="#d4af37",
            textposition="outside",
            textfont=dict(color="white")
        )

        fig.update_layout(
            plot_bgcolor="#0b0f14",
            paper_bgcolor="#0b0f14",
            yaxis=dict(showgrid=False, showticklabels=False),
            xaxis=dict(title=None, tickfont=dict(color="#cbd5e1")),
            font=dict(color="white")
        )

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # OTHER EXPENSES (FIXED)
    # =========================
    others = mdf[mdf["category"] == "others"]

    if not others.empty:

        st.markdown("<h3 style='color:#1e3a8a;'>Other Expenses</h3>", unsafe_allow_html=True)

        grp = others.groupby("description")["amount"].sum().reset_index()

        fig = go.Figure(data=[go.Pie(
            labels=grp["description"],
            values=grp["amount"],
            hole=0.6
        )])

        st.plotly_chart(fig, use_container_width=True)
