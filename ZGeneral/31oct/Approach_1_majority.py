import json
from collections import Counter
import requests
import re
import streamlit as st

def query_ollama(prompt):
    """Base single query to Ollama (unchanged)."""
    try:
        url = "http://localhost:11434/api/generate"
        response = requests.post(
            url,
            json={
                "model": "gemma3:4",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.01},
            },
        )
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        print(f"Error querying Ollama server: {str(e)}")
        return ""

def query_ollama_majority(content_to_search, prompt):
    """
    Approach 1:
    Query Ollama 5 times for the same content & prompt,
    take the majority (Yes/No) and create a concise 50-word reason.
    """

    responses = []
    reasons = []

    # 5 independent runs
    for i in range(5):
        full_prompt = f"""
        #########################
        Text: {content_to_search}
        #########################
        Instructions:
        You are given a document content in the above `Text`.
        {prompt}
        Return the response strictly in JSON format: {{ "Answer": "Yes/No", "Reason": "..." }}
        """

        raw_resp = query_ollama(full_prompt)

        try:
            # Handle ```json blocks
            if raw_resp.startswith("```json") and raw_resp.endswith("```"):
                raw_resp = raw_resp.replace("```json", "").replace("```", "")

            parsed = json.loads(raw_resp)
            ans = parsed.get("Answer", "").strip()
            reason = parsed.get("Reason", "").strip()

            if ans in ["Yes", "No"]:
                responses.append(ans)
                reasons.append(reason)
        except Exception as e:
            print(f"[Warning] Could not parse response {i+1}: {e}")
            continue

    # If none of the runs succeeded
    if not responses:
        return {"Answer": "No", "Reason": "Could not determine from document."}

    # Majority voting for Answer
    majority_answer = Counter(responses).most_common(1)[0][0]

    # Combine all reasons for LLM summarization
    combined_reasons = " ".join(reasons)
    summary_prompt = f"""
    Combine and summarize the following explanations into one concise reason (about 50 words)
    supporting why the answer is '{majority_answer}'.
    Reasons:
    {combined_reasons}
    """

    concise_reason = query_ollama(summary_prompt)

    # Optional: clean up the summarized text
    concise_reason = re.sub(r"[\n\r]+", " ", concise_reason).strip()

    return {"Answer": majority_answer, "Reason": concise_reason}


final_response = query_ollama_majority(content_to_search, prompts[j])

df_to_write = dict_to_markdown(
    f"{q['question']}", f"{sub_q[j]}", final_response, iteration_counter, Main_Counter, out_dir=out_dir
)
