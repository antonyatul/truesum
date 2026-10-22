"""S07 Sales performance: column mapping, profit, tiers, top performers."""
import streamlit as st

from smartlytics.core import charts, findings, io, profile, sales
from smartlytics.ui import components as ui
from smartlytics.ui.widgets import chart_style, money, next_steps, require_data, show_chart, table_config

s = require_data()
df = s.df
st.title("Sales performance")

if not s.cleaned:
    st.info("Tip: run the recommended clean on the Overview page first, so numbers and dates are read correctly.",
            icon=":material/lightbulb:")

# ---- mapping ----------------------------------------------------------------
guess = s.mapping or sales.guess_mapping(df)
numeric = profile.columns_of(df, "numeric")
everything = list(df.columns)
NONE = "— none —"


def pick(label: str, options: list[str], current: str | None, key: str, help_text: str, optional: bool = True) -> str | None:
    opts = ([NONE] if optional else []) + options
    index = opts.index(current) if current in opts else 0
    choice = st.selectbox(label, opts, index=index, key=key, help=help_text,
                          placeholder="No suitable columns" if not opts else None)
    return None if choice in (NONE, None) else choice


with st.expander("Which columns are which?", expanded=s.result is None, icon=":material/link:"):
    if not numeric:
        ui.empty_state("No number columns found", "Clean the data first so amounts are read as numbers.")
        st.stop()
    with st.form("mapping"):
        st.caption("We've guessed from your headers. Check them, then run the analysis.")
        a, b, c = st.columns(3)
        with a:
            revenue = pick("Revenue (sale amount)", numeric, guess.revenue, "map_revenue",
                           "What the customer paid for the row, after discounts.", optional=False)
            date = pick("Date", everything, guess.date, "map_date", "Optional. Used for trends.")
        with b:
            cost = pick("Cost", numeric, guess.cost, "map_cost",
                        "Optional, but needed for profit. Without it, rows are rated on revenue.")
            customer = pick("Customer", everything, guess.customer, "map_customer", "Optional. Used on the Customers page.")
        with c:
            quantity = pick("Quantity", numeric, guess.quantity, "map_quantity", "Needed when cost is per unit.")
            product = pick("Product", everything, guess.product, "map_product", "Optional. Used for breakdowns.")
        per_unit = st.toggle("Cost is per unit (multiply by quantity)", value=guess.cost_is_per_unit, key="map_per_unit",
                             help="Turn off if the cost column is already the total cost for the row.")
        submitted = st.form_submit_button("Run analysis", type="primary", icon=":material/play_arrow:")

    if submitted:
        mapping = sales.SalesMapping(revenue=revenue, cost=cost, quantity=quantity, cost_is_per_unit=per_unit,
                                     date=date, customer=customer, product=product)
        problems = sales.validate_mapping(df, mapping)
        if problems:
            for p in problems:
                st.error(p)
        else:
            s.mapping = mapping
            s.result = sales.analyse(df, mapping)
            st.rerun()

r = s.result
if r is None:
    ui.empty_state("No analysis yet", "Check the column choices above and press Run analysis.")
    next_steps("pages/sales.py")
    st.stop()

# ---- results ----------------------------------------------------------------
t = r.totals
cards = st.columns(4)
with cards[0]:
    ui.metric("Revenue", money(t["revenue"]), f"{int(t['rows']):,} rows")
if r.metric == "profit":
    with cards[1]:
        ui.metric("Profit", money(t["profit"]), f"{int(t['loss_rows']):,} rows made a loss")
    with cards[2]:
        ui.metric("Margin", f"{t['margin_pct']:.1f}%", "profit ÷ revenue, rows with a cost")
else:
    with cards[1]:
        ui.metric("Profit", "—", "Map a cost column to see profit")
    with cards[2]:
        ui.metric("Margin", "—", "Needs a cost column")
with cards[3]:
    ui.metric("Not rated", f"{int(t['unrated_rows']):,}", "rows with no value to rate")

facts = findings.findings(r)
if facts:
    with st.container(border=True):
        st.markdown("**What stands out**")
        st.markdown("\n".join(f"- {f}" for f in facts))
        st.caption("Worked out from your data with fixed rules, not guessed by AI.")

for w in r.warnings:
    st.warning(w, icon=":material/info:")

st.header("Performance tiers")
label = r.metric.replace("_", " ")
st.markdown(
    f"Every row is rated on **{label}** against the rest of your data: "
    f"{ui.tier_badge('Low')} below {money(r.thresholds.q25)}, "
    f"{ui.tier_badge('Medium')} in between, {ui.tier_badge('High')} at {money(r.thresholds.q75)} or more.",
    unsafe_allow_html=True,
)
style = chart_style()
show_chart(charts.profit_thresholds(r, style), "thresholds",
           caption=f"Low/Medium boundary {money(r.thresholds.q25)}, average {money(r.thresholds.mean)}, "
                   f"Medium/High boundary {money(r.thresholds.q75)}.")

left, right = st.columns(2, gap="large")
with left:
    st.markdown("**Rows and money per tier**")
    summary = sales.tier_summary(r)
    st.dataframe(summary, hide_index=True, use_container_width=True, column_config={
        **table_config(summary), "rows": st.column_config.NumberColumn(format="localized"),
        "share_of_rows_pct": st.column_config.NumberColumn("share of rows", format="%.1f%%")})
with right:
    st.markdown("**Tier boundaries**")
    st.dataframe(sales.threshold_table(r.thresholds), hide_index=True, use_container_width=True,
                 column_config={"value": st.column_config.NumberColumn(format="%,.2f")})
    st.caption(f"{r.thresholds.rated_rows:,} rows rated.")

if r.metric == "profit":
    show_chart(charts.sales_vs_profit(r, style), "sales_vs_profit")

st.header("Where the money comes from")
dims = [c for c in profile.columns_of(r.df, "category") if c != "tier" and r.df[c].nunique() <= 200]
if dims:
    default = r.mapping.product if r.mapping.product in dims else dims[0]
    by = st.selectbox("Break down by", dims, index=dims.index(default), key="breakdown_by")
    data = sales.breakdown(r, by)
    value = "profit" if r.metric == "profit" else r.mapping.revenue
    show_chart(charts.breakdown_bar(data, by, value, style), f"breakdown_{by}")
else:
    st.caption("No text columns with 200 or fewer values to break down by.")

st.header("Top performers")
top = sales.top_performers(r)
st.caption(f"{len(top):,} High-tier rows, best first. Showing up to 500.")
show = top.head(500).copy()
st.dataframe(show, hide_index=True, use_container_width=True, column_config=table_config(show))
st.download_button("Download top performers (CSV)", lambda: io.to_csv_bytes(top), "top_performers.csv",
                   mime="text/csv", key="dl_top", icon=":material/download:")
next_steps("pages/sales.py")
