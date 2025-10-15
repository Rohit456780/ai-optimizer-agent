"""
Day 3 (Final Polished): Interactive Knapsack with Logical and Target Constraints
Simplified for clean user experience — penalty handled internally, not displayed.
"""

import pandas as pd
from pyomo.environ import *

def solve_knapsack(csv_path="data/knapsack_items.csv", capacity=None, output_path="data/knapsack_solution.csv"):
    # --- Step 1: Load item data ---
    df = pd.read_csv(csv_path)
    items = list(df["item"])
    values = dict(zip(items, df["value"]))
    weights = dict(zip(items, df["weight"]))

    print(f"Available items: {items}\n")

    # --- Step 2: Load or ask capacity ---
    try:
        cap_df = pd.read_csv("data/knapsack_capacity.csv")
        file_capacity = float(cap_df.loc[0, "capacity"])
        print(f"📁 Capacity read from file: {file_capacity}")
    except FileNotFoundError:
        file_capacity = None

    if capacity is None:
        if file_capacity:
            capacity = file_capacity
        else:
            capacity = float(input("Enter knapsack capacity: "))

    print(f"🧮 Using capacity = {capacity}\n")

    # --- Step 3: Optional item limit ---
    apply_limit = input("Do you want to set a limit on number of items? (yes/no): ").strip().lower()
    item_limit = None
    if apply_limit == "yes":
        try:
            item_limit = int(input("Enter the maximum number of items allowed: "))
            print(f"📏 Applying item limit: {item_limit}\n")
        except ValueError:
            print("⚠️ Invalid input. Ignoring item limit constraint.\n")

    # --- Step 4: Mutually exclusive pairs ---
    exclusive_pairs = []
    while True:
        add_pair = input("Do you want to add mutually exclusive items? (yes/no): ").strip().lower()
        if add_pair != "yes":
            break
        pair = input("Enter two item names separated by a comma (e.g., A,B): ").strip().split(",")
        if len(pair) != 2:
            print("⚠️ Invalid input format. Use: A,B")
            continue
        i, j = pair[0].strip(), pair[1].strip()
        if i in items and j in items:
            exclusive_pairs.append((i, j))
            print(f"✅ Added mutually exclusive pair: ({i}, {j})")
        else:
            print(f"❌ Invalid pair ({i}, {j}) — one or both items not found in {items}")

    print()

    # --- Step 5: Dependent pairs ---
    dependent_pairs = []
    while True:
        add_pair = input("Do you want to add dependent item pairs (must go together)? (yes/no): ").strip().lower()
        if add_pair != "yes":
            break
        pair = input("Enter two item names separated by a comma (e.g., A,B): ").strip().split(",")
        if len(pair) != 2:
            print("⚠️ Invalid input format. Use: A,B")
            continue
        i, j = pair[0].strip(), pair[1].strip()
        if i in items and j in items:
            dependent_pairs.append((i, j))
            print(f"✅ Added dependent pair: ({i}, {j})")
        else:
            print(f"❌ Invalid pair ({i}, {j}) — one or both items not found in {items}")

    print()

    # --- Step 6: Build the model ---
    model = ConcreteModel()
    model.Items = Set(initialize=items)
    model.x = Var(model.Items, within=Binary)

    # Base objective
    model.value = Objective(expr=sum(values[i] * model.x[i] for i in model.Items), sense=maximize)

    # Weight constraint
    model.weight_constraint = Constraint(expr=sum(weights[i] * model.x[i] for i in model.Items) <= capacity)

    # Optional item limit constraint
    if item_limit is not None:
        model.limit_constraint = Constraint(expr=sum(model.x[i] for i in model.Items) <= item_limit)

    # Mutually exclusive constraints
    for k, (i, j) in enumerate(exclusive_pairs):
        setattr(model, f"exclusive_{k}", Constraint(expr=model.x[i] + model.x[j] <= 1))

    # Dependent pair constraints
    for k, (i, j) in enumerate(dependent_pairs):
        setattr(model, f"dependent_{k}", Constraint(expr=model.x[i] - model.x[j] == 0))

    # --- Step 7: Target minimum value (soft constraint, internal penalty) ---
    apply_target = input("Do you want to set a target minimum total value? (yes/no): ").strip().lower()
    if apply_target == "yes":
        try:
            target_value = float(input("Enter target minimum total value: "))
            penalty = 1000  # internal high penalty

            model.slack = Var(within=NonNegativeReals)
            model.target_constraint = Constraint(
                expr=sum(values[i] * model.x[i] for i in model.Items) + model.slack >= target_value
            )

            model.value.set_value(
                expr=sum(values[i] * model.x[i] for i in model.Items) - penalty * model.slack
            )

            print(f"🎯 Target minimum total value set: {target_value}\n")

        except ValueError:
            print("⚠️ Invalid target input. Skipping target constraint.\n")

    # --- Step 8: Solve ---
    solver = SolverFactory("glpk")
    solver.solve(model, tee=False)

    # --- Step 9: Collect results ---
    df["selected"] = [int(model.x[i]()) for i in items]
    total_value = sum(df["value"] * df["selected"])
    slack_value = model.slack.value if hasattr(model, "slack") else 0

    df.to_csv(output_path, index=False)
    print(f"✅ Optimal total value achieved: {total_value:.2f}")
    if slack_value > 0:
        print(f"⚠️ Target missed by {slack_value:.2f} units due to constraints.")
    print("📦 Selected items:")
    print(df[df["selected"] == 1])

    # --- Step 10: Summary ---
    print("\n🧠 Constraint Summary:")
    print(f"Capacity: {capacity}")
    if item_limit:
        print(f"Item limit: {item_limit}")
    if exclusive_pairs:
        print(f"Mutually exclusive pairs: {exclusive_pairs}")
    if dependent_pairs:
        print(f"Dependent pairs: {dependent_pairs}")
    if apply_target == "yes":
        print(f"Target value: {target_value}")

if __name__ == "__main__":
    solve_knapsack()




