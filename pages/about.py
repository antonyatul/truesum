"""Privacy & about."""
import streamlit as st

from truesum.core import io

st.title("Privacy & about")

st.header("What happens to your file")
st.markdown(
    "- Your file is read **in memory, on the server**, for this visit only.\n"
    "- It is **never written to disk**, logged, or shared. When you close the tab or refresh, it's gone.\n"
    "- Nothing you upload is used to train anything.\n"
    "- Truesum adds no tracking or analytics of its own. The hosting provider (Streamlit Community Cloud) "
    "may set its own cookies and keep standard server logs, such as IP addresses, to run the service."
)
st.caption(f"Limits: {io.MAX_BYTES // (1024 * 1024)} MB and {io.MAX_ROWS:,} rows per file.")

st.header("How the numbers are worked out")
st.markdown(
    "- **Profit** = revenue − cost × quantity when cost is per unit, or revenue − cost when it's a row total. "
    "Rows with no cost get no profit; they are never treated as free.\n"
    "- **Tiers** compare each sale with the rest of your file: Low below the 25th percentile, "
    "High at or above the 75th, Medium in between.\n"
    "- **What stands out** and the **data checks** follow fixed rules you can read in the source code. "
    "No AI model is involved."
)

st.header("About")
st.markdown(
    "Truesum is a free demo built by **Atul Antony** (MSc IT with Data Analytics, University of the West "
    "of Scotland). It's open source; the code, tests and design notes are on GitHub."
)
st.caption("Not financial or accounting advice. Check important figures before acting on them.")
