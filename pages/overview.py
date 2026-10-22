"""S02 Overview & clean (includes the plain-English summary, formerly S03 'AI insights')."""
import pandas as pd
import streamlit as st

from smartlytics.core import checks, cleaning, io, profile, sales
from smartlytics.ui import components as ui
from smartlytics.ui.widgets import next_steps, require_data, table_config

s = require_data()
df = s.df
st.title("Overview & clean")
st.caption(f"{s.name} · {'cleaned' if s.cleaned else 'original data, not cleaned yet'}")

ov = profile.overview(df)
c = st.columns(4)
with c[0]:
    ui.metric("Rows", f"{ov['rows']:,}")
with c[1]:
    ui.metric("Columns", f"{ov['columns']}")
with c[2]:
    ui.metric("Missing cells", f"{ov['missing_pct']:.1f}%", f"{ov['missing_cells']:,} cells")
with c[3]:
    ui.metric("Duplicate rows", f"{ov['duplicate_rows']:,}")

# ---- cleaning ---------------------------------------------------------------
st.header("Clean")
left, right = st.columns([3, 2], gap="large")
with left:
    st.write(
        "The recommended clean tidies headers, trims stray spaces, merges labels that only differ "
        "by capitals, turns number-like text into numbers, reads dates, removes exact duplicates and "
        "labels missing text as *Unknown*. Missing numbers are left blank on purpose, so a missing "
        "cost is never treated as free."
    )
    b1, b2 = st.columns(2)
    if b1.button("Clean with recommended settings", type="primary", key="clean_recommended",
                 icon=":material/auto_fix_high:", disabled=s.cleaned, use_container_width=True):
        with st.spinner("Cleaning…"):
            new_df, entries = cleaning.clean_recommended(df)
        s.replace_data(new_df, entries)
        st.rerun()
    if b2.button("Undo all cleaning", key="reset", icon=":material/undo:",
                 disabled=not s.audit, use_container_width=True):
        s.reset_to_original()
        st.toast("Back to the original upload", icon=":material/undo:")
        st.rerun()
    if s.cleaned:
        st.success("Recommended clean applied. Fine-tune below if you need to.")

with right:
    st.markdown("**Steps so far**")
    ui.step_list([(e.message, e.meta()) for e in s.audit])

with st.expander("Fine-tune: missing values and negative rows", icon=":material/tune:"):
    miss = profile.missing(df)
    miss = miss[miss["missing"] > 0]
    types = profile.column_types(df)
    if miss.empty:
        st.info("No missing values left.")
    else:
        st.write("Choose what happens to each column with gaps.")
        options = {"numeric": ["leave", "drop_rows", "median", "mean", "mode", "zero"],
                   "date": ["leave", "drop_rows"],
                   "category": ["leave", "drop_rows", "unknown", "mode"]}
        plan = {}
        for _, row in miss.iterrows():
            col = row["column"]
            kind = types[col]
            plan[col] = st.selectbox(
                f"{col} · {int(row['missing']):,} missing ({row['missing_pct']:.1f}%)",
                options[kind], key=f"fill_{col}",
                format_func=lambda m: {"leave": "Leave blank", "drop_rows": "Remove these rows",
                                       "median": "Fill with median", "mean": "Fill with average",
                                       "mode": "Fill with most common", "zero": "Fill with 0",
                                       "unknown": "Fill with 'Unknown'"}[m],
            )
            if kind == "numeric" and plan[col] == "zero" and "cost" in col.lower():
                st.warning(f"Filling '{col}' with 0 makes those items look free and inflates profit.")
        if st.button("Apply missing-value choices", key="apply_fill"):
            new_df, entry = cleaning.fill_missing(df, plan)
            s.replace_data(new_df, [entry])
            st.rerun()

    st.divider()
    num_cols = profile.columns_of(df, "numeric")
    neg = st.multiselect("Remove rows with negative values in", num_cols, key="neg_cols",
                         help="Negative revenue is often a refund. Keep those rows if refunds should count.")
    if st.button("Remove negative rows", key="apply_neg", disabled=not neg):
        new_df, entry = cleaning.drop_negative(df, neg)
        s.replace_data(new_df, [entry])
        st.rerun()

# ---- data checks ------------------------------------------------------------
st.header("Check the maths")
mapping = s.mapping or sales.guess_mapping(df)
if not mapping.revenue:
    st.caption("Data checks need a numeric revenue column. Clean the data or set columns on the Sales page.")
else:
    found = checks.run_checks(df, mapping)
    problems = [c for c in found if not c.passed]
    if not found:
        st.caption("No columns here that the checks know how to test.")
    elif not problems:
        st.success(f"All {len(found)} checks passed.", icon=":material/verified:")
    else:
        st.write(f"{len(problems)} of {len(found)} checks found rows worth a look. Nothing has been changed; "
                 "these are for you to judge.")
    if found:
        st.dataframe(checks.summary(found), hide_index=True, use_container_width=True, column_config={
            "rows flagged": st.column_config.NumberColumn(format="localized"),
            "rows checked": st.column_config.NumberColumn(format="localized")})
        if problems:
            flagged = pd.concat([c.rows.assign(failed_check=c.name) for c in problems], ignore_index=True)
            st.download_button("Download flagged rows (CSV)", lambda: io.to_csv_bytes(flagged), "flagged_rows.csv",
                               mime="text/csv", key="dl_flagged", icon=":material/download:")

# ---- explore ----------------------------------------------------------------
st.header("Explore")
t1, t2, t3, t4, t5 = st.tabs(["Summary", "Number columns", "Text and date columns", "Missing values", "Data"])
with t1:
    for line in profile.text_summary(df):
        st.markdown(f"- {line}")
    st.caption("Generated from simple rules about your data, not by an AI model.")
with t2:
    stats = profile.numeric_stats(df)
    if stats.empty:
        ui.empty_state("No number columns", "Cleaning may convert number-like text into numbers.")
    else:
        st.dataframe(stats, use_container_width=True, column_config={
            **{c: st.column_config.NumberColumn(format="%,.2f") for c in stats.columns},
            "count": st.column_config.NumberColumn(format="localized")})
with t3:
    cats = profile.category_stats(df)
    if cats.empty:
        ui.empty_state("No text or date columns", "Every column here holds numbers.")
    else:
        st.dataframe(cats, hide_index=True, use_container_width=True)
with t4:
    m = profile.missing(df)
    st.dataframe(m, hide_index=True, use_container_width=True, column_config={
        "missing_pct": st.column_config.ProgressColumn("missing %", min_value=0, max_value=100, format="%.1f%%")})
with t5:
    st.caption(f"Showing the first 1,000 of {len(df):,} rows.")
    st.dataframe(df.head(1000), hide_index=True, use_container_width=True, column_config=table_config(df))
    dtypes = pd.DataFrame({"column": df.columns, "read as": [profile.column_types(df)[c] for c in df.columns]})
    st.dataframe(dtypes, hide_index=True)

next_steps("pages/overview.py")
