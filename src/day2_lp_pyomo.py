"""
Day 2 Task - Test Pyomo Solver
Simple Linear Programming Example
"""

from pyomo.environ import *

def main():
    model = ConcreteModel()

    # Decision variables
    model.x = Var(bounds=(0, 10))
    model.y = Var(bounds=(0, 10))

    # Objective
    model.obj = Objective(expr=3*model.x + 4*model.y, sense=maximize)

    # Constraints
    model.con1 = Constraint(expr=model.x + 2*model.y <= 14)
    model.con2 = Constraint(expr=3*model.x - model.y >= 0)
    model.con3 = Constraint(expr=model.x - model.y <= 2)

    # Solver
    solver = SolverFactory("glpk")  # or "cbc" if glpk isn't installed
    results = solver.solve(model, tee=False)

    print(f"x = {model.x():.2f}")
    print(f"y = {model.y():.2f}")
    print(f"Objective = {model.obj():.2f}")

if __name__ == "__main__":
    main()
