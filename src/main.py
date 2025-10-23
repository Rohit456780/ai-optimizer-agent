from utils.data_loader import load_json_data
from models.knapsack_model_json import solve_knapsack_from_json

if __name__ == "__main__":
    data = load_json_data("data/knapsack_input.json")
    if data:
        solve_knapsack_from_json(data)