# **LLM Debate Orchestrator**

## **Overview**

The **LLM Debate Orchestrator** is a Python-based multi-agent framework designed to pit two Large Language Models (LLMs) against each other in a structured, multi-round debate.

By having models cross-examine each other and independently evaluate the transcript, this system mitigates the "self-enhancement bias" commonly found when a single LLM evaluates its own output. A neutral "Judge" model then synthesizes the peer evaluations to declare a winner and provide a consensus score.

This is an excellent tool for:

* **Model Evaluation:** Testing the reasoning and factuality of different open-weight or proprietary models.  
* **Prompt Engineering:** Observing how models react to adversarial questioning.  
* **Complex Problem Solving:** Forcing LLMs to defend their logic and clarify their reasoning on difficult topics.

## **How It Works**

The orchestrator runs through a four-phase loop:

1. **Protocol Setup:** Both models (Model A and Model B) are initialized with system prompts establishing their roles (e.g., "Debater" vs. "Skeptic").  
2. **Cross-Examination (The Arena):** The models take turns. Model A presents an argument, Model B critiques it and asks a follow-up, and Model A defends. This repeats for a configurable number of rounds.  
3. **Peer Evaluation Phase:** The entire debate transcript is frozen and sent back to *both* models independently. They evaluate the *opponent's* performance using a strict JSON rubric.  
4. **Consensus & Aggregation:** A final Judge Model reviews the independent scorecards, normalizes any vastly unfair grading, and outputs a final JSON declaration of the winner and the averaged scores.

## **Prerequisites**

* Python 3.8+  
* requests library (pip install requests)  
* Access to an LLM API (OpenAI, Google Gemini, Anthropic, or a local endpoint like Ollama/vLLM).

## **Setup & Configuration**

1. **Clone/Download** the llm\_debate.py script.  
2. **Install dependencies:**  
   pip install requests

3. **Configure the Script:** Open llm\_debate.py and modify the \# \--- CONFIGURATION \--- block to match your environment.  
   \# Replace with your actual endpoint  
   API\_URL \= "https://api.openai.com/v1/chat/completions"   
   API\_KEY \= "YOUR\_API\_KEY"

   \# Define the models (can be the same model to test self-consistency)  
   MODEL\_A \= "gpt-4o-mini"   
   MODEL\_B \= "gpt-4o-mini"  
   JUDGE\_MODEL \= "gpt-4o"

   \# Set the debate topic and duration  
   ROUNDS \= 2  
   TOPIC \= "The feasibility of achieving AGI before 2030." 

   *Also refer curated list of topics [ TOPICS ](https://github.com/dfhsingh/LLM-Debate-Orchestrator/blob/main/curated%20debate%20topics)

   *Note on Local Models (e.g., Ollama):* If using Ollama, change the API\_URL to http://localhost:11434/v1/chat/completions, leave API\_KEY blank, and ensure the require\_json payload format matches your local server's expectations.

## **Usage**

Run the script from your terminal:

python llm\_debate.py

### **Expected Output**

You will see the debate print to the console in real-time, followed by the peer evaluations, and finally the JSON consensus:

\--- Starting Debate on: The feasibility of achieving AGI before 2030\. \---

\--- Round 1 \---  
Model A: \[Opening Argument...\]  
Model B: \[Critique and Question...\]

\--- Evaluation Phase \---  
Model A's Evaluation of B: {"Logical Rigor": 8, "Factuality": 9, "Clarity": 8, "Feedback": "..."}  
Model B's Evaluation of A: {"Logical Rigor": 6, "Factuality": 7, "Clarity": 9, "Feedback": "..."}

\--- Consensus Phase \---  
FINAL CONSENSUS:  
{  
  "Winner": "Model B",  
  "Final\_Score\_A": { ... },  
  "Final\_Score\_B": { ... },  
  "Justification": "Model B successfully identified a logical leap in Model A's timeline..."  
}

## **Customizing the Rubric**

The evaluation criteria are defined in the RUBRIC string. You can modify this to test different dimensions of the models' outputs:

RUBRIC \= """  
Evaluate the opponent based on the following criteria (0-10 scale):  
1\. Logical Rigor: Soundness of arguments.  
2\. Factuality: Accuracy of claims.  
3\. Clarity: Conciseness and directness.  
"""

* **For Coding Tasks:** Change criteria to "Code Efficiency," "Edge Case Handling," and "Readability."  
* **For Creative Tasks:** Change criteria to "Originality," "Tone," and "Narrative Flow."

## **Extending the Framework**

* **Elo Rating System:** Wrap this script in a larger loop that tests multiple model combinations and feeds the binary Win/Loss results into an Elo calculation script to build a local leaderboard.  
* **Web Dashboard:** Expose the run\_debate function via a Flask or FastAPI endpoint to trigger debates from a React frontend.
