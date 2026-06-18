import json
import requests
from typing import List, Dict

# --- CONFIGURATION ---
# Replace with your actual LLM API endpoints (e.g., GoogleAntigravity, Ollama, or OpenAI)
API_URL = "https://api.openai.com/v1/chat/completions" # Example standard endpoint
API_KEY = "YOUR_API_KEY"

MODEL_A = "model-a-identifier" 
MODEL_B = "model-b-identifier"
JUDGE_MODEL = "model-judge-identifier" # Can be the same as A or B, or a larger model

ROUNDS = 2
TOPIC = "The feasibility of achieving AGI before 2030."

RUBRIC = """
Evaluate the opponent based on the following criteria (0-10 scale):
1. Logical Rigor: Soundness of arguments.
2. Factuality: Accuracy of claims.
3. Clarity: Conciseness and directness.
"""

# --- HELPER FUNCTIONS ---
def call_llm(model: str, messages: List[Dict], require_json: bool = False) -> str:
    """Generic wrapper for LLM API calls."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    if require_json:
         # Force JSON output format if supported by your API
         payload["response_format"] = { "type": "json_object" }

    try:
        # Note: Adapt this payload structure if GoogleAntigravity uses a different schema
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API Error with {model}: {e}")
        return "{}" if require_json else "Error generating response."

# --- MAIN SYSTEM ---
def run_debate():
    print(f"--- Starting Debate on: {TOPIC} ---")
    
    # 1. Initialize Contexts
    history_A = [
        {"role": "system", "content": "You are Debater A. Present arguments clearly. Question Debater B's logic. Keep responses under 150 words."}
    ]
    history_B = [
        {"role": "system", "content": "You are Debater B. Act as a skeptic. Point out flaws in Debater A's arguments and counter them. Keep responses under 150 words."}
    ]
    
    transcript = f"Topic: {TOPIC}\n\n"
    
    # 2. The Cross-Examination Loop
    current_prompt = f"Please provide your opening argument on the topic: {TOPIC}"
    
    for i in range(ROUNDS):
        print(f"\n--- Round {i+1} ---")
        
        # Model A's Turn
        history_A.append({"role": "user", "content": current_prompt})
        reply_A = call_llm(MODEL_A, history_A)
        history_A.append({"role": "assistant", "content": reply_A})
        print(f"Model A: {reply_A}\n")
        transcript += f"Model A: {reply_A}\n\n"
        
        # Model B's Turn (Reacting to A)
        history_B.append({"role": "user", "content": f"Model A said: '{reply_A}'. Critique this and ask a follow-up question."})
        reply_B = call_llm(MODEL_B, history_B)
        history_B.append({"role": "assistant", "content": reply_B})
        print(f"Model B: {reply_B}\n")
        transcript += f"Model B: {reply_B}\n\n"
        
        # Set next prompt for A
        current_prompt = f"Model B responded: '{reply_B}'. Defend your position and counter-question."

    # 3. Peer Evaluation Phase
    print("\n--- Evaluation Phase ---")
    eval_prompt = f"""
    Review the following debate transcript. 
    {transcript}
    
    Based on this rubric: {RUBRIC}
    
    Provide a JSON output evaluating the OPPONENT. 
    Format MUST be exactly: {{"Logical Rigor": 0, "Factuality": 0, "Clarity": 0, "Feedback": "short reason"}}
    """
    
    score_A_grading_B = call_llm(MODEL_A, [{"role": "user", "content": eval_prompt}], require_json=True)
    score_B_grading_A = call_llm(MODEL_B, [{"role": "user", "content": eval_prompt}], require_json=True)
    
    print("Model A's Evaluation of B:", score_A_grading_B)
    print("Model B's Evaluation of A:", score_B_grading_A)

    # 4. Consensus & Reconciliation Phase
    print("\n--- Consensus Phase ---")
    consensus_prompt = f"""
    You are the neutral Judge. 
    Model A received these scores from B: {score_B_grading_A}
    Model B received these scores from A: {score_A_grading_B}
    
    Review their scoring. If the scores are vastly unfair, normalize them. 
    Output a final JSON declaring the winner and the final averaged scores.
    Format: {{"Winner": "Model A/Model B/Tie", "Final_Score_A": {{...}}, "Final_Score_B": {{...}}, "Justification": "..."}}
    """
    
    final_judgment = call_llm(JUDGE_MODEL, [{"role": "user", "content": consensus_prompt}], require_json=True)
    
    print("\nFINAL CONSENSUS:")
    try:
        print(json.dumps(json.loads(final_judgment), indent=2))
    except json.JSONDecodeError:
        print(final_judgment)

if __name__ == "__main__":
    run_debate()
