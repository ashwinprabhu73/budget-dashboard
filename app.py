# -----------------------
# CATEGORY COMPARISON (CLEAN 🔥)
# -----------------------
st.markdown("### 📊 Category Comparison (Top 10)")

cat1 = df1.groupby("category")["amount"].sum()
cat2 = df2.groupby("category")["amount"].sum()

compare = pd.DataFrame({
    f"{m1}-{y1}": cat1,
    f"{m2}-{y2}": cat2
}).fillna(0)

# Top 10 categories
compare["total"] = compare.sum(axis=1)
compare = compare.sort_values(by="total", ascending=False).head(10)
compare = compare.drop(columns=["total"]).reset_index()

# Totals for %
total1 = df1["amount"].sum()
total2 = df2["amount"].sum()

# Add %
compare[f"{m1}-{y1}_pct"] = (compare[f"{m1}-{y1}"] / total1) * 100
compare[f"{m2}-{y2}_pct"] = (compare[f"{m2}-{y2}"] / total2) * 100

# Melt properly
melted = pd.DataFrame()

for month in [f"{m1}-{y1}", f"{m2}-{y2}"]:
    temp = compare[["category", month, f"{month}_pct"]].copy()
    temp.columns = ["category", "amount", "percent"]
    temp["Month"] = month
    melted = pd.concat([melted, temp])

# Label
melted["label"] = melted.apply(
    lambda x: f"₹{x['amount']:,.0f} ({x['percent']:.1f}%)", axis=1
)

# -----------------------
# SPLIT BY CATEGORY (CORRECT WAY 🔥)
# -----------------------
categories = compare["category"].tolist()

first5_cat = categories[:5]
next5_cat = categories[5:]

first5 = melted[melted["category"].isin(first5_cat)]
next5 = melted[melted["category"].isin(next5_cat)]

# -----------------------
# CHART 1
# -----------------------
fig1 = px.bar(
    first5,
    x="category",
    y="amount",
    color="Month",
    barmode="group",
    text="label"
)

fig1.update_traces(
    textposition="outside",
    textfont=dict(size=14)  # 🔥 Bigger font
)

fig1.update_layout(
    height=450,
    yaxis=dict(visible=False),
    xaxis_title=""
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------
# CHART 2
# -----------------------
if not next5.empty:
    fig2 = px.bar(
        next5,
        x="category",
        y="amount",
        color="Month",
        barmode="group",
        text="label"
    )

    fig2.update_traces(
        textposition="outside",
        textfont=dict(size=14)  # 🔥 Bigger font
    )

    fig2.update_layout(
        height=450,
        yaxis=dict(visible=False),
        xaxis_title=""
    )

    st.plotly_chart(fig2, use_container_width=True)
