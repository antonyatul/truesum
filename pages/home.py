"""S01 Upload."""
import streamlit as st

from truesum.core import io
from truesum.ui import components as ui
from truesum.ui import state
from truesum.ui.widgets import next_steps, table_config

s = state.get()
ui.hero("Truesum", "Your sales spreadsheet, explained in plain English.")

left, right = st.columns([3, 2], gap="large")
with left:
    st.header("Add your sales file")
    upload = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx"],
        key="upload",
        help="Up to 50 MB or 250,000 rows. Your file is read in memory for this visit only and never saved to disk.",
    )
    if upload is not None and upload.file_id != st.session_state.get("_loaded_file_id"):
        with st.spinner("Reading your file…"):
            try:
                df = io.read_table(upload.getvalue(), upload.name)
            except io.UploadError as err:
                kept = f" Your earlier file, {s.name}, is still loaded." if s.has_data else ""
                st.error(f"{err}{kept}")
            else:
                s.load(upload.name, df)
                st.session_state["_loaded_file_id"] = upload.file_id
                st.toast(f"Loaded {len(df):,} rows", icon=":material/check_circle:")

    st.caption("Handles up to 250,000 rows. A 200,000-row file cleans and analyses in about 2 seconds. "
               "Nothing is kept after you leave, so refreshing the page starts over.")
    st.caption("No file to hand?")
    if st.button("Try the sample sales data", key="load_sample", icon=":material/dataset:"):
        s.load("Sample sales (synthetic)", io.load_sample())
        st.session_state["_loaded_file_id"] = None
        st.toast("Loaded the sample data", icon=":material/check_circle:")

with right:
    st.header("What you get back")
    st.markdown(
        "- **The maths, checked**: rows where the numbers don't add up, flagged for you to judge\n"
        "- **Every sale rated** High, Medium or Low on profit, against your own data\n"
        "- **What stands out**, in sentences, not formulas\n"
        "- **Your answers back in Excel**, plus a report you can email or print"
    )

if s.has_data:
    st.divider()
    st.header(f"Preview · {s.name}")
    st.caption(f"{len(s.df):,} rows · {s.df.shape[1]} columns. First 20 rows shown.")
    st.dataframe(s.df.head(20), hide_index=True, use_container_width=True, column_config=table_config(s.df))

next_steps("pages/home.py")
