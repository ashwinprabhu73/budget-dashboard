st.markdown("""
<style>

/* APP BACKGROUND */
body {
    background-color: #0f0f10;
    color: #ffffff;
}

/* MAIN AREA */
.block-container {
    padding-top: 2rem;
}

/* TITLE */
h1 {
    color: #ffffff;
    font-weight: 600;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #000000;
    color: #cfcfcf;
}

/* CARDS */
.premium-card {
    background: #18181b;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #2a2a2e;
}

/* NUMBERS */
.big-number {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
}

/* LABELS */
.caption {
    font-size: 12px;
    color: #9ca3af;
    text-transform: uppercase;
}

/* IPO CARD (CRED STYLE GOLD ACCENT) */
.gold-card {
    background: #18181b;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #2a2a2e;
    position: relative;
}

/* GOLD LINE */
.gold-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, #d4af37, #f5d77a);
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}

/* IPO TEXT */
.gold-title {
    font-size: 13px;
    color: #d4af37;
    margin-bottom: 10px;
}

.gold-value {
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
}

/* CHART BG */
.js-plotly-plot {
    background: transparent !important;
}

/* REMOVE WHITE CHART BG */
.plot-container {
    background: transparent !important;
}

/* DIVIDER */
hr {
    border: none;
    height: 1px;
    background: #2a2a2e;
    margin: 25px 0;
}

</style>
""", unsafe_allow_html=True)
