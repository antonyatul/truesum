"""Customers: top spenders and repeat buyers (split out of the Hub's dashboard, fixes B5)."""
import streamlit as st

from smartlytics.core import customers, io, profile
from smartlytics.ui import components as ui
from smartlytics.ui.widgets import money, require_data

s = require_data()
df = s.result.df if s.result is not None else s.df
st.title("Customers")

cats = profile.columns_of(df, "category")
nums = [c for c in profile.columns_of(df, "numeric")]
if not cats:
    ui.empty_state("No customer column found", "This page needs a column that identifies customers, such as an ID or name.")
    st.stop()

m = s.mapping
cust_default = m.customer if m and m.customer in cats else next((c for c in cats if "cust" in c.lower()), cats[0])
a, b, c = st.columns(3)
customer = a.selectbox("Customer column", cats, index=cats.index(cust_default), key="cust_col")
if nums:
    amount_options = (["profit"] if "profit" in nums else []) + [n for n in nums if n != "profit"]
    amount_default = m.revenue if m and m.revenue in amount_options else amount_options[0]
    amount = b.selectbox("Amount column", amount_options, index=amount_options.index(amount_default), key="cust_amount")
else:
    amount = None
n = c.slider("How many to show", 5, 50, 10, step=5, key="cust_n")

table, stats = customers.repeat_customers(df, customer)
k = st.columns(4)
with k[0]:
    ui.metric("Customers", f"{stats['customers']:,}")
with k[1]:
    ui.metric("Came back", f"{stats['repeat_pct']:.1f}%", f"{stats['repeat_customers']:,} customers")
with k[2]:
    ui.metric("Orders from returners", f"{stats['orders_from_repeat_pct']:.1f}%")
with k[3]:
    ui.metric("Orders per customer", f"{len(df) / max(stats['customers'], 1):.1f}", "average")

left, right = st.columns(2, gap="large")
with left:
    st.header("Top customers")
    if amount is None:
        ui.empty_state("No amount column", "Top customers need a column with numbers, such as revenue.")
    else:
        top = customers.top_customers(df, customer, amount, n)
        st.dataframe(top, hide_index=True, use_container_width=True, column_config={
            "total": st.column_config.NumberColumn(f"total {amount}", format="%,.2f"),
            "orders": st.column_config.NumberColumn(format="localized"),
            "share_pct": st.column_config.NumberColumn("share of all", format="%.2f%%")})
        if len(top):
            st.caption(f"Your best customer, {top.iloc[0]['customer']}, accounts for {money(top.iloc[0]['total'])} "
                       f"({top.iloc[0]['share_pct']:.2f}% of all {amount}).")
with right:
    st.header("Repeat customers")
    if table.empty:
        ui.empty_state("No repeat customers", "Every customer appears only once in this data.")
    else:
        st.dataframe(table.head(n), hide_index=True, use_container_width=True)
        st.download_button("Download all repeat customers (CSV)", lambda: io.to_csv_bytes(table), "repeat_customers.csv",
                           mime="text/csv", key="dl_repeat", icon=":material/download:")
