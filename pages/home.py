"""S01 Upload."""
import streamlit as st

from smartlytics.core import io
from smartlytics.ui import components as ui
from smartlytics.ui import state
from smartlytics.ui.widgets import table_config

s = state.get()
ui.hero("Smartlytics", "Turn a sales spreadsheet into profit tiers, charts and a shareable report in minutes.")

left, right = st.columns([3, 2], gap="large")
with left:
    st.header("Start with your data")
    upload = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx"],
        key="upload",
        help="Up to 50 MB or 500,000 rows. Your file stays in this browser session and is never stored.",
    )
    if upload is not None and upload.file_id != st.session_state.get("_loaded_file_id"):
        with st.spinner("Reading your file…"):
            try:
                df = io.read_table(upload.getvalue(), upload.name)
            except io.UploadError as err:
                st.error(str(err))
            else:
                s.load(upload.name, df)
                st.session_state["_loaded_file_id"] = upload.file_id
                st.toast(f"Loaded {len(df):,} rows", icon=":material/check_circle:")

    st.caption("No file to hand?")
    if st.button("Try the sample sales data", key="load_sample", icon=":material/dataset:"):
        s.load("Sample sales (synthetic)", io.load_sample())
        st.session_state["_loaded_file_id"] = None
        st.toast("Loaded the sample data", icon=":material/check_circle:")

with right:
    st.header("What you get")
    st.markdown(
        "- **Clean data**: tidy headers, merged labels, duplicates removed, every step logged\n"
        "- **Profit tiers**: each sale rated High, Medium or Low against your own data\n"
        "- **Customers**: your biggest spenders and who comes back\n"
        "- **Charts and a report**: one HTML file you can email or print"
    )

if s.has_data:
    st.divider()
    st.header(f"Preview · {s.name}")
    st.caption(f"{len(s.df):,} rows · {s.df.shape[1]} columns. First 20 rows shown.")
    st.dataframe(s.df.head(20), hide_index=True, use_container_width=True, column_config=table_config(s.df))
    a, b, _ = st.columns([1, 1, 2])
    with a:
        st.page_link("pages/overview.py", label="Next: check and clean", icon=":material/arrow_forward:")
    with b:
        st.page_link("pages/sales.py", label="Skip to sales performance", icon=":material/trending_up:")
