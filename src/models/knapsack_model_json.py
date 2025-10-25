from pyomo.environ import *
from pyomo.opt import TerminationCondition
from heuristics.greedy_knapsack import greedy_knapsack

def solve_knapsack_from_json(data):
    mode = data.get("solve_mode", "exact").lower()
    params = data.get("parameters", {})
    capacity = params.get("capacity")
    budget = params.get("budget")
    target_value = params.get("target_value")
    items_data = data.get("items", [])
    mandatory_items = data.get("mandatory_items", [])

    def run_exact():
        """Run Pyomo-based exact solver"""
        model = ConcreteModel()
        items = [i["name"] for i in items_data]
        model.Items = Set(initialize=items)
        model.x = Var(model.Items, within=Binary)
        values = {i["name"]: i["value"] for i in items_data}
        weights = {i["name"]: i["weight"] for i in items_data}
        costs = {i["name"]: i["cost"] for i in items_data}

        model.obj = Objective(expr=sum(values[i] * model.x[i] for i in items), sense=maximize)
        if capacity:
            model.capacity = Constraint(expr=sum(weights[i] * model.x[i] for i in items) <= capacity)
        if budget:
            model.budget = Constraint(expr=sum(costs[i] * model.x[i] for i in items) <= budget)

        # Mandatory constraints
        for m in mandatory_items:
            if m in items:
                setattr(model, f"mandatory_{m}", Constraint(expr=model.x[m] == 1))

        solver = SolverFactory("glpk")
        try:
            result = solver.solve(model, tee=False, timelimit=10)  # 10s time cap
        except Exception as e:
            print(f"❌ Solver error: {e}")
            return None, "error"

        termination = result.solver.termination_condition
        if termination in (TerminationCondition.infeasible, TerminationCondition.unbounded):
            print("❌ Exact model infeasible or unbounded.")
            return None, "infeasible"
        elif termination == TerminationCondition.maxTimeLimit:
            print("⏱️ Exact solver timeout.")
            return None, "timeout"

        # Successful solve
        selected = [i for i in items if model.x[i]() >= 0.5]
        total_value = sum(values[i] for i in selected)
        total_weight = sum(weights[i] for i in selected)
        total_cost = sum(costs[i] for i in selected)

        return {
            "mode": "exact",
            "selected": selected,
            "value": total_value,
            "weight": total_weight,
            "cost": total_cost,
            "info": {"mandatory_dropped": False}
        }, "success"

    def run_heuristic():
        """Run the greedy heuristic solver"""
        print("⚡ Running Self-Repairing Greedy Heuristic Solver...")
        if not capacity:
            print("⚠️ Capacity required for heuristic solver. Skipping.")
            return None, "error"

        selected, total_value, total_weight, total_cost, info = greedy_knapsack(
            items_data, capacity, budget, mandatory_items
        )

        result = {
            "mode": "heuristic",
            "selected": selected,
            "value": total_value,
            "weight": total_weight,
            "cost": total_cost,
            "info": info,
        }

        if info.get("mandatory_dropped"):
            print("\n⚠️ Mandatory adjustments applied in heuristic solution.")
        return result, "success"

    # --------------------- Mode Handling ---------------------
    print(f"\n🧩 Solve Mode: {mode.upper()}")

    if mode == "exact":
        result, status = run_exact()
        return result

    elif mode == "heuristic":
        result, status = run_heuristic()
        return result

    elif mode == "auto":
        print("🤖 Auto Mode: Trying exact solver first...")
        result, status = run_exact()
        if status != "success":
            print("🔁 Switching to heuristic fallback...")
            result, _ = run_heuristic()
            if result:
                result["mode"] = "auto (heuristic fallback)"
        else:
            print("✅ Exact solver succeeded in auto mode.")
            result["mode"] = "auto (exact)"
        return result

    else:
        print(f"⚠️ Unknown solve_mode '{mode}'. Defaulting to exact solver.")
        result, _ = run_exact()
        return result
