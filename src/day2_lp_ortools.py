"""
Day 2 Task - Test OR-Tools Solver
Simple Linear Programming Example
"""

from ortools.linear_solver import pywraplp

def main():
    # Create solver
    solver = pywraplp.Solver.CreateSolver("GLOP")

    # Variables
    x = solver.NumVar(0, 10, "x")
    y = solver.NumVar(0, 10, "y")

    # Constraints
    solver.Add(x + 2*y <= 14)
    solver.Add(3*x - y >= 0)
    solver.Add(x - y <= 2)

    # Objective
    solver.Maximize(3*x + 4*y)

    # Solve
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print(f"x = {x.solution_value():.2f}")
        print(f"y = {y.solution_value():.2f}")
        print(f"Objective = {solver.Objective().Value():.2f}")
    else:
        print("No optimal solution found.")

if __name__ == "__main__":
    main()
