#!/usr/bin/env python3
import os
import json
from utils.data_loader import load_json_data
from models.knapsack_model_json import solve_knapsack_from_json
from utils.logger import log_run, print_summary


def save_comparison(result_exact, result_heuristic):
    """Save comparison between exact and heuristic solvers."""
    os.makedirs("results", exist_ok=True)
    comparison_path = "results/last_comparison.json"

    gap = 0
    if result_exact and result_heuristic and result_exact["value"] > 0:
        gap = ((result_exact["value"] - result_heuristic["value"]) / result_exact["value"]) * 100

    comparison_data = {
        "exact_value": result_exact["value"],
        "heuristic_value": result_heuristic["value"],
        "value_gap_percent": round(gap, 2),
        "exact_items": result_exact["selected"],
        "heuristic_items": result_heuristic["selected"],
        "exact_weight": result_exact["weight"],
        "heuristic_weight": result_heuristic["weight"],
        "exact_cost": result_exact["cost"],
        "heuristic_cost": result_heuristic["cost"],
    }

    with open(comparison_path, "w") as f:
        json.dump(comparison_data, f, indent=4)

    print(f"\n📁 Comparison saved to {comparison_path}")
    return comparison_data



if __name__ == "__main__":
    print("\n🧠 AI Optimizer Agent — Knapsack Model Runner")

    data = load_json_data("data/knapsack_input.json")
    if not data:
        print("❌ Failed to load input data. Please check JSON file path.")
        exit(1)

    solve_mode = data.get("solve_mode", "exact").lower()
    print(f"🚀 Solve mode selected: {solve_mode.upper()}")

    # ----------------- COMPARISON MODE -----------------
    if solve_mode == "compare":
        print("\n📊 Running solver comparison: Exact vs Heuristic\n")

        data_exact = data.copy()
        data_exact["solve_mode"] = "exact"
        result_exact = solve_knapsack_from_json(data_exact)

        data_heuristic = data.copy()
        data_heuristic["solve_mode"] = "heuristic"
        result_heuristic = solve_knapsack_from_json(data_heuristic)

        if result_exact and result_heuristic:
            gap = 0
            if result_exact["value"] > 0:
                gap = ((result_exact["value"] - result_heuristic["value"]) / result_exact["value"]) * 100

            print("\n📈 --- Comparison Summary ---")
            print(f"✅ Exact Value: {result_exact['value']}")
            print(f"⚡ Heuristic Value: {result_heuristic['value']}")
            print(f"📉 Gap: {gap:.2f}%")
            print(f"Exact Items: {result_exact['selected']}")
            print(f"Heuristic Items: {result_heuristic['selected']}")

            save_comparison(result_exact, result_heuristic)

            # Log comparison
            entry = {
                "mode": "compare",
                "exact_value": result_exact["value"],
                "heuristic_value": result_heuristic["value"],
                "gap_percent": round(gap, 2),
                "status": "SUCCESS",
            }
            log_run(entry)
            print_summary(entry)

        else:
            print("\n⚠️ Comparison failed. One of the solvers returned no result.")

    # ----------------- NORMAL MODES -----------------
    else:
        result = solve_knapsack_from_json(data)
        if result:
            info = result.get("info", {})
            print("\n📊 --- Final Solution Summary ---")
            print(f"🧩 Mode Used: {result['mode']}")
            print(f"📦 Selected Items: {result['selected']}")
            print(f"💰 Total Value: {result['value']}")
            print(f"⚖️ Total Weight: {result['weight']}")
            print(f"🏷️ Total Cost: {result['cost']}")

            if info.get("mandatory_dropped"):
                print("\n⚠️ Mandatory Adjustments:")
                if info.get("dropped_items"):
                    print(f"   → Dropped during repair: {info['dropped_items']}")
                if info.get("original_mandatory"):
                    print(f"   → Mandatory items dropped entirely (infeasible): {info['original_mandatory']}")
            else:
                print("\n✅ All mandatory items satisfied.")

            if "auto" in result["mode"]:
                print("\n🤖 Auto Mode Summary:")
                if "heuristic" in result["mode"]:
                    print("   → Used heuristic fallback.")
                else:
                    print("   → Exact solver succeeded.")

            # Log single-mode run
            entry = {
                "mode": result["mode"],
                "value": result["value"],
                "weight": result["weight"],
                "cost": result["cost"],
                "runtime": result.get("info", {}).get("runtime", None),
                "status": "SUCCESS",
            }
            log_run(entry)
            print_summary(entry)

        else:
            print("\n⚠️ No valid solution returned.")
