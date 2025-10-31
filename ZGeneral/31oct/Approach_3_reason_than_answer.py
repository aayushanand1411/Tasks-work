def query_ollama_reason_first(content_to_search, prompt):
    """
    Approach 3:
    1️⃣ First ask LLM to generate a ~50-word reason.
    2️⃣ Then ask for Yes/No using that reason and the content.
    Returns: {"Answer": "Yes/No", "Reason": "..."}
    """

    # STEP 1: Ask for the reason first
    reason_prompt = f"""
    #########################
    Text: {content_to_search}
    #########################
    Instructions:
    You are given the above document content.
    {prompt}

    Please provide a concise reason (around 50 words) based on the text
    that supports or refutes the condition implied in the question.
    Do not answer Yes or No yet—only give the reasoning.
    """

    reason_resp = query_ollama(reason_prompt)
    reason_resp = re.sub(r"[\n\r]+", " ", reason_resp).strip()

    # STEP 2: Ask for the Yes/No decision using the reason
    decision_prompt = f"""
    #########################
    Text: {content_to_search}
    #########################
    Question:
    {prompt}

    Reason (from previous analysis):
    {reason_resp}

    Based on the above document content and reason,
    respond strictly with either "Yes" or "No".
    Do not include any explanation.
    """

    raw_resp = query_ollama(decision_prompt).strip()
    raw_resp = raw_resp.replace("```", "").replace('"', '').strip()

    # Extract Yes/No robustly
    if "yes" in raw_resp.lower():
        answer = "Yes"
    elif "no" in raw_resp.lower():
        answer = "No"
    else:
        answer = "No"  # fallback

    return {
        "Answer": answer,
        "Reason": reason_resp
    }

final_response = query_ollama_reason_first(content_to_search, prompts[j])

df_to_write = dict_to_markdown(
    f"{q['question']}", f"{sub_q[j]}", final_response, iteration_counter, Main_Counter, out_dir=out_dir
)
