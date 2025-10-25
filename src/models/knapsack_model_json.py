from pyomo.environ import *
from pyomo.opt import TerminationCondition
from heuristics.greedy_knapsack import greedy_knapsack  # ✅ import heuristic

def solve_knapsack_from_json(data):
    print("\n🚀 Running Knapsack Model (JSON mode)...")

    # ------------------ Config ------------------
    mode = data.get("solve_mode", "exact")
    params = data.get("parameters", {})
    capacity = params.get("capacity")
    budget = params.get("budget")
    target_value = params.get("target")
    penalty = 1000  # fixed penalty factor

    category_limits = data.get("category_limits", {})
    mandatory_items = data.get("mandatory_items", [])
    items_data = data.get("items", [])

    items = [i["name"] for i in items_data]
    values = {i["name"]: i["value"] for i in items_data}
    weights = {i["name"]: i["weight"] for i in items_data}
    costs = {i["name"]: i["cost"] for i in items_data}
    categories = {i["name"]: i["category"] for i in items_data}

    dep_map = {i["name"]: i["dependent"] for i in items_data if i["dependent"]}
    exc_map = {i["name"]: i["exclusive"] for i in items_data if i["exclusive"]}

    # ------------------ Heuristic Mode ------------------
    if mode == "heuristic":
        print("⚡ Running Greedy Heuristic Solver (capacity-only)...")
        if not capacity:
            print("⚠️ Capacity required for heuristic solver. Skipping.")
            return None
        selected, total_value, total_weight = greedy_knapsack(items_data, capacity)
        return {
            "mode": "heuristic",
            "selected": selected,
            "value": total_value,
            "weight": total_weight,
            "cost": sum([i["cost"] for i in items_data if i["name"] in selected])
        }

    # ------------------ Exact Mode (Pyomo) ------------------
    model = ConcreteModel()
    model.Items = Set(initialize=items)
    model.x = Var(model.Items, within=Binary)

    # Objective (max value, optional target slack)
    if target_value:
        model.slack = Var(within=NonNegativeReals)
        model.obj = Objective(
            expr=sum(values[i]*model.x[i] for i in model.Items) - penalty*model.slack,
            sense=maximize
        )
        model.target_constraint = Constraint(
            expr=sum(values[i]*model.x[i] for i in model.Items) + model.slack >= target_value
        )
    else:
        model.obj = Objective(expr=sum(values[i]*model.x[i] for i in model.Items), sense=maximize)

    # Constraints: capacity, budget, category limits
    if capacity:
        model.capacity_constraint = Constraint(expr=sum(weights[i]*model.x[i] for i in model.Items) <= capacity)
    if budget:
        model.budget_constraint = Constraint(expr=sum(costs[i]*model.x[i] for i in model.Items) <= budget)

    model.category_constraints = ConstraintList()
    for cat, (minv, maxv) in category_limits.items():
        cat_items = [i for i in items if categories[i] == cat]
        if cat_items:
            model.category_constraints.add(sum(model.x[i] for i in cat_items) >= minv)
            model.category_constraints.add(sum(model.x[i] for i in cat_items) <= maxv)

    # Dependencies
    model.dependency_constraints = ConstraintList()
    for i, deps in dep_map.items():
        for d in deps:
            if d in items:
                model.dependency_constraints.add(model.x[i] <= model.x[d])

    # Exclusivity
    model.exclusivity_constraints = ConstraintList()
    for i, excs in exc_map.items():
        for e in excs:
            if e in items and i < e:
                model.exclusivity_constraints.add(model.x[i] + model.x[e] <= 1)

    # Mandatory
    model.mandatory_constraints = ConstraintList()
    for m in mandatory_items:
        if m in items:
            model.mandatory_constraints.add(model.x[m] == 1)
            print(f"📌 Mandatory item enforced: {m}")
        else:
            print(f"⚠️ Warning: mandatory item '{m}' not found in list (ignored).")

    # ------------------ Solve ------------------
    solver = SolverFactory("glpk")
    result = solver.solve(model, tee=False)

    status = result.solver.status
    termination = result.solver.termination_condition
    print(f"\n📊 Solver status: {status}, Termination: {termination}")

    # Fallback logic if infeasible
    if termination == TerminationCondition.infeasible:
        print("❌ Exact model infeasible — switching to heuristic fallback...")
        if capacity:
            selected, total_value, total_weight = greedy_knapsack(items_data, capacity)
            return {
                "mode": "fallback_heuristic",
                "selected": selected,
                "value": total_value,
                "weight": total_weight,
                "cost": sum([i["cost"] for i in items_data if i["name"] in selected])
            }
        else:
            print("⚠️ Cannot fallback: capacity not defined.")
            return None

    # ------------------ Extract solution ------------------
    selected = [i for i in items if model.x[i]() >= 0.5]
    total_value = sum(values[i] for i in selected)
    total_weight = sum(weights[i] for i in selected)
    total_cost = sum(costs[i] for i in selected)

    print("\n✅ Optimal solution found:")
    print(f"Selected items: {selected}")
    print(f"Total Value: {total_value}")
    print(f"Total Weight: {total_weight}")
    print(f"Total Cost: {total_cost}")

    if target_value:
        achieved = sum(values[i]*model.x[i]() for i in items)
        diff = max(0, target_value - achieved)
        if diff > 0:
            print(f"⚠️ Target missed by {diff}")
        else:
            print("🎯 Target achieved or exceeded!")

    return {
        "mode": "exact",
        "selected": selected,
        "value": total_value,
        "weight": total_weight,
        "cost": total_cost
    }
