import streamlit as st
import pandas as pd
import time

# Collector for rows
if "table_rows" not in st.session_state:
    st.session_state["table_rows"] = []

# Create a placeholder for the table
if "table_placeholder" not in st.session_state:
    st.session_state["table_placeholder"] = st.empty()

def dict_to_markdown(question, prompt, data, iter_count):
    # Append row
    if iter_count == 1:
        st.session_state["table_rows"].append([question, prompt, data["Answer"], data["Reason"]])
    else:
        st.session_state["table_rows"].append(["", prompt, data["Answer"], data["Reason"]])

    # Convert to DataFrame
    df = pd.DataFrame(
        st.session_state["table_rows"],
        columns=["Question", "Sub-Question (prompt)", "Answer", "Reason"]
    )
    df.index = df.index + 1
    df.index.name = "Sr No."
    st.session_state["table_placeholder"].table(df)



# Example usage (simulate separate calls)
dict_to_markdown("Main Question?", "SubQ1", {"Answer": "Ans1", "Reason": "Because..."}, 1)
time.sleep(2)
dict_to_markdown("Main Question?", "SubQ2", {"Answer": "Ans2", "Reason": "Logic..."}, 2)
time.sleep(2)
dict_to_markdown("Main Question2?", "SubQ1", {"Answer": "AnsX", "Reason": "Why..."}, 1)
time.sleep(2)
dict_to_markdown("Main Question2?", "SubQ2", {"Answer": "AnsY", "Reason": "Reasoning..."}, 2)
dict_to_markdown("Main Question2?", "SubQ2", {"Answer": "AnsY", "Reason": "Reasoning..."}, 3)
