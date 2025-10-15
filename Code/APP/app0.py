import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import re
import json
from fuzzywuzzy import fuzz
import os
from rich import print as rich_print
from rich.markdown import Markdown
import requests
from datetime import datetime
from ZFinal_md_with_section3 import *

# Document types
DOC_TYPES = ["SRS", "SDD", "ICD"]


def add_question(doc_type, question, sub_questions, reference_section, special_instructions):
    """Add a new question to the data"""
    new_question = {
        "id": len(st.session_state.questions_data) + 1,
        "doc_type": doc_type,
        "question": question,
        "sub_questions": sub_questions,
        "reference_section": reference_section,
        "special_instructions": special_instructions,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.questions_data.append(new_question)
    save_to_local_storage()


def update_question(index, doc_type, question, sub_questions, reference_section, special_instructions):
    """Update an existing question"""
    if 0 <= index < len(st.session_state.questions_data):
        st.session_state.questions_data[index].update({
            "doc_type": doc_type,
            "question": question,
            "sub_questions": sub_questions,
            "reference_section": reference_section,
            "special_instructions": special_instructions,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_to_local_storage()
        return True
    return False


def delete_question(index):
    """Delete a question from the data"""
    if 0 <= index < len(st.session_state.questions_data):
        st.session_state.questions_data.pop(index)
        save_to_local_storage()
        # Reset edit mode if we're editing the deleted item
        if st.session_state.edit_index == index:
            reset_form()
        elif st.session_state.edit_index is not None and st.session_state.edit_index > index:
            # Adjust edit index if a question before the current edit was deleted
            st.session_state.edit_index -= 1
        return True
    return False


def reset_form():
    """Reset form to add mode"""
    st.session_state.edit_mode = False
    st.session_state.edit_index = None


DATA_FILE = "questions_data2.json"


def save_to_local_storage():
    """Save questions data to a local JSON file"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.questions_data, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save data: {e}")


def load_from_local_storage():
    """Load questions data from a local JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                st.session_state.questions_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to load existing data: {e}")
            st.session_state.questions_data = []


def dict_to_markdown3(question, data):
    # Create the header of the table
    markdown = "| Question | Sub-Question (prompt) | Answer |\n"
    markdown += "| --- | --- | --- |\n"

    # Add the main question row with empty sub-question and result
    # Iterate over each key-value pair in the dictionary
    iter = 1
    for key, value in data.items():
        # Add a new row to the table for each key-value pair
        if iter == 1:
            markdown += f"| {question} |{key} | {value} |\n"
            iter += 1
        else:
            markdown += f"|  | {key} | {value} |\n"

    return markdown


def dict_to_markdown4(question, prompt, data, iter_count):
    # Create the header of the table
    markdown = "| Question | Sub-Question (prompt) | Answer | Reason |\n"
    markdown += "| --- | --- | --- | --- |\n"
    # iter = 1

    # Add the main question row with empty sub-question and result
    # Iterate over each key-value pair in the dictionary

    # iter = 1
    if iter_count == 1:
        markdown += f"| {question} |{prompt} | {data['Answer']} | {data['Reason']} |\n"
    else:
        markdown += f"| | {prompt} | {data['Answer']} | {data['Reason']} |\n"

    return markdown


def dict_to_markdown5(question, Sub, data, iter_count,main_count):
    # Initialize an empty list to store DataFrames
    # Append row
    if iter_count == 1:
        temp = f"{question}\n {Sub}"
        st.session_state["table_rows"].append([main_count, question,iter_count,Sub, data['Answer'], data['Reason']])
    else:
        st.session_state["table_rows"].append(["","",iter_count,Sub, data['Answer'], data['Reason']])

    # Convert to DataFrame
    df = pd.DataFrame(
        st.session_state["table_rows"],
        columns=["Main No.", "Main Question","Sub no.", "Sub-Question", "Answer", "Reason"]
        #columns = ["Main No.", "Question", "Sub no.", "Sub-Question", "Answer", "Score"]
    )
    # df.index = df.index + 1
    # df.index.name = "Sr No."
    df["Main No."] = df["Main No."].apply(lambda x: f"<b>{x}</b>" if x != "" else "")
    html_table = df.to_html(index=False, escape=False)
    # Add CSS for custom column widths
    styled_html = f"""
    <div>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', sans-serif;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px 10px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
            }}
            /* Column widths */
            th:nth-child(1), td:nth-child(1) {{ width: 10%; text-align: center; }}
            th:nth-child(2), td:nth-child(2) {{ width: 20%; }}
            th:nth-child(3), td:nth-child(3) {{ width: 10%; text-align: center; }}
            th:nth-child(4), td:nth-child(4) {{ width: 20%; }}
            th:nth-child(5), td:nth-child(5) {{ width: 10%; text-align: center; }}
            th:nth-child(6), td:nth-child(6) {{ width: 30%; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
        </style>
        {html_table}
        <div>
        """
    st.session_state["table_placeholder"].markdown(styled_html, unsafe_allow_html=True)
    return df


def dict_to_markdown(question, Sub, data, iter_count,main_count):
    # Initialize an empty list to store DataFrames
    # Append row
    if iter_count == 1:
        temp = f"{question}\n {Sub}"
        st.session_state["table_rows"].append([main_count, question,iter_count,Sub, data['Answer'], data['Reason']])
    else:
        st.session_state["table_rows"].append(["","",iter_count,Sub, data['Answer'], data['Reason']])

    # Convert to DataFrame
    df = pd.DataFrame(
        st.session_state["table_rows"],
        columns=["Main No.", "Main Question","Sub no.", "Sub-Question", "Answer", "Reason"]
        #columns = ["Main No.", "Question", "Sub no.", "Sub-Question", "Answer", "Score"]
    )
    # df.index = df.index + 1
    # df.index.name = "Sr No."
    df["Main No."] = df["Main No."].apply(lambda x: f"<b>{x}</b>" if x != "" else "")
    html_table = df.to_html(index=False, escape=False)
    # Add CSS for custom column widths
    styled_html = f"""
    <div style="max-height: 600px; overflow-y: auto; border: 1px solid #ddd;">
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', sans-serif;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px 10px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
                position: sticky;      /*  Makes header stick */
                top: 0;                /*  Stick to top of scroll container */
                z-index: 2;            /*  Ensure header stays above rows */
            }}
            /* Column widths */
            th:nth-child(1), td:nth-child(1) {{ width: 10%; text-align: center; }}
            th:nth-child(2), td:nth-child(2) {{ width: 20%; }}
            th:nth-child(3), td:nth-child(3) {{ width: 10%; text-align: center; }}
            th:nth-child(4), td:nth-child(4) {{ width: 20%; }}
            th:nth-child(5), td:nth-child(5) {{ width: 10%; text-align: center; }}
            th:nth-child(6), td:nth-child(6) {{ width: 30%; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
        </style>
        {html_table}
    </div>
    """

    st.session_state["table_placeholder"].markdown(styled_html, unsafe_allow_html=True)
    return df


def table_render(main_no, new_main_question):
    """
    Update the Main Question content for a given Main No.
    and re-render the table in Streamlit frontend.
    """

    # --- Safety check ---
    if "table_rows" not in st.session_state or len(st.session_state["table_rows"]) == 0:
        st.warning("No table data found to update.")
        return

    updated = False

    # --- Update the matching row(s) ---
    for i, row in enumerate(st.session_state["table_rows"]):
        # row[0] = Main No., row[1] = Main Question
        if str(row[0]) == str(main_no):
            st.session_state["table_rows"][i][1] = new_main_question
            updated = True

    if not updated:
        st.warning(f"No row found with Main No. = {main_no}")
        return

    # --- Re-render the table with same formatting ---
    df = pd.DataFrame(
        st.session_state["table_rows"],
        columns=["Main No.", "Main Question","Sub no.", "Sub-Question", "Answer", "Reason"]
    )
    df["Main No."] = df["Main No."].apply(lambda x: f"<b>{x}</b>" if x != "" else "")

    html_table = df.to_html(index=False, escape=False)

    styled_html = f"""
    <div>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', sans-serif;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 6px 10px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
            }}
            th:nth-child(1), td:nth-child(1) {{ width: 10%; text-align: center; }}
            th:nth-child(2), td:nth-child(2) {{ width: 20%; }}
            th:nth-child(3), td:nth-child(3) {{ width: 10%; text-align: center; }}
            th:nth-child(4), td:nth-child(4) {{ width: 20%; }}
            th:nth-child(5), td:nth-child(5) {{ width: 10%; text-align: center; }}
            th:nth-child(6), td:nth-child(6) {{ width: 30%; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
        </style>
        {html_table}
    </div>
    """

    # Re-display the updated table
    st.session_state["table_placeholder"].markdown(styled_html, unsafe_allow_html=True)
    st.success(f"Updated Main Question for Main No. {main_no}")


def table_render2(main_no, new_main_question):
    """
    Update the Main Question for a given Main No.
    and re-render the table using dict_to_markdown().
    """

    if "table_rows" not in st.session_state or len(st.session_state["table_rows"]) == 0:
        st.warning("No table data found to update.")
        return

    updated = False

    # Find and update the target row
    for i, row in enumerate(st.session_state["table_rows"]):
        if str(row[0]) == str(main_no):
            st.session_state["table_rows"][i][1] = new_main_question
            updated = True

    if not updated:
        st.warning(f"No row found with Main No. = {main_no}")
        return

    # Just re-render using the existing function
    df = dict_to_markdown("", "", {"Answer": "", "Reason": ""}, iter_count=0, main_count=0)

    st.success(f"✅ Main Question updated for Main No. {main_no}")
    return df

def table_render3(main_no, score):
    """
    Append the calculated score to the Main Question cell
    and re-render the table using dict_to_markdown().
    """
    if "table_rows" not in st.session_state or len(st.session_state["table_rows"]) == 0:
        st.warning("No table data found to update.")
        return

    updated = False
    for i, row in enumerate(st.session_state["table_rows"]):
        if str(row[0]) == str(main_no):
            # Append or replace the score
            if "Score:" in row[1]:
                # Update old score (optional)
                row[1] = re.sub(r"Score:.*", f"Score: {score:.2f}", row[1])
            else:
                row[1] += f" | Score: {score:.2f}"
            st.session_state["table_rows"][i] = row
            updated = True

    if not updated:
        st.warning(f"No row found with Main No. = {main_no}")
        return

    # Re-render using dict_to_markdown
    dict_to_markdown("", "", {"Answer": "", "Reason": ""}, iter_count=0, main_count=0)

def table_render(main_no, score):
    """
    Append or update the score for a given Main Question (by Main No.)
    and re-render the table with styled color coding.
    """

    if "table_rows" not in st.session_state or len(st.session_state["table_rows"]) == 0:
        st.warning("No table data found to update.")
        return

    updated = False

    # Color-code based on score value
    if score >= 0.75:
        color = "green"
    elif score >= 0.4:
        color = "orange"
    else:
        color = "red"

    score_text = f'<span style="color:{color}; font-weight:bold;">Score: {score:.2f}</span>'

    # Find and update the target row
    for i, row in enumerate(st.session_state["table_rows"]):
        if str(row[0]) == str(main_no):
            if "Score:" in row[1]:
                # Replace existing score text
                row[1] = re.sub(r"Score:.*?(</span>|$)", score_text, row[1])
            else:
                # Append score to question
                row[1] += f" | {score_text}"
            st.session_state["table_rows"][i] = row
            updated = True
            break

    if not updated:
        st.warning(f"No row found with Main No. = {main_no}")
        return

    # Re-render the table using dict_to_markdown()
    dict_to_markdown("", "", {"Answer": "", "Reason": ""}, iter_count=0, main_count=0)

def find_file(target_filename):
    """Recursively search for a file in all folders starting from start_dir."""
    target_name = target_filename.replace('.pdf', '_with_desc.md')
    for dirpath, _, filenames in os.walk("logs"):
        if target_name in filenames:
            return Path(dirpath) / target_name  # Return immediately after finding the first occurrence
    return None  # Return None if the file is not found

def query_ollama(prompt):
    # print('\n\n',prompt,'\n\n')
    try:
        url = "http://localhost:11434/api/generate"
        # url = "http://10.144.177.192:12345/api/generate"
        response = requests.post(url,
                                 json={
                                     #"model": "mistral-nemo:12b-instruct-2407-q4_K_M",
                                     # "model": "mistral-nemo:12b-instruct-2407-q4_K_M",
                                     "model": "glm4:latest",
                                     "prompt": prompt,
                                     "stream": False,
                                     "options": {
                                         "temperature": 0.1
                                     }
                                 })
        result = response.json()
        extracted_value = result['response']  # .strip().strip('"').strip()
        return extracted_value if extracted_value else ""
    except Exception as e:
        print(f"Error querying Ollama server: {str(e)}")
        return ""


# Initialize session state
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = []
    load_from_local_storage()

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Verify SRS"

if 'show_delete_confirm' not in st.session_state:
    st.session_state.show_delete_confirm = False

# App configuration
st.set_page_config(
    page_title="SRS Verification System",
    page_icon="📋",
    layout="wide"
)

st.title("📋 SRS Verification System")
st.markdown("---")

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")

    # Don't auto-switch pages - let user control navigation
    page = st.selectbox(
        "Select Page",
        ["Verify SRS", "Add/Edit Questions", "View All Questions", "Export/Import Data"],
        index=["Verify SRS", "Add/Edit Questions", "View All Questions", "Export/Import Data"].index(
            st.session_state.current_page)
    )

    st.session_state.current_page = page
    print(st.session_state.current_page, '\n')
    # Update current page in session state only if user manually changed it
    if page != st.session_state.current_page:
        st.session_state.current_page = page
        # Reset edit mode when changing pages manually
        if page != "Verify SRS":
            reset_form()

# Page 1: Add/Edit Questions
if page == "Add/Edit Questions":
    st.header("Add/Edit Questions")

    # Show notification if in edit mode
    if st.session_state.edit_mode and st.session_state.edit_index is not None:
        if st.session_state.edit_index < len(st.session_state.questions_data):
            edit_data = st.session_state.questions_data[st.session_state.edit_index]
            st.info(f"Currently editing question ID: {edit_data['id']}")
        else:
            # Invalid edit index, reset
            reset_form()

    # Form section
    col1, col2 = st.columns([3, 1])

    with col1:
        # Get default values if in edit mode
        if st.session_state.edit_mode and st.session_state.edit_index is not None and st.session_state.edit_index < len(st.session_state.questions_data):
            edit_data = st.session_state.questions_data[st.session_state.edit_index]
            default_doc_type = edit_data["doc_type"]
            default_question = edit_data["question"]
            default_sub_questions = edit_data["sub_questions"]
            default_reference = edit_data["reference_section"]
            default_instructions = edit_data["special_instructions"]
            form_title = f"Edit Question (ID: {edit_data['id']})"
        else:
            default_doc_type = "SRS"
            default_question = ""
            default_sub_questions = ""
            default_reference = ""
            default_instructions = ""
            form_title = "Add New Question"

        st.subheader(form_title)

        # Form fields
        doc_type = st.selectbox(
            "Document Type",
            DOC_TYPES,
            index=DOC_TYPES.index(default_doc_type) if default_doc_type in DOC_TYPES else 0,
            key="doc_type_select"
        )

        question = st.text_area(
            "Question",
            value=default_question,
            height=100,
            placeholder="Enter your main question here...",
            key="question_input"
        )

        sub_questions = st.text_area(
            "Sub-questions",
            value=default_sub_questions,
            height=120,
            placeholder="Enter sub-questions (one per line or as needed)...",
            key="sub_questions_input"
        )

        reference_section = st.text_area(
            "Reference Section",
            value=default_reference,
            height=100,
            placeholder="Enter reference information...",
            key="reference_input"
        )

        special_instructions = st.text_area(
            "Prompts for each sub-question",
            value=default_instructions,
            height=100,
            placeholder="Enter any special instructions or prompts ...",
            key="instructions_input"
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer

        # Form buttons
        if st.session_state.edit_mode:
            if st.button("Update Question", type="primary", key="update_btn"):
                if question.strip():
                    success = update_question(
                        st.session_state.edit_index,
                        doc_type, question, sub_questions,
                        reference_section, special_instructions
                    )
                    if success:
                        st.success("Question updated successfully!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error("Failed to update question.")
                else:
                    st.error("Please enter a question before submitting.")

            if st.button("Cancel Edit", key="cancel_btn"):
                reset_form()
                st.rerun()
        else:
            if st.button("Add Question", type="primary", key="add_btn"):
                if question.strip():
                    add_question(doc_type, question, sub_questions, reference_section, special_instructions)
                    st.success("Question added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a question before submitting.")


# Page 2: View All Questions
elif page == "View All Questions":
    st.header("All Questions")
    if st.session_state.questions_data:
        # Filter options
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            filter_doc_type = st.selectbox(
                "Filter by Document Type",
                ["All"] + DOC_TYPES
            )

        with col2:
            search_term = st.text_input("Search in questions", placeholder="Type to search...")

        with col3:
            st.write("")  # Spacer
            if not st.session_state.show_delete_confirm:
                if st.button("Clear All Data", type="secondary"):
                    st.session_state.show_delete_confirm = True
                    st.rerun()
            else:
                st.warning("Are you sure you want to delete all questions?")
                col3a, col3b = st.columns(2)
                with col3a:
                    if st.button("Yes, Delete All", type="primary"):
                        st.session_state.questions_data = []
                        st.session_state.show_delete_confirm = False
                        reset_form()
                        st.success("All questions deleted!")
                        st.rerun()
                with col3b:
                    if st.button("Cancel"):
                        st.session_state.show_delete_confirm = False
                        st.rerun()

        # Filter data
        filtered_data = st.session_state.questions_data

        if filter_doc_type != "All":
            filtered_data = [q for q in filtered_data if q["doc_type"] == filter_doc_type]

        if search_term:
            filtered_data = [q for q in filtered_data if search_term.lower() in q["question"].lower()]

        # Display questions
        if filtered_data:
            st.write(f"Showing {len(filtered_data)} question(s)")

            for i, q in enumerate(filtered_data):
                # Find original index for edit/delete operations
                # print(f'q is {q} \n')
                # print(q['question'],'\n\n')
                # print(q['sub_questions'], '\n\n')
                original_index = st.session_state.questions_data.index(q)

                with st.expander(f"[{q['doc_type']}] {q['question'][:50]}..." if len(
                        q['question']) > 50 else f"[{q['doc_type']}] {q['question']}", expanded=False):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(f"**ID:** {q['id']}")
                        st.write(f"**Document Type:** {q['doc_type']}")
                        st.write(f"**Question:** {q['question']}")

                        if q['sub_questions']:
                            st.write(f"**Sub-questions:** {q['sub_questions']}")

                        if q['reference_section']:
                            st.write(f"**Reference Section:** {q['reference_section']}")

                        if q['special_instructions']:
                            st.write(f"**Prompts:** {q['special_instructions']}")

                        st.write(f"**Created:** {q['created_at']}")
                        st.write(f"**Updated:** {q['updated_at']}")

                    with col2:
                        if st.button("Edit", key=f"edit_{original_index}"):
                            st.session_state.edit_mode = True
                            st.session_state.edit_index = original_index
                            st.session_state.current_page = "Add/Edit Questions"
                            # st.rerun() ## Commented to stop rerunning

                        if st.button("Delete", key=f"delete_{original_index}", type="secondary"):
                            success = delete_question(original_index)
                            if success:
                                st.success("Question deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to delete question.")
        else:
            st.info("No questions found matching your criteria.")
    else:
        st.info("No questions added yet. Go to 'Add/Edit Questions' to add your first question.")

# Page 3: Export/Import Data
elif page == "Export/Import Data":
    st.header("Export/Import Data")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Data")
        export_format = st.radio("Select export format:", ["JSON", "CSV"])
        if st.session_state.questions_data:
            if export_format == "JSON":
                json_data = json.dumps(st.session_state.questions_data, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"questions_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                df = pd.DataFrame(st.session_state.questions_data)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"questions_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No data to export")

    with col2:
        st.subheader("Import Data")

        uploaded_file = st.file_uploader(
            "Upload JSON file",
            type=['json'],
            help="Upload a previously exported JSON file"
        )

        if uploaded_file is not None:
            try:
                imported_data = json.load(uploaded_file)

                if isinstance(imported_data, list):
                    st.write(f"Found {len(imported_data)} questions in the file")

                    import_option = st.radio(
                        "Import option:",
                        ["Replace existing data", "Append to existing data"]
                    )

                    if st.button("Import Data"):
                        if import_option == "Replace existing data":
                            st.session_state.questions_data = imported_data
                        else:
                            st.session_state.questions_data.extend(imported_data)

                        st.success(f"Successfully imported {len(imported_data)} questions!")
                        st.rerun()
                else:
                    st.error("Invalid file format. Please upload a valid JSON file.")

            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please check the file format.")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")


# Page4 Generate Results
elif page == "Verify SRS":
    yes_count = 0
    no_count = 0
    ans = []
    x=0
     # 🟢 Initialize weights (example)
    weights = [
    [4.17, 5.83],  # Row 1,   
    [0.83, 1.67, 2.5, 3.0],  # Row 2,  
    [1, 1, 1, 1, 1, 1, 1, 1, .5, .5, .5 , .5],  # Row 3, 
    [1.67, 3.33, 5.0],  # Row 4,  
    [0.67, 1.33, 2.0, 2.67, 3.33],  # Row 5,   
    [10.0],  # Row 6,   
    [4.17, 5.83],  # Row 7,  
    [4.17, 5.83],  # Row 8,  
    [10.0],  # Row 9,   
    [10.0],  # Row 10,   
    [10.0],  # Row 11,   
    [10.0],  # Row 12,   
    [4.17, 5.83],  # Row 13,   
    [10.0],  # Row 14,   
    [10.0],  # Row 15,   
    [4.17, 5.83],  # Row 16,   
    [10.0],  # Row 17,   
    [10.0]   # Row 18,   
]

     # 🟢 Initialize results array (same shape)
    results = [[] for _ in range(len(weights))]
    main_weights = [
    0.5, 0.4, 0.6, 0.5, 0.4, 0.5,
    0.6, 0.7, 0.5, 0.4, 0.5, 0.6,
    0.4, 0.6, 0.5, 0.4, 0.6, 0.6
    ]

    col1, col2 = st.columns([0.10, 0.90])
    with col2:
        # sub_col1, sub_col2 = st.columns(2)
        if "table_rows" not in st.session_state:
            st.session_state["table_rows"] = []
        # Create a placeholder for the table
        if "table_placeholder" not in st.session_state:
            st.session_state["table_placeholder"] = st.empty()

        with st.sidebar:
            pdf = st.file_uploader("Upload PDF below", type=['.pdf'])
            Button = st.button("Submit")

        if Button:

            if pdf is None:
                st.warning("PDF not uploaded. Please upload the PDF file")
            else:
                out_dir = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                os.mkdir(f"logs/{out_dir}")
                with open(f"logs/{out_dir}/{pdf.name}", "wb") as f1:
                  f1.write(pdf.getbuffer())

                # cache_file = find_file(pdf.name)  # Find converted file in logs
                # if cache_file:
                #     md_file_text = open(cache_file).read()
                # else:
                with st.spinner('Processing the SRS Document'):
                    md = pdf_to_descriptive_mapped_sections(f'logs/{out_dir}/{pdf.name}', f'logs/{out_dir}')

                sections_to_search = md['mapped_sections'].keys()
                print(f'\n\n {sections_to_search} \n\n')
                # sections_to_search = list(loaded_dict.keys())
                mapped_text_dict = md['mapped_sections']

                log_file = open(f"logs/{out_dir}/logfile.txt", "w")
                Main_Counter = 0
                for i, q in enumerate(st.session_state.questions_data):
                    print('*' * 80)
                    print(q['question'])
                    print('*' * 80, '\n\n')
                    log_file.write(f'\n {q['question']} \n')
                    log_file.write('#' * 100)

                    # Initialize an empty dictionary for each question

                    final_responses = {}
                    sections = q['reference_section']
                    section_list = [s.strip() for s in sections.splitlines() if len(s) > 0]
                    print('\n', 'Entered section is  ', section_list, '\n\n')

                    if section_list:
                        content_to_search = ""
                        for entered_sec in section_list:
                            match_found = False
                            for key in sections_to_search:
                                if fuzz.WRatio(entered_sec, key) >= 76 and not match_found:
                                    #print(f'Matched {entered_sec} with {key} ratio is {fuzz.WRatio(entered_sec, key)}')
                                    match_found = True
                                    try:
                                        # print('\n',mapped_text_dict[key],'\n')
                                        text = mapped_text_dict[key]['content']
                                        # print(f'\n text is {text} \n')
                                        # print(f'\n Length of text is {len(text)} \n')
                                        content_to_search += text
                                    except Exception as exp:
                                        # pass
                                        log_file.write(f'\n exception {exp} for {key} content not found \n')
                                        print(f'exception for {key} {exp}')
                    else:
                        # take full content if no ref section is given
                        content_to_search = f'{md['md_with_descriptions']}'

                    log_file.write(f'\n {content_to_search} \n')  # write the text to log file
                    sub_q = [line for line in q['sub_questions'].split('\n\n') if line != '']
                    sub_q = [section.strip() for section in sub_q]
                    # prompts = [line for line in q['special_instructions'].splitlines() if line != '']
                    prompts = [line for line in q['special_instructions'].split('\n\n') if line != '']
                    prompts = [section.strip() for section in prompts]

                    # if text_to_search is None:
                    #     print(f'\n ********** Section {section_list[0]} not found in Table of Contents Page *********\n')
                    #     continue

                    iteration_counter = 0
                    Main_Counter = Main_Counter + 1
                     # 🟢 Prepare to store sub-question results
                    current_results = []
                    for j in range(len(sub_q)):
                        # print(f'\n {st.session_state['table_rows']} \n')
                        final_prompt2 = f"""
                                        #########################p
                                        Text: {content_to_search} 
                                        #########################
                                        Instructions:
                                        You are given a document content in the above `Text` {prompts[j]}
                                        Return the response strictly in the JSON format: {{ "Answer": "Yes/No", "Reason": "..." }}
                                        """
                        final_prompt = f"""
                                        #########################
                                        Text: {content_to_search}
                                        #########################
                                        Instructions:
                                        You are given a document content in the above `Text`.

                                        Now, follow the checklist below carefully:
                                        {prompts[j]}

                                        Your task:
                                        Evaluate the document *practically*, not rigidly. 
                                        If the information seems partially mentioned, inferred, or described indirectly, still consider it as **"Partially Yes"** (not strictly No).
                                        Be lenient where technical meaning is clear even if phrasing differs.

                                        Respond in **JSON** format as:
                                        {{
                                        "Answer": "Yes" / "Partially Yes" / "No",
                                        "Reason": "Provide a clear, concise explanation (40–60 words) describing which aspects are mentioned, implied, or missing. Be objective and avoid repetition."
                                        }}

                                        Guidelines:
                                        - If the content explicitly meets the criteria → "Yes".
                                        - If it somewhat covers or implies it → "Partially Yes".
                                        - If it is missing or unrelated → "No".
                                        - Maintain neutral tone and professional phrasing.
                                        """


                        resp = query_ollama(final_prompt)
                        iteration_counter += 1
                        # print(f'Iter count is {iteration_counter}')
                        # print(f'\n {resp} \n')
                        # final_response = json.loads(resp)
                        if resp.startswith("```json") and resp.endswith("```"):
                            js = resp.replace("```json", "").replace("```", "")
                            final_response = json.loads(js)
                            print(f'\n {final_response} {type(final_response)} \n')
                            df_to_write=dict_to_markdown(f'{q['question']}', f'{sub_q[j]}', final_response, iteration_counter,Main_Counter)

                        else:
                            final_response = json.loads(resp)
                            print(f'\n {final_response} {type(final_response)}\n')
                            df_to_write=dict_to_markdown(f'{q['question']}', f'{sub_q[j]}', final_response, iteration_counter,Main_Counter)

                        # Update the dictionary with the new response"**Score out of 10:  {score} **"


                        if final_response['Answer'] == "Yes":
                            yes_count = yes_count + 1
                            current_results.append(1)
                        else:
                            no_count = no_count + 1
                            current_results.append(0)

                        # Save the responses to a csv file
                        df_to_write.to_csv(f"logs/{out_dir}/responses_log.csv", index=False)
                    # 🟢 After finishing all sub-questions for this main question
                    results[Main_Counter - 1] = current_results
                        # 🟢 Compute weighted score
                    score = 0.0
                    if len(weights) >= Main_Counter:
                        w = weights[Main_Counter - 1]
                        r = results[Main_Counter - 1]
                        if len(w) == len(r):
                            score = sum([wi * ri for wi, ri in zip(w, r)])
                        else:
                            st.warning(f"Weight length mismatch for Main {Main_Counter}")
                    else:
                        st.warning(f"No weights defined for Main {Main_Counter}")

                    # 🟢 Append score to Main Question using table_render
                    table_render(Main_Counter, score)
                    Score_final += main_weights[Main_Counter-1]*score

                log_file.close()
                # st.markdown(f"**Total Yes: {yes_count}**")
                # st.markdown(f"**Total Questions: {yes_count+no_count}**")
                # score = 0
                # if yes_count > 0:
                #     score = (yes_count * 10) / (yes_count + no_count)
                # st.markdown(f"**Score out of 10:  {score:.2f}**")
                st.markdown(f"<span style='font-size:25px; font-weight:bold;'>Total 18 Questions</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:25px; font-weight:bold;'>Score out of 10: {Score_final:.2f}</span>", unsafe_allow_html=True)
                print('#' * 80)
                print(' Questions Completed')
                print('#' * 80, '\n')
                print("Score out of 10:  ", score)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        SRS Verification System | Built by DEAIS
    </div>
    """,
    unsafe_allow_html=True
)

# Display current data stats in sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("Statistics")

    total_questions = len(st.session_state.questions_data)
    st.metric("Total Questions", total_questions)

    if total_questions > 0:
        doc_type_counts = {}
        for q in st.session_state.questions_data:
            doc_type = q["doc_type"]
            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1

        st.write("**By Document Type:**")
        for doc_type, count in doc_type_counts.items():
            st.write(f"• {doc_type}: {count}")
