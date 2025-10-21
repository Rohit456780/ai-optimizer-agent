"""
Day 4 (Final) — Multi-Dimensional, Data-Driven Knapsack Optimizer
Includes: capacity, budget, category limits, group-based dependency/exclusivity,
and a soft target minimum value (internal slack + penalty).
"""

import os
import sys
import pandas as pd
from pyomo.environ import *
from pyomo.opt import TerminationCondition

# Ensure working directory is project root so data/ paths work in VS Code Run
os.chdir(os.path.dirname(os.path.dirname(__file__)))

# --------------------------------------------------------------------
# Helper: merge related items into unique groups
# --------------------------------------------------------------------
def merge_groups(links):
    groups = []
    for key, vals in links.items():
        group = set([key] + vals)
        found = False
        for existing in groups:
            if group & existing:
                existing |= group
                found = True
                break
        if not found:
            groups.append(group)

    # Transitive closure merging
    merged = []
    while groups:
        first, *rest = groups
        first = set(first)
        changed = True
        while changed:
            changed = False
            rest2 = []
            for g in rest:
                if first & g:
                    first |= g
                    changed = True
                else:
                    rest2.append(g)
            rest = rest2
        merged.append(first)
        groups = rest
    return [list(g) for g in merged]

# --------------------------------------------------------------------
# Main solver
# --------------------------------------------------------------------
def solve_knapsack(csv_path="data/knapsack_items.csv", output_path="data/knapsack_solution.csv"):
    df = pd.read_csv(csv_path)

    # ---------------------- Capacity ----------------------
    if "CAPACITY" in df["item"].values:
        cap_row = df[df["item"] == "CAPACITY"].iloc[0]
        capacity = float(cap_row["weight"])
        df = df[df["item"] != "CAPACITY"]
        print(f"📁 Capacity read from CSV: {capacity}")
    else:
        cap_input = input("Enter capacity (press Enter to skip): ").strip()
        if cap_input == "":
            capacity = None
            print("⚖️ No capacity constraint applied.")
        else:
            capacity = float(cap_input)
            print(f"⚖️ Capacity set to {capacity}")

    # ---------------------- Budget -----------------------
    if "BUDGET" in df["item"].values:
        budget_row = df[df["item"] == "BUDGET"].iloc[0]
        budget = float(budget_row["cost"])
        df = df[df["item"] != "BUDGET"]
        print(f"💰 Budget read from CSV: {budget}")
    else:
        budget_input = input("Enter budget limit (press Enter to skip): ").strip()
        if budget_input == "":
            budget = None
            print("💰 No budget constraint applied.")
        else:
            budget = float(budget_input)
            print(f"💰 Budget set to {budget}")

        use_target = False
    target_value = None
    internal_penalty = 1000.0  # constant penalty factor

    # ---------------------- Target -----------------------
    if "TARGET" in df["item"].values:
        target_row = df[df["item"] == "TARGET"].iloc[0]
        try:
            # Try reading from category column
            target_value = float(target_row["cost"])
            use_target = True
            print(f"🎯 Target minimum total value read from CSV: {target_value}")
        except ValueError:
            print("⚠️ Target row found but invalid format — skipping target constraint.")
        df = df[df["item"] != "TARGET"]
    else:
        apply_target = input("Do you want to set a target minimum total value? (press Enter to skip): ").strip().lower()
        if apply_target == "yes":
            try:
                target_value = float(input("Enter target minimum total value: ").strip())
                use_target = True
                print(f"🎯 Target minimum total value set: {target_value}")
            except ValueError:
                print("⚠️ Invalid target input. Skipping target constraint.")
                use_target = False

    # ------------------- Category limits -------------------
    category_limits = {}
    if "CATEGORY_LIMIT" in df["item"].values:
        limit_row = df[df["item"] == "CATEGORY_LIMIT"].iloc[0]
        raw_limits = str(limit_row.get("category", ""))
        parts = [p.strip() for p in raw_limits.split(";") if p.strip()]
        for p in parts:
            cat, bounds = p.split(":")
            minv, maxv = bounds.split("-")
            category_limits[cat.strip()] = (int(minv), int(maxv))
        df = df[df["item"] != "CATEGORY_LIMIT"]
        print(f"📊 Category limits read from CSV: {category_limits}")
    else:
        cat_choice = input("Press yes if you want to enter category limits, or Enter to skip: ").strip().lower()
        if cat_choice == "yes":
            unique_cats = df["category"].unique()
            for cat in unique_cats:
                minv = input(f"Enter min items for category {cat} (press Enter for 0): ").strip()
                maxv = input(f"Enter max items for category {cat} (press Enter for no limit): ").strip()
                minv = int(minv) if minv else 0
                maxv = int(maxv) if maxv else len(df[df['category'] == cat])
                category_limits[cat] = (minv, maxv)
        else:
            print("📊 Skipping category constraints.")

    # ------------------- Prepare item data -------------------
    items = list(df["item"])
    values = dict(zip(items, df["value"]))
    weights = dict(zip(items, df["weight"]))
    costs = dict(zip(items, df["cost"]))

    print(f"\n📦 Available items: {items}")

    # ------------- Parse dependency/exclusivity -------------
    dep_map, exc_map = {}, {}
    if "dependent" in df.columns:
        for _, row in df.iterrows():
            if pd.notna(row["dependent"]):
                deps = [d.strip() for d in str(row["dependent"]).split(",") if d.strip()]
                valid = [d for d in deps if d in items]
                if valid:
                    dep_map[row["item"]] = valid

    if "exclusive" in df.columns:
        for _, row in df.iterrows():
            if pd.notna(row["exclusive"]):
                excls = [e.strip() for e in str(row["exclusive"]).split(",") if e.strip()]
                valid = [e for e in excls if e in items]
                if valid:
                    exc_map[row["item"]] = valid

    dependent_groups = merge_groups(dep_map)
    exclusive_groups = merge_groups(exc_map)

    # Manual input fallback for groups
    if not dependent_groups and not exclusive_groups:
        dep_choice = input("Press yes if you want to enter dependency groups, or Enter to skip: ").strip().lower()
        if dep_choice == "yes":
            num_dep = int(input("How many dependency groups? "))
            for i in range(num_dep):
                g = input(f"Enter items for dependency group {i+1} (comma-separated): ").split(",")
                dependent_groups.append([x.strip() for x in g if x.strip()])

        exc_choice = input("Press yes if you want to enter exclusivity groups, or Enter to skip: ").strip().lower()
        if exc_choice == "yes":
            num_exc = int(input("How many exclusivity groups? "))
            for i in range(num_exc):
                g = input(f"Enter items for exclusivity group {i+1} (comma-separated): ").split(",")
                exclusive_groups.append([x.strip() for x in g if x.strip()])

    print(f"\n✅ Found {len(dependent_groups)} dependency groups and {len(exclusive_groups)} exclusivity groups.\n")

    # ------------------- Ask for target minimum value? -------------------
    # ------------------- Read target minimum value -------------------




    # ------------------- Build model -------------------
    model = ConcreteModel()
    model.Items = Set(initialize=items)
    model.x = Var(model.Items, within=Binary)

    # Objective (initial)
    model.obj = Objective(expr=sum(values[i] * model.x[i] for i in model.Items), sense=maximize)

    # Hard constraints: capacity & budget & categories
    if capacity is not None:
        model.capacity_constraint = Constraint(expr=sum(weights[i] * model.x[i] for i in model.Items) <= capacity)
    if budget is not None:
        model.budget_constraint = Constraint(expr=sum(costs[i] * model.x[i] for i in model.Items) <= budget)
    for cat, (minv, maxv) in category_limits.items():
        cat_items = [i for i in items if df.loc[df["item"] == i, "category"].values[0] == cat]
        if cat_items:
            setattr(model, f"cat_min_{cat}", Constraint(expr=sum(model.x[i] for i in cat_items) >= minv))
            setattr(model, f"cat_max_{cat}", Constraint(expr=sum(model.x[i] for i in cat_items) <= maxv))

    # Group constraints: dependent = equality, exclusive = at most one
    for g_id, group in enumerate(dependent_groups):
        first = group[0]
        for other in group[1:]:
            setattr(model, f"dep_{g_id}_{other}", Constraint(expr=model.x[first] - model.x[other] == 0))
    for g_id, group in enumerate(exclusive_groups):
        setattr(model, f"exc_{g_id}", Constraint(expr=sum(model.x[i] for i in group) <= 1))

    # Soft target: add slack and incorporate into objective if requested
    if use_target:
        model.slack = Var(within=NonNegativeReals)
        model.target_constraint = Constraint(expr=sum(values[i] * model.x[i] for i in model.Items) + model.slack >= target_value)
        # Replace objective with penalized version
        model.obj.set_value(expr=sum(values[i] * model.x[i] for i in model.Items) - internal_penalty * model.slack)


    # ------------------- Solve model & status handling -------------------
    solver = SolverFactory("glpk")
    result = solver.solve(model, tee=False)

    status = result.solver.status
    termination = result.solver.termination_condition

    print(f"\n📊 Solver status: {status}, Termination: {termination}")

    if termination == TerminationCondition.optimal:
        print("✅ Optimal solution found.\n")
    elif termination in (TerminationCondition.feasible, TerminationCondition.locallyOptimal):
        print("⚠️ Feasible (non-optimal) solution found.\n")
    elif termination in (TerminationCondition.infeasible, TerminationCondition.unbounded):
        print("❌ Model is infeasible or unbounded. No valid solution found.\n")
        print("🧠 Try adjusting capacity, budget, or category constraints.")
        return
    else:
        print("⚠️ Solver ended with unknown status. Please check configuration.")
        return

    # ------------------- Extract solution -------------------
    df["selected"] = [int(model.x[i]()) for i in items]
    total_value = sum(df["value"] * df["selected"])
    total_weight = sum(df["weight"] * df["selected"])
    total_cost = sum(df["cost"] * df["selected"])
    slack_value = getattr(model, "slack", None)
    slack_val = float(model.slack()) if (slack_value is not None) else 0.0

    df.to_csv(output_path, index=False)

    # ------------------- Print results -------------------
    print(f"✅ Total value achieved: {total_value:.2f}")
    if capacity is not None:
        print(f"⚖️ Total weight used: {total_weight:.2f}")
    if budget is not None:
        print(f"💰 Total cost used: {total_cost:.2f}")
    if use_target:
        if slack_val > 0:
            print(f"⚠️ Target missed by {slack_val:.2f} units due to constraints.")
        else:
            print("🎯 Target met.")

    print("\n📋 Selected items:")
    print(df[df["selected"] == 1])

    # ------------------- Summary -------------------
    print("\n🧠 Constraint Summary:")
    if capacity is not None: print(f"Capacity: {capacity}")
    if budget is not None: print(f"Budget: {budget}")
    if category_limits: print(f"Category limits: {category_limits}")
    if dependent_groups: print(f"Dependency groups: {dependent_groups}")
    if exclusive_groups: print(f"Exclusivity groups: {exclusive_groups}")
    if use_target: print(f"Target value: {target_value}")

# --------------------------------------------------------------------
if __name__ == "__main__":
    solve_knapsack()


