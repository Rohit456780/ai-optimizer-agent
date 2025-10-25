import time

def greedy_knapsack(items, capacity, budget=None, mandatory_items=None):
    """
    Multi-pass, self-repairing greedy heuristic with local improvement.
    - Runs three greedy strategies (value/weight, value/cost, hybrid).
    - Repairs infeasible mandatory sets.
    - Applies small local search to refine results.
    - Returns the best solution found among passes.
    """

    start_time = time.time()
    mandatory_items = set(mandatory_items or [])
    item_lookup = {i["name"]: i for i in items}

    def single_pass(score_func):
        """Run one greedy pass using a given score function."""
        selected = set()
        total_value = total_weight = total_cost = 0

        # Add mandatory items first
        for m in mandatory_items:
            if m in item_lookup:
                item = item_lookup[m]
                total_weight += item["weight"]
                total_cost += item["cost"]
                total_value += item["value"]
                selected.add(m)

        # Skip if mandatory already infeasible
        if capacity and total_weight > capacity or (budget and total_cost > budget):
            return selected, total_value, total_weight, total_cost

        # Compute scores
        sorted_items = sorted(
            [i for i in items if i["name"] not in selected],
            key=score_func,
            reverse=True
        )

        for item in sorted_items:
            name = item["name"]
            if any(e in selected for e in item.get("exclusive", [])):
                continue
            if capacity and total_weight + item["weight"] > capacity:
                continue
            if budget and (total_cost + item["cost"] > budget):
                continue

            selected.add(name)
            total_weight += item["weight"]
            total_cost += item["cost"]
            total_value += item["value"]

        return selected, total_value, total_weight, total_cost

    # ------------------ Step 1: Run multiple greedy passes ------------------
    print("\n⚙️ Running Multi-Pass Greedy Heuristic...")

    def vw_ratio(x): return x["value"] / max(1e-9, x["weight"])
    def vc_ratio(x): return x["value"] / max(1e-9, x["cost"])
    def hybrid_ratio(x): return x["value"] / (0.5 * x["weight"] + 0.5 * x["cost"])

    passes = {
        "value/weight": single_pass(vw_ratio),
        "value/cost": single_pass(vc_ratio),
        "hybrid": single_pass(hybrid_ratio),
    }

    # ------------------ Step 2: Pick the best result ------------------
    best_name, (best_sel, best_val, best_wt, best_cost) = max(
        passes.items(), key=lambda kv: kv[1][1]
    )
    print(f"🏁 Best pass: {best_name} (Value = {best_val:.2f})")

    # ------------------ Step 3: Local improvement ------------------
    non_selected = [i["name"] for i in items if i["name"] not in best_sel]
    improved = True
    while improved:
        improved = False
        for s in list(best_sel):
            for n in list(non_selected):
                s_item = item_lookup[s]
                n_item = item_lookup[n]

                new_weight = best_wt - s_item["weight"] + n_item["weight"]
                new_cost = best_cost - s_item["cost"] + n_item["cost"]
                new_value = best_val - s_item["value"] + n_item["value"]

                # Check feasibility and improvement
                if (capacity and new_weight > capacity) or (budget and new_cost > budget):
                    continue
                if new_value > best_val:
                    best_sel.remove(s)
                    best_sel.add(n)
                    best_val, best_wt, best_cost = new_value, new_weight, new_cost
                    non_selected.remove(n)
                    non_selected.append(s)
                    improved = True
                    print(f"🔄 Local swap improved solution: replaced {s} with {n}")
                    break
            if improved:
                break

    runtime = round(time.time() - start_time, 3)
    print(f"⏱️ Heuristic runtime: {runtime} sec")
    print(f"✅ Final Value: {best_val:.2f}, Weight: {best_wt}/{capacity}, Cost: {best_cost}/{budget}")

    info = {"mandatory_dropped": False, "best_pass": best_name, "runtime": runtime}

    return list(best_sel), best_val, best_wt, best_cost, info
