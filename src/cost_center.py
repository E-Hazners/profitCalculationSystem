class CostCenter:
    def __init__(self, name: str, fixed_cost: float, variable_cost: float):
        self.name = name
        self.fixed_cost = fixed_cost
        self.variable_cost = variable_cost

    def get_total_cost(self) -> float:
        return self.fixed_cost + self.variable_cost

    def __repr__(self) -> str:
        return f"CostCenter(name={self.name}, total_cost={self.get_total_cost()})"