def greedy_knapsack(items, capacity):
    """
    Simple greedy knapsack heuristic: sort by value/weight ratio and fill until capacity.
    """
    sorted_items = sorted(items, key=lambda x: x["value"] / x["weight"], reverse=True)
    selected, total_value, total_weight = [], 0, 0

    for item in sorted_items:
        if total_weight + item["weight"] <= capacity:
            selected.append(item["name"])
            total_weight += item["weight"]
            total_value += item["value"]

    print("\n⚡ Heuristic Mode Result:")
    print(f"Selected Items: {selected}")
    print(f"Total Value: {total_value}")
    print(f"Total Weight: {total_weight}")
    return selected, total_value, total_weight
