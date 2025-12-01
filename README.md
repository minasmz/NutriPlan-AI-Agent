
<p align="center">
  <img src=https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/Logo%20design%20for%20NutriPlan%20AI.png width="300">
</p>

# 🥗 NutriPlan AI  
An Intelligent Multi-Agent Nutrition Assistant Powered by Google ADK & Gemini

NutriPlan AI is a fully featured **multi-agent system** designed to generate safe, personalized daily meal plans, compute macronutrients, and retrieve real-world nutrition facts via search.  
It demonstrates practical use of **LLM‑powered agents**, **sequential workflows**, **custom tools**, **memory reasoning**, **observability**, and **automated evaluation**.

I personally built this project because I often struggle with the everyday question:  
**“What should I eat today?”**  
NutriPlan AI answers that question with structure, safety, and intelligence.

---

# 📌 Table of Contents
- [Project Overview](#-project-overview)
- [Demo](#-demo)
- [Installation](#installation)
- [Running the Agent](#running-the-agent)
- [Project Architecture](#project-architecture)
- [Multi-Agent Design](#-multi-agent-design)
- [Tooling](#-tooling)
- [Memory & Context Handling](#-memory--context-handling)
- [Safety Guardrails](#-safety-guardrails)
- [Observability & Logging](#-observability--logging)
- [Evaluation](#-evaluation)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [License](#-license)

---

# 🧠 Project Overview

NutriPlan AI is an intelligent, multi-agent nutrition assistant that helps users:

✓ Generate a **personalized 1‑day meal plan**  
✓ Calculate **recommended macros** based on calorie targets  
✓ Retrieve **nutrition facts** using real Google Search  
✓ Maintain lightweight memory during the conversation  
✓ Enforce **health safety guardrails** for extreme calorie values  
✓ Provide observability through logging and evaluation tooling  

The system is built to be:

- **Modular** — each agent handles one responsibility  
- **Safe** — strict calorie guardrails prevent harmful recommendations  
- **Intuitive** — detects greetings, help requests, farewells, nutrition queries, and plan requests  
- **Extensible** — additional tools or agents can be plugged in seamlessly
  
---

# 🤖 Demo

- A suggested plan based on 1500 calories and no dietary restrictions
![1500None](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/1500cal_none.png)


- A suggested vegeterian plan based on 1800 calories
![1500None](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/1800%20calories%20vegeterian.png)


- Google Search Response for Food Macro Query 
![googlesearch](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/google%20search.png) 

---

# Installation

Clone the repository:

```bash
git clone https://github.com/minasmz/nutriplan-ai-agent.git
cd nutriplan-ai-agent
```

Create (optional) a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install Google ADK with all extras:

```bash
pip install "google-adk[all]"
```

---

# Running the Agent

Inside the project folder:

```bash
adk run nutri
```

This launches your full NutriPlan AI assistant.

---

# Project Architecture

NutriPlan AI is built using a **root router agent** that delegates every user message to the appropriate sub-agent:

```
User → Root Agent → {Greeting, Help, Preprocess, Meal Planner, Nutrition Search, Farewell}
```
![Architecture Diagram](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/overview.png)

### High-Level Flow

1. **GreetingAgent** — triggers on simple greetings  
2. **HelpAgent** — explains capabilities  
3. **FarewellAgent** — exits politely  
4. **NutritionSearchAgent** — answers nutrition fact questions  
5. **NutritionFlowGroup (SequentialAgent)**  
   - **NutritionPreprocessAgent** collects:
     - daily_calories  
     - dietary_preferences  
   - **NutritionistPlannerAgent** generates macros + meal plan  
6. **Router chooses EXACTLY ONE agent per turn**  

This ensures clarity, determinism, and removes ambiguity.

---

# 🤖 Multi-Agent Design

NutriPlan AI demonstrates three key ADK concepts:

### ✔️ LLM-Powered Agents
All agents run on **Gemini 2.5 Flash**, each with different instructions.

### ✔️ Sequential Agents
`NutritionFlowGroup` chains:

1. Preprocessing  
2. Planning

Ensuring the meal plan is only produced when all inputs are known.

### ✔️ Custom Router Logic
The root agent uses explicit tool-selection rules to determine flow.

---

# 🔧 Tooling

NutriPlan AI uses **two categories of tools**:

## 1. Custom Python Tool
A handcrafted macro calculator:

```python
def calculate_macros(daily_calories: int) -> dict:
    # 30% protein, 40% carbs, 30% fats
    ...
    return {"protein_g": ..., "carbs_g": ..., "fats_g": ...}
```

Used by `NutritionistPlannerAgent` to create the **Recommended Macros** section.

## 2. Built-in ADK Tool: google_search

```python
from google.adk.tools import google_search
```

Used by `NutritionSearchAgent` to answer questions like:

- “How many calories are in an avocado?”
- “Is brown rice higher in fiber than white rice?”

![googlesearch](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/google%20search.png)

---

# 🧵 Memory & Context Handling

Although ADK’s full session memory tools aren't used here,  
**NutritionPreprocessAgent reads the entire conversation history** to detect:

- previously stated calories  
- previously stated dietary preferences  

This prevents repetitive questions and creates a **lightweight memory layer**.

---

# 🔒 Safety Guardrails

The planner **refuses to generate a meal plan** if:

```
daily_calories < 1000 OR > 5000
```

The agent returns a medical safety warning instead.

This demonstrates safe LLM deployment practices.

![guardrails](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/gaurdrails.png)

---

# 📊 Observability & Logging

The project uses:

### ✔️ Python Logging
```python
logger.info("Calculating macros for daily_calories=%s", daily_calories)
```

### ✔️ ADK Automatic Logs
ADK automatically outputs:

- Tool calls  
- Agent routing  
- LLM responses  
- Execution metadata  

### ▶️ Live Log Monitoring

```bash
tail -F /path/to/agents_log/agent.latest.log
```

![logInfo](https://github.com/minasmz/NutriPlan-AI-Agent/blob/main/images/log%20info.png)

---

# 🧪 Evaluation

NutriPlan AI includes a custom eval set:

```
evals/nutriplan_basic_evalset.json
```

Run evaluation:

```bash
adk eval nutri evals/nutriplan_basic_evalset.json > evals/results.json
```

## 📂 Evaluation History

ADK stores results under:

```
nutri/.adk/eval_history/
```

## Metrics Included

- `tool_trajectory_avg_score`
- `response_match_score`

---

# 📁 Project Structure

```
nutriplan-ai/
│
├── nutri/
│   ├── agent.py
│   └── __init__.py
│
├── evals/
│   ├── nutriplan_basic_evalset.json
│   └── results.json
│
└── README.md
```

---

# 📎 Requirements

- Python 3.11+
- google-adk  (installed via pip)
- Gemini API key configured as:
  - `GOOGLE_API_KEY`

---

---

# 📄 License

This project is released under the MIT License.  
Feel free to fork, extend, remix, and build upon it.

This work was developed as part of the **Kaggle Agents Intensive Capstone Project**:  
🔗 https://www.kaggle.com/competitions/agents-intensive-capstone-project/

---

If you use this project or build on it, I’d love to hear about it!  
Happy learning! 🎉

