import streamlit as st
import json
import os
import ollama
from datetime import datetime

# ========================
# STREAMLIT PAGE SETUP
# ========================
st.set_page_config(page_title="🧠 LLM Prompt Evaluator (Ollama)", layout="wide")

st.title("🧩 LLM Prompt Evaluator using Ollama")

# ========================
# CREATE OLLAMA CLIENT
# ========================
try:
    client = ollama.Client()
except Exception as e:
    st.error(f"❌ Could not initialize Ollama client: {e}")
    st.stop()

# ========================
# FUNCTIONS
# ========================

def load_json(file_path):
    """Load JSON file content."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return {}

def save_json(data, file_path):
    """Save JSON back to file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        st.toast("✅ Prompt saved successfully!", icon="💾")
    except Exception as e:
        st.error(f"Error saving JSON: {e}")

def query_llm_ollama(model, prompt, content):
    """Query Ollama model with a prompt and content."""
    try:
        full_input = f"### PROMPT:\n{prompt}\n\n### CONTENT:\n{content}"
        response = client.generate(model=model, prompt=full_input)
        return response.get("response", "").strip()
    except Exception as e:
        st.error(f"Error querying Ollama: {e}")
        return "Error during LLM response."

def generate_recommendation_prompt(model, original_prompt, content, answer):
    """Use another Ollama model to suggest a better prompt."""
    try:
        recom_input = (
            "You are an expert prompt engineer.\n\n"
            "Given the following:\n"
            f"Original Prompt: {original_prompt}\n\n"
            f"Content: {content}\n\n"
            f"Answer Generated: {answer}\n\n"
            "Suggest a better version of the original prompt (50–100 words) "
            "that would yield a more accurate or detailed response."
        )
        response = client.generate(model=model, prompt=recom_input)
        return response.get("response", "").strip()
    except Exception as e:
        st.error(f"Error generating recommended prompt: {e}")
        return "Error during recommendation prompt generation."

# ========================
# USER INPUT SECTION
# ========================

st.sidebar.header("⚙️ Configuration")

prompt_path = st.sidebar.text_input("📄 Path to Prompts JSON:", "")
content_path = st.sidebar.text_input("📚 Path to Content JSON:", "")
model_1 = st.sidebar.text_input("🧠 Primary LLM Model (for answers):", "llama3")
model_2 = st.sidebar.text_input("💡 Secondary LLM Model (for prompt improvement):", "llama3")

if prompt_path and content_path and os.path.exists(prompt_path) and os.path.exists(content_path):
    prompts_data = load_json(prompt_path)
    content_data = load_json(content_path)

    prompt_keys = list(prompts_data.keys())
    content_keys = list(content_data.keys())

    st.sidebar.subheader("🗝 Select")
    selected_prompt_key = st.sidebar.selectbox("Prompt Key", prompt_keys)
    selected_content_key = st.sidebar.selectbox("Content Key", content_keys)

    current_prompt = prompts_data[selected_prompt_key]
    current_content = content_data[selected_content_key]

    edited_prompt = st.text_area("📝 Edit Prompt", value=current_prompt, height=150)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Save Edited Prompt"):
            prompts_data[selected_prompt_key] = edited_prompt
            save_json(prompts_data, prompt_path)

    with col2:
        run_llm = st.button("🚀 Run LLM")

    if run_llm:
        with st.spinner("Querying primary LLM..."):
            answer = query_llm_ollama(model_1, edited_prompt, current_content)

        st.subheader("🧠 LLM Answer")
        st.write(answer)

        with st.spinner("Generating improved prompt with secondary LLM..."):
            recommendation = generate_recommendation_prompt(model_2, edited_prompt, current_content, answer)

        st.subheader("💡 Recommended Improved Prompt")
        st.write(recommendation)

else:
    st.info("Please enter valid paths for both prompt and content JSON files in the sidebar.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + Ollama Client (Local LLM Integration)")
