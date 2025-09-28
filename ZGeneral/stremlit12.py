import streamlit as st
import pandas as pd
import time

# Collector for rows
if "table_rows" not in st.session_state:
    st.session_state["table_rows"] = []

# Create a placeholder for the table
if "table_placeholder" not in st.session_state:
    st.session_state["table_placeholder"] = st.empty()

# Store feedback inputs separately
if "feedbacks" not in st.session_state:
    st.session_state["feedbacks"] = []

def dict_to_markdown(question, prompt, data, iter_count, show_srno=True):
    # Append new row if needed
    if iter_count == 1:
        st.session_state["table_rows"].append([question, prompt, data["Answer"], data["Reason"]])
    else:
        st.session_state["table_rows"].append(["", prompt, data["Answer"], data["Reason"]])

    # Ensure feedback list has same length
    while len(st.session_state["feedbacks"]) < len(st.session_state["table_rows"]):
        st.session_state["feedbacks"].append("")

    # Render feedback input for each row
    for i in range(len(st.session_state["table_rows"])):
        st.session_state["feedbacks"][i] = st.text_input(
            f"Feedback for row {i+1}", value=st.session_state["feedbacks"][i], key=f"feedback_{i}"
        )

    # Convert to DataFrame including feedback
    df = pd.DataFrame(
        [row + [fb] for row, fb in zip(st.session_state["table_rows"], st.session_state["feedbacks"])],
        columns=["Question", "Sub-Question (prompt)", "Answer", "Reason", "Feedback"]
    )

    if show_srno:
        df.index = df.index + 1
        df.index.name = "Sr No."
        st.session_state["table_placeholder"].table(df)
    else:
        st.session_state["table_placeholder"].table(df.reset_index(drop=True))


# Toggle to control Sr No. column
show_srno = True

# Example usage (simulate separate calls)
dict_to_markdown("Main Question?", "SubQ1", {"Answer": "Ans1", "Reason": "Because..."}, 1, show_srno)
time.sleep(1)
dict_to_markdown("Main Question?", "SubQ2", {"Answer": "Ans2", "Reason": "Logic..."}, 2, show_srno)
time.sleep(1)
dict_to_markdown("Main Question2?", "SubQ1", {"Answer": "AnsX", "Reason": "Why..."}, 1, show_srno)
time.sleep(1)
dict_to_markdown("Main Question2?", "SubQ2", {"Answer": "AnsY", "Reason": "Reasoning..."}, 2, show_srno)
