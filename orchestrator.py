import os
import sys
import json
import requests
from typing import List, Dict

# --- CONFIGURATION ---
# Supported providers: "ollama", "openai", "gemini", "anthropic", "interactive"
MODEL_A_CONFIG = {
    "provider": "ollama",
    "model": "nemotron-3-super:cloud",
    "api_url": "http://localhost:11434/v1/chat/completions",
    "api_key": ""  # Leave blank to load from environment variable (if applicable)
}

MODEL_B_CONFIG = {
    "provider": "interactive",
    "model": "Gemini 3.5 Flash (High)",
    "api_url": "",
    "api_key": ""
}

JUDGE_CONFIG = {
    "provider": "interactive",
    "model": "Gemini 3.5 Flash (High)",
    "api_url": "",
    "api_key": ""
}

ROUNDS = 2
TOPIC = "The feasibility of achieving AGI before 2030."
OUTPUT_FILE = "debate_transcript.md"

RUBRIC = """
Evaluate the opponent based on the following criteria (0-10 scale):
1. Logical Rigor: Soundness of arguments.
2. Factuality: Accuracy of claims.
3. Clarity: Conciseness and directness.
"""

# --- HELPER FUNCTIONS ---
def resolve_api_key_and_url(config: Dict) -> (str, str):
    provider = config.get("provider", "").lower()
    api_key = config.get("api_key", "")
    api_url = config.get("api_url", "")

    if not api_key:
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
        elif provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "")
        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        elif provider == "ollama":
            api_key = os.environ.get("OLLAMA_API_KEY", "")

    if not api_url:
        if provider == "ollama":
            api_url = "http://localhost:11434/v1/chat/completions"
        elif provider == "openai":
            api_url = "https://api.openai.com/v1/chat/completions"
        elif provider == "gemini":
            api_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        elif provider == "anthropic":
            api_url = "https://api.anthropic.com/v1/messages"

    return api_key, api_url

def call_llm(config: Dict, messages: List[Dict], require_json: bool = False) -> str:
    provider = config.get("provider", "").lower()
    model_name = config.get("model", "")

    if provider == "interactive":
        # Interactive prompting via stdin
        print(f"\n[REQUEST] Model: {model_name} (Interactive)")
        print(f"[REQUEST] Messages: {json.dumps(messages, indent=2)}")
        print(f"[REQUEST] Require JSON: {require_json}")
        print("[WAITING FOR RESPONSE] Please enter the response below (end with a line containing only '__END__'):")
        sys.stdout.flush()
        
        lines = []
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            if line.strip() == "__END__":
                break
            lines.append(line)
        return "".join(lines).strip()

    api_key, api_url = resolve_api_key_and_url(config)
    headers = {"Content-Type": "application/json"}
    
    if provider in ("openai", "gemini", "ollama"):
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7
        }
        if require_json:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API Error with {model_name} ({provider}): {e}")
            try:
                if 'response' in locals() and response is not None:
                    print("Response detail:", response.text)
            except Exception:
                pass
            return "{}" if require_json else "Error generating response."

    elif provider == "anthropic":
        if api_key:
            headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"

        # Transform messages format for Anthropic (extract system role, clean up alternating roles)
        system_content = None
        cleaned_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                role = "assistant" if msg["role"] == "assistant" else "user"
                if cleaned_messages and cleaned_messages[-1]["role"] == role:
                    cleaned_messages[-1]["content"] += "\n\n" + msg["content"]
                else:
                    cleaned_messages.append({"role": role, "content": msg["content"]})
        
        if not cleaned_messages:
            cleaned_messages.append({"role": "user", "content": "Hello"})

        payload = {
            "model": model_name,
            "messages": cleaned_messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        if system_content:
            payload["system"] = system_content

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except Exception as e:
            print(f"Anthropic API Error with {model_name}: {e}")
            try:
                if 'response' in locals() and response is not None:
                    print("Response detail:", response.text)
            except Exception:
                pass
            return "{}" if require_json else "Error generating response."
    
    else:
        print(f"Unknown provider: {provider}")
        return "{}" if require_json else "Error: Unknown provider."

# --- MAIN SYSTEM ---
def run_debate():
    model_a_name = MODEL_A_CONFIG.get("model", "Model A")
    model_b_name = MODEL_B_CONFIG.get("model", "Model B")
    judge_name = JUDGE_CONFIG.get("model", "Judge")

    print(f"--- Starting Debate on: {TOPIC} ---")
    print(f"Model A: {model_a_name} ({MODEL_A_CONFIG.get('provider')})")
    print(f"Model B: {model_b_name} ({MODEL_B_CONFIG.get('provider')})")
    print(f"Judge:   {judge_name} ({JUDGE_CONFIG.get('provider')})")

    # 1. Initialize Contexts
    history_A = [
        {
            "role": "system",
            "content": f"You are Debater A ({model_a_name}). Present arguments clearly. Question Debater B's logic. Keep responses under 150 words.",
        }
    ]
    history_B = [
        {
            "role": "system",
            "content": f"You are Debater B ({model_b_name}). Act as a skeptic. Point out flaws in Debater A's arguments and counter them. Keep responses under 150 words.",
        }
    ]

    # Initialize Markdown output
    md_content = f"# Debate: {model_a_name} vs. {model_b_name}\n\n"
    md_content += f"**Topic:** {TOPIC}\n\n"
    md_content += f"**Debater A:** {model_a_name} ({MODEL_A_CONFIG.get('provider')})\n"
    md_content += f"**Debater B:** {model_b_name} ({MODEL_B_CONFIG.get('provider')})\n"
    md_content += f"**Judge:** {judge_name} ({JUDGE_CONFIG.get('provider')})\n\n"
    md_content += "---\n\n"

    transcript = f"Topic: {TOPIC}\n\n"

    # 2. The Cross-Examination Loop
    current_prompt = f"Please provide your opening argument on the topic: {TOPIC}"

    for i in range(ROUNDS):
        print(f"\n--- Round {i+1} ---")
        md_content += f"## Round {i+1}\n\n"

        # Model A's Turn
        history_A.append({"role": "user", "content": current_prompt})
        reply_A = call_llm(MODEL_A_CONFIG, history_A)
        history_A.append({"role": "assistant", "content": reply_A})
        print(f"{model_a_name}: {reply_A}\n")
        transcript += f"{model_a_name}: {reply_A}\n\n"
        md_content += f"### Model A ({model_a_name})\n{reply_A}\n\n"

        # Model B's Turn (Reacting to A)
        history_B.append(
            {
                "role": "user",
                "content": f"Model A said: '{reply_A}'. Critique this and ask a follow-up question.",
            }
        )
        reply_B = call_llm(MODEL_B_CONFIG, history_B)
        history_B.append({"role": "assistant", "content": reply_B})
        print(f"{model_b_name}: {reply_B}\n")
        transcript += f"{model_b_name}: {reply_B}\n\n"
        md_content += f"### Model B ({model_b_name})\n{reply_B}\n\n"

        md_content += "---\n\n"

        # Set next prompt for A
        current_prompt = f"Model B responded: '{reply_B}'. Defend your position and counter-question."

    # 3. Peer Evaluation Phase
    print("\n--- Evaluation Phase ---")
    md_content += "## Evaluation Phase\n\n"
    
    eval_prompt = f"""
    Review the following debate transcript. 
    {transcript}
    
    Based on this rubric: {RUBRIC}
    
    Provide a JSON output evaluating the OPPONENT. 
    Format MUST be exactly: {{"Logical Rigor": 0, "Factuality": 0, "Clarity": 0, "Feedback": "short reason"}}
    """

    score_A_grading_B = call_llm(
        MODEL_A_CONFIG, [{"role": "user", "content": eval_prompt}], require_json=True
    )
    score_B_grading_A = call_llm(
        MODEL_B_CONFIG, [{"role": "user", "content": eval_prompt}], require_json=True
    )

    print(f"{model_a_name}'s Evaluation of B:", score_A_grading_B)
    print(f"{model_b_name}'s Evaluation of A:", score_B_grading_A)
    
    md_content += f"### Model A's Evaluation of B\n```json\n{score_A_grading_B}\n```\n\n"
    md_content += f"### Model B's Evaluation of A\n```json\n{score_B_grading_A}\n```\n\n"
    md_content += "---\n\n"

    # 4. Consensus & Reconciliation Phase
    print("\n--- Consensus Phase ---")
    md_content += "## Consensus Phase\n\n"
    
    consensus_prompt = f"""
    You are the neutral Judge. 
    Model A ({model_a_name}) received these scores from B ({model_b_name}): {score_B_grading_A}
    Model B ({model_b_name}) received these scores from A ({model_a_name}): {score_A_grading_B}
    
    Review their scoring. If the scores are vastly unfair, normalize them. 
    Output a final JSON declaring the winner and the final averaged scores.
    Format: {{"Winner": "Model A/Model B/Tie", "Final_Score_A": {{...}}, "Final_Score_B": {{...}}, "Justification": "..."}}
    """

    final_judgment = call_llm(
        JUDGE_CONFIG, [{"role": "user", "content": consensus_prompt}], require_json=True
    )

    print("\nFINAL CONSENSUS:")
    try:
        parsed_judgment = json.loads(final_judgment)
        formatted_judgment = json.dumps(parsed_judgment, indent=2)
        print(formatted_judgment)
    except json.JSONDecodeError:
        formatted_judgment = final_judgment
        print(final_judgment)

    md_content += f"### FINAL CONSENSUS (Judge: {judge_name})\n```json\n{formatted_judgment}\n```\n"

    # Save to file
    with open(OUTPUT_FILE, "w") as f:
        f.write(md_content)
    print(f"\nSaved debate results to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_debate()
