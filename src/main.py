#!/usr/bin/env python3
from utils.data_loader import load_json_data
from models.knapsack_model_json import solve_knapsack_from_json

if __name__ == "__main__":
    print("\n🧠 AI Optimizer Agent — Knapsack Model Runner")

    # Load input data
    data = load_json_data("data/knapsack_input.json")
    if not data:
        print("❌ Failed to load input data. Please check JSON file path.")
        exit(1)

    # Display solve mode
    solve_mode = data.get("solve_mode", "exact").upper()
    print(f"🚀 Solve mode selected: {solve_mode}")

    # Solve model
    result = solve_knapsack_from_json(data)

    # Display output summary
    if result:
        print("\n📊 --- Solution Summary ---")
        print(f"🧩 Mode Used: {result['mode']}")
        print(f"📦 Selected Items: {result['selected']}")
        print(f"💰 Total Value: {result['value']}")
        print(f"⚖️ Total Weight: {result['weight']}")
        print(f"🏷️ Total Cost: {result['cost']}")
    else:
        print("\n⚠️ No valid solution returned.")
