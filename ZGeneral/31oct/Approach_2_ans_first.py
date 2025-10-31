def query_ollama_reasoned(content_to_search, prompt):
    """
    Approach 2:
    1️⃣ Ask for only 'Yes' or 'No'.
    2️⃣ Then, using that answer, ask LLM for a concise (~50 words) reason.
    Returns: {"Answer": "Yes/No", "Reason": "..."}
    """

    # STEP 1: Ask for Yes/No
    yesno_prompt = f"""
    #########################
    Text: {content_to_search}
    #########################
    Instructions:
    You are given the above document content.
    {prompt}

    Answer strictly with either "Yes" or "No" only.
    Do not provide any explanation.
    """

    raw_resp = query_ollama(yesno_prompt).strip()

    # Clean any Markdown formatting
    raw_resp = raw_resp.replace("```", "").strip()
    raw_resp = raw_resp.replace('"', '').strip()

    # Extract yes/no from the model output robustly
    if "yes" in raw_resp.lower():
        answer = "Yes"
    elif "no" in raw_resp.lower():
        answer = "No"
    else:
        answer = "No"  # default fallback

    # STEP 2: Ask for Reason (~50 words)
    reason_prompt = f"""
    #########################
    Text: {content_to_search}
    #########################
    The question was:
    {prompt}

    Given the above document content and question, the answer obtained is: '{answer}'.
    Please provide a concise reason (around 50 words) justifying why this answer is correct.
    Be factual and context-specific.
    """

    reason_resp = query_ollama(reason_prompt)

    # Clean the reason text
    reason_resp = re.sub(r"[\n\r]+", " ", reason_resp).strip()

    # Final combined output
    return {
        "Answer": answer,
        "Reason": reason_resp
    }

final_response = query_ollama_reasoned(content_to_search, prompts[j])


df_to_write = dict_to_markdown(
    f"{q['question']}", f"{sub_q[j]}", final_response, iteration_counter, Main_Counter, out_dir=out_dir
)
