import streamlit as st
import json
from datetime import datetime
import os

st.set_page_config(page_title="Feedback Collector", layout="centered")
st.title("Dynamic Feedback Collector")

# Path to your local JSON file
json_file_path = "./Feedback.json"

# Load data from disk or initialize empty
if os.path.exists(json_file_path):
    with open(json_file_path, "r") as f:
        data = json.load(f)
else:
    data = {}

ids = list(data.keys())
if not ids:
    st.warning("No data found in JSON file.")
else:
    selected_id = st.selectbox("Select ID to give feedback", ids)

    feedback_text = st.text_area("Enter your feedback")

    if st.button("Submit Feedback"):
        if feedback_text.strip():
            feedback_entry = {
                "text": feedback_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if "feedback" not in data[selected_id]:
                data[selected_id]["feedback"] = []
            data[selected_id]["feedback"].append(feedback_entry)

            # Save immediately to disk
            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=4)

            st.success("Feedback submitted and saved successfully!")
        else:
            st.warning("Feedback cannot be empty.")

    # Show all feedback for selected ID
    st.subheader(f"Feedback History for ID {selected_id}")
    if "feedback" in data[selected_id] and data[selected_id]["feedback"]:
        for idx, fb in enumerate(data[selected_id]["feedback"], 1):
            st.markdown(f"**{idx}.** _{fb['timestamp']}_ — {fb['text']}")
    else:
        st.write("No feedback available yet.")

    # Download updated JSON
    updated_json = json.dumps(data, indent=4)
    st.subheader("Download Updated JSON")
    st.download_button(
        label="Download JSON",
        data=updated_json,
        file_name="updated_feedback.json",
        mime="application/json"
    )

