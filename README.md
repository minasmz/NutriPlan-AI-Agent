# NutriPlan AI

NutriPlan AI is a multi-agent nutrition assistant built using Google ADK.  
It generates personalized meal plans, computes macronutrient targets, retrieves real‑time nutrition facts, and demonstrates core agent concepts such as tool use, sequential agents, routing, observability, and evaluation.

## 🚀 Features
- Multi-agent architecture (greeting, farewell, help, preprocess, planner, search)
- Sequential agent pipeline for calorie & preference extraction
- Custom macro-calculation tool
- Built‑in Google Search tool for nutrition fact lookup
- Safety guardrails for extreme calorie values
- Logging & observability
- Automated evaluation with ADK Eval

## 📦 Project Structure
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

## 🛠 Installation

```bash
pip install "google-adk[all]"
```

## ▶️ Running the Agent

Inside your project folder:

```bash
adk run nutri
```

## 🧪 Running Evaluation

```bash
adk eval nutri evals/nutriplan_basic_evalset.json > evals/results.json
```

Evaluation history is stored under:

```
nutri/.adk/eval_history/
```

## 📜 License
MIT
