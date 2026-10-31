"""
Confidential data, analysed offline: the whole method on 1 page.

Start it with start-windows.bat or start-mac.command (or: streamlit run app.py).
It opens in the browser, but it runs on this computer: the file you choose is
read here and never sent anywhere.
"""
import io
from pathlib import Path

import pandas as pd
import streamlit as st

import anonymize as an
import report

HERE = Path(__file__).parent
SAMPLE = HERE / "sample" / "time_entries_2027-01.xlsx"

st.set_page_config(page_title="Confidential data, analysed offline", page_icon="🔒", layout="wide")

# ---------------------------------------------------------------- the top
st.title("🔒 Confidential data, analysed offline")
st.success("**This page runs on your own computer.** The file you choose is read here and is not uploaded "
           "anywhere. To check, switch off Wi-Fi: everything below still works.")
st.markdown(
    "A confidential file cannot go into a chatbot, but the chatbot is the fastest way to get a script written. "
    "So the AI gets **an anonymized sample** and a description of the task, writes the script, "
    "and the script runs **here, on the real file**. 3 steps:"
)
c1, c2, c3 = st.columns(3)
c1.info("**1 · Choose the file**  \nThe real one stays on this computer.")
c2.info("**2 · Decide what the AI may see**  \nNames, case numbers and texts are replaced; you check every column.")
c3.info("**3 · Run the analysis here**  \nThe script the AI wrote, on the real file, offline.")

# ---------------------------------------------------------------- step 1
st.header("1 · Choose the file")
source = st.radio("Which file?", ["The sample file (fictional law firm, January 2027)", "My own Excel file"],
                  horizontal=True, label_visibility="collapsed")
if source.startswith("My own"):
    up = st.file_uploader("Choose an .xlsx file. It is read on this computer only.", type=["xlsx"])
    if up is None:
        st.stop()
    data = io.BytesIO(up.getvalue())
else:
    data = SAMPLE

first, df, others = an.read_workbook(data)
st.write(f"Read: **{len(df)} rows**, **{len(df.columns)} columns** on the sheet “{first}”"
         + (f", plus {len(others)} more sheet(s): " + ", ".join(f"“{k}”" for k in others) if others else "") + ".")

# ---------------------------------------------------------------- step 2
st.header("2 · Decide what the AI may see")
st.markdown("For every column the app has made a guess. **Check each line**, and change it where the guess is wrong: "
            "you know which columns are confidential, the app only guesses.")

plan = an.guess_plan(df)
choices = list(an.KINDS.values())
table = pd.DataFrame({
    "Column": list(df.columns),
    "Example from your file": [
        (f"{df[c].dropna().iloc[0]:%d.%m.%Y}" if pd.api.types.is_datetime64_any_dtype(df[c]) else str(df[c].dropna().iloc[0]))
        if df[c].notna().any() else "" for c in df.columns],
    "What to do with it": [an.KINDS[plan[c]] for c in df.columns],
})
edited = st.data_editor(
    table, hide_index=True, width="stretch", height=36 * (len(table) + 1) + 4, disabled=["Column", "Example from your file"],
    column_config={"What to do with it": st.column_config.SelectboxColumn(options=choices, required=True, width="large")},
)
back = {v: k for k, v in an.KINDS.items()}
plan = {r["Column"]: back[r["What to do with it"]] for _, r in edited.iterrows()}

sample, mapping = an.anonymize(df, plan)


def shown(frame):
    """Dates without the 00:00:00, for the eye only."""
    frame = frame.copy()
    for c in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[c]):
            frame[c] = frame[c].dt.strftime("%d.%m.%Y")
    return frame


left, right = st.columns(2)
with left:
    st.subheader("Your file · stays here")
    st.dataframe(shown(df.head(6)), hide_index=True, width="stretch")
with right:
    st.subheader("What the AI will see")
    st.dataframe(shown(sample.head(6)), hide_index=True, width="stretch")

buf = io.BytesIO()
sample.to_excel(buf, index=False, engine="openpyxl")
structure = an.describe(df, sample, plan, others)
prompt = (HERE / "PROMPT.md").read_text(encoding="utf-8").split("```text")[1].split("```")[0].strip()
prompt = prompt.replace("{STRUCTURE}", structure).replace("{ROWS}", str(len(df)))

st.markdown("**Give these 2 things to the AI** (ChatGPT, Claude or any other): the anonymized sample and the task.")
d1, d2 = st.columns([1, 3])
with d1:
    st.download_button("⬇️ Download the sample for the AI", buf.getvalue(), "sample_for_ai.xlsx", width="stretch")
    with st.expander("Which label stands for whom (stays on this computer)"):
        st.dataframe(mapping, hide_index=True, width="stretch")
with d2:
    st.caption("The task, ready to copy (the copy icon is at the top right of the box):")
    st.code(prompt, language="markdown", wrap_lines=True)

# ---------------------------------------------------------------- step 3
st.header("3 · Run the analysis here")
st.markdown("The AI answered with a script. Here it is the one in **report.py**, written by an AI from exactly this "
            "sample and task; it never saw the real file. Now it runs on the real one, on this computer.")

if st.button("▶️ Run the report on the real file", type="primary"):
    st.session_state["result"] = report.build(df, others.get("Matters"))

result = st.session_state.get("result")
if result:
    s = result["summary"]
    m = st.columns(5)
    m[0].metric("Month", s["Month"])
    m[1].metric("Hours", f"{s['Hours']:,.1f}")
    m[2].metric("Amount, RUB", f"{s['Amount (RUB)']:,.0f}")
    m[3].metric("Matters", s["Matters"])
    m[4].metric("To check before billing", s["Entries to check"])

    st.subheader("⚠️ To check before the report goes to the client")
    st.dataframe(result["checks"], hide_index=True, width="stretch")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Hours by matter, against the cap")
        bm = result["by_matter"].set_index("Matter")
        cols = ["Hours"] + (["Monthly cap (hours)"] if "Monthly cap (hours)" in bm else [])
        st.bar_chart(bm[cols], stack=False, horizontal=True)
    with g2:
        st.subheader("Hours by lawyer")
        st.bar_chart(result["by_lawyer"].set_index("Lawyer")["Hours"], horizontal=True)

    out = io.BytesIO()
    report.save(result, out)
    st.download_button("⬇️ Download the report (.xlsx)", out.getvalue(), "report.xlsx", type="primary")

with st.expander("Show the script the AI wrote (report.py)"):
    st.code((HERE / "report.py").read_text(encoding="utf-8"), language="python")
with st.expander("Using a script your AI wrote for your own file"):
    st.markdown(
        "1. Save the AI's answer as a file next to this one, for example `my_report.py`.\n"
        "2. Open a terminal in this folder and run `python my_report.py \"path to your real file.xlsx\"`.\n"
        "3. Check the result against 2 or 3 numbers you know by heart before you trust the rest."
    )
