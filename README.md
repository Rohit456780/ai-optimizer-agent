# AI Optimization Agent Project
# AI Optimizer Agent

An AI-powered Operations Research assistant that can automatically build optimization models (Phase 1)
and generate heuristic solutions (Phase 2).

## Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/rohit456780/ai-optimizer-agent.git
   cd ai-optimizer-agent
2. Create and activate virtual environment
3. Install dependencies:
pip install -r requirements.txt
Phase 1 Goals

Build LLM prompts and structure for model-building.

Auto-generate Pyomo/OR-Tools formulations.
Phase 2 Goals

Develop heuristic and metaheuristic solvers (Genetic, Tabu, etc.).

## 🧠 Day 2 Summary
- Verified OR-Tools (GLOP) and Pyomo (GLPK) solvers
- Built and solved a sample LP problem
- Tested environment setup in VS Code
- Ready to move to Day 3: dynamic model building from CSV inputgit add README.md

🧩 Day 3 — Data-Driven Knapsack Model

In Day 3, the knapsack model was upgraded to be fully data-driven and interactive. The script now reads input data from a CSV file, allows dynamic capacity (from user or file), and supports optional constraints such as item count limits, mutually exclusive pairs, and dependent pairs. All inputs are validated before being added as constraints, and the final solution (selected items and total value) is saved to a results file. This makes the model flexible, explainable, and closer to how an AI optimization agent would interpret user-defined problem logic.
