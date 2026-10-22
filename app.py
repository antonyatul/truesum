"""Truesum entry point: streamlit run app.py"""
import streamlit as st

from truesum.ui import components as ui
from truesum.ui.widgets import sidebar_status

st.set_page_config(
    page_title="Truesum",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="auto",
)
ui.inject_theme()

pages = {
    "Data": [
        st.Page("pages/home.py", title="Upload", icon=":material/upload_file:", default=True),
        st.Page("pages/overview.py", title="Overview & clean", icon=":material/table_chart:"),
    ],
    "Analyse": [
        st.Page("pages/sales.py", title="Sales performance", icon=":material/trending_up:"),
        st.Page("pages/customers.py", title="Customers", icon=":material/groups:"),
        st.Page("pages/charts.py", title="Chart builder", icon=":material/bar_chart:"),
    ],
    "Share": [
        st.Page("pages/report.py", title="Report & export", icon=":material/description:"),
    ],
}

nav = st.navigation(pages)
sidebar_status()
nav.run()
