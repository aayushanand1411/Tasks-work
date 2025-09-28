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
import ollama
# from ZFinal_md_with_section import *

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


DATA_FILE = "questions_data.json"


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


def dict_to_markdown(question, prompt, data, iter_count):
    # Create the header of the table
    markdown = "| Question | Sub-Question (prompt) | Answer | Reason |\n"
    markdown += "| --- | --- | --- | --- |\n"
    # iter = 1

    # Add the main question row with empty sub-question and result
    # Iterate over each key-value pair in the dictionary

    # iter = 1
    if iter_count == 1:
        markdown += f"| {question} |{prompt} | {data['Answer']} | {data['Reason']} |\n"
    else :
        markdown += f"| | {prompt} | {data['Answer']} | {data['Reason']} |\n"

    return markdown


def query_ollama(prompt):
    # print('\n\n',prompt,'\n\n')
    try:
        url = "http://localhost:11434/api/generate"
        # url = "http://10.144.177.192:12345/api/generate"
        response = requests.post(url,
                                 json={
                                     "model": "gemma3:4",
                                     "prompt": prompt,
                                     "stream": False,
                                     "options": {
                                         "temperature": 0.01
                                     }
                                 })
        result = response.json()
        extracted_value = result['response']  # .strip().strip('"').strip()
        return extracted_value if extracted_value else ""
        print(f'extracted_value is {extracted_value}')
    except Exception as e:
        print(f"Error querying Ollama server: {str(e)}")
        return ""


def get_sections(index_list, start_no):
    start_sec = None
    end_sec = None
    end_no = int(start_no) + 1
    ct = 1
    for line in index_list:
        if line.startswith(f'## {start_no}'):
            ct += 1
            if ct == 2:
                start_sec = line
        elif line.startswith(f'## {end_no}'):
            end_sec = line
            break
    return start_sec, end_sec


# Initialize session state
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = []
    load_from_local_storage()

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Add/Edit Questions"

if 'show_delete_confirm' not in st.session_state:
    st.session_state.show_delete_confirm = False

# App configuration
st.set_page_config(
    page_title="Document Questions Manager",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Document Questions Manager")
st.markdown("---")

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")

    # Don't auto-switch pages - let user control navigation
    page = st.selectbox(
        "Select Page",
        ["Add/Edit Questions", "View All Questions", "Export/Import Data", "Generate Result"],
        index=["Add/Edit Questions", "View All Questions", "Export/Import Data", "Generate Result"].index(
            st.session_state.current_page)
    )

    st.session_state.current_page = page
    print(st.session_state.current_page, '\n')
    # Update current page in session state only if user manually changed it
    if page != st.session_state.current_page:
        st.session_state.current_page = page
        # Reset edit mode when changing pages manually
        if page != "Add/Edit Questions":
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
        if st.session_state.edit_mode and st.session_state.edit_index is not None and st.session_state.edit_index < len(
                st.session_state.questions_data):
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
elif page == "Generate Result":
    yes_count = 0
    no_count = 0
    col1, col2 = st.columns([0.10, 0.90])
    # with col1:
    #     st.image("logo_dark.png")
    # st.set_page_config(layout="wide", page_icon="logo_dark.png",page_title="RCI Software-Assistant")
    with col2:
        sub_col1, sub_col2 = st.columns(2)

        with st.sidebar:
            pdf = st.file_uploader("Upload PDF below", type=['.pdf'])
            Button = st.button("Submit")

        if Button:
            # if pdf is None:
            #     # st.warning("PDF not uploaded. Please upload the PDF file")
            # else:
            # with open(f"logs/{pdf.name}", "wb") as f1:
            #     f1.write(pdf.getbuffer())

            # # if os.path.exists(f'logs/{pdf.name.replace(".pdf", "_with_desc.md")}'):
            # #     md_file_text = open(f'logs/{pdf.name.replace(".pdf", ".md")}').read()
            # # else:
            # with st.spinner('Converting pdf to markdown .......'):
            #     out_dir = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            #     os.mkdir(f"logs/{out_dir}")
            #     md = pdf_to_descriptive_mapped_sections(f'logs/{pdf.name}', f'logs/{out_dir}')

            # with open(
            #         '/home/dlpda/Tejawork/kalidas_sir_work/DocVerification/docling_work/logs/2025-09-25-10:07:31/saved_mapped_dict.json',
            #         'r') as f:
            #     loaded_dict = json.load(f)

            # sections_to_search = md['mapped_sections'].keys()
            # sections_to_search = list(loaded_dict.keys())
            # # mapped_text_dict = md['mapped_sections']
            # mapped_text_dict = loaded_dict
            for i, q in enumerate(st.session_state.questions_data):
                print('*' * 80)
                print(q['question'])
                print('*' * 80, '\n\n')

                # Initialize an empty dictionary for each question

                final_responses = {}
                sections = q['reference_section']
                section_list = [s.strip() for s in sections.splitlines() if len(s) > 0]
                print('\n', 'Entered section is  ', section_list, '\n\n')

                if section_list:
                    for entered_sec in section_list:
                        content_to_search = ""
                        match_found = False
                        # print(f'entered section is {entered_sec}')
                        # for key in sections_to_search:
                        #     if fuzz.WRatio(entered_sec, key) >= 76 and not match_found:
                        #         print(f'Matched {entered_sec} with {key} ratio is {fuzz.WRatio(entered_sec, key)}')
                        #         match_found = True
                        #         try:
                        #             content_to_search += "".join(mapped_text_dict[key].get("content", []))
                        #         except Exception as exp:
                        #             print(f'exception for {key}')
                else:
                    # take full content if no ref section is given
                    # content_to_search = open(f'logs/{out_dir}/{pdf.name.replace(".pdf", "_with_desc.md")}').read()
                    content_to_search = "My name is Aayush"

                # print(text_to_search,'\n\n')
                # sub_q = [line.strip() for line in q['sub_questions'].splitlines()]
                sub_q = [line for line in q['sub_questions'].split('\n\n') if line != '']
                sub_q = [section.strip() for section in sub_q]
                # prompts = [line for line in q['special_instructions'].splitlines() if line != '']
                prompts = [line for line in q['special_instructions'].split('\n\n') if line != '']
                prompts = [section.strip() for section in prompts]




                # if text_to_search is None:
                #     print(f'\n ********** Section {section_list[0]} not found in Table of Contents Page *********\n')
                #     continue

                iteration_counter = 0
                markdown_list = []
                for j in range(len(sub_q)):
                    #print('\n',prompts[j],'\n')
                    final_prompt = f"""
                                    #########################p
                                    Text: {content_to_search} 
                                    #########################
                                    Instructions:
                                    You are given a document content in the above `Text` {prompts[j]}
                                    Return the response strictly in the JSON format: {{ "Answer": "Yes/No", "Reason": "..." }}
                                    """

                    resp = query_ollama(final_prompt)
                    iteration_counter += 1
                    print(f'Iter count is {iteration_counter}')
                    # print(f'\n {resp} \n')
                    # final_response = json.loads(resp)
                    if resp.startswith("```json") and resp.endswith("```"):
                        js = resp.replace("```json", "").replace("```", "")
                        final_response = json.loads(js)
                        print(f'\n {final_response} {type(final_response)} \n')
                        st.write(dict_to_markdown(f"{q['question']}", f"{prompts[j]}", final_response, iteration_counter))
                    else:
                        final_response = json.loads(resp)
                        print(f'\n {final_response} {type(final_response)}\n')
                        st.write(dict_to_markdown(f"{q['question']}", f"{prompts[j]}", final_response, iteration_counter))

                    # Update the dictionary with the new response

                    if final_response['Answer'] == "Yes":
                        yes_count = yes_count + 1
                    else:
                        no_count = no_count + 1

                # with sub_col1:
                #     # print(f'\n {final_responses} \n')
                #     for markdown in markdown_list:
                #         st.write(markdown)

            st.write('yescount  ', yes_count)
            st.write('nocount  ', no_count)
            score = (yes_count * 10) / (yes_count + no_count)
            st.write('**Questions Completed**')
            st.write('**Score out of 10:  ', score)
            print('#' * 80)
            print(' Questions Completed')
            print('#' * 80, '\n')
            print("Score out of 10:  ", score)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Document Questions Manager | Built with Streamlit
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
