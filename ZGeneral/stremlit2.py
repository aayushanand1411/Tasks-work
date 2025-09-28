import streamlit as st
import pandas as pd
import json
import os
import uuid
import time

# ------------------------
# Config
# ------------------------
FEEDBACK_FILE = "D:\Virtual_Environment_11\27sep\feedback.json"

# Load existing feedback
if os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "r") as f:
        feedback_data = json.load(f)
else:
    feedback_data = {}

# Initialize session state
if "table_rows" not in st.session_state:
    st.session_state["table_rows"] = []

if "table_placeholder" not in st.session_state:
    st.session_state["table_placeholder"] = st.empty()

if "editing_row" not in st.session_state:
    st.session_state["editing_row"] = None  # tracks which row feedback is open

# ------------------------
# Functions
# ------------------------
def save_feedback_to_json(question, prompt, answer, reason, feedback_text):
    key = f"{question}||{prompt}||{answer}||{reason}"
    if key not in feedback_data:
        feedback_data[key] = []
    feedback_data[key].append(feedback_text)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_data, f, indent=4)

def render_table(show_srno=True):
    df = pd.DataFrame(st.session_state["table_rows"])
    if show_srno:
        df.index = df.index + 1
        df.index.name = "Sr No."
    st.session_state["table_placeholder"].table(df.reset_index(drop=False))

def add_row(question, prompt, answer, reason):
    st.session_state["table_rows"].append({
        "Question": question,
        "Sub-Question (prompt)": prompt,
        "Answer": answer,
        "Reason": reason,
        "Feedback": ""
    })

def handle_feedback(idx):
    row = st.session_state["table_rows"][idx]
    key = f"{row['Question']}||{row['Sub-Question (prompt)']}||{row['Answer']}||{row['Reason']}"

    # Text area for feedback
    feedback_text = st.text_area(
        f"Enter feedback for row {idx+1}", value="", key=f"feedback_{uuid.uuid4()}"
    )

    if st.button(f"Submit Feedback for row {idx+1}", key=f"submit_{uuid.uuid4()}"):
        save_feedback_to_json(row["Question"], row["Sub-Question (prompt)"], row["Answer"], row["Reason"], feedback_text)
        st.success(f"Feedback saved for row {idx+1}!")
        # Reset editing row so feedback disappears
        st.session_state["editing_row"] = None
        # Update the Feedback column to show latest feedback
        row["Feedback"] = feedback_text

# ------------------------
# UI
# ------------------------
st.title("Dynamic Table with Optional Feedback")

show_srno = st.checkbox("Show Sr No.", value=True)

# Example rows
if len(st.session_state["table_rows"]) == 0:
    add_row("Main Question?", "SubQ1", "Ans1", "Because...")
    add_row("Main Question?", "SubQ2", "Ans2", "Logic...")
    add_row("Main Question2?", "SubQ1", "AnsX", "Why...")
    add_row("Main Question2?", "SubQ2", "AnsY", "Reasoning...")

render_table(show_srno)

# Render buttons to add feedback
for idx, row in enumerate(st.session_state["table_rows"]):
    if st.button(f"Add Feedback for row {idx+1}", key=f"btn_{idx}"):
        st.session_state["editing_row"] = idx

# If a row is being edited, show the feedback text_area
if st.session_state["editing_row"] is not None:
    handle_feedback(st.session_state["editing_row"])
